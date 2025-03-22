"""
Dispatcher for the CI system

The dispatcher acts as the central coordinator. It listens for:
  - "status" requests (to verify its availability)
  - "register" requests (from test runners registering themselves)
  - "dispatch" requests (from the repository observer with a commit ID)
  - "results" requests (from test runners reporting test outcomes)

It also monitors the health of registered test runners and reassigns commits if needed.
"""

import argparse
import os
import re
import threading
import time
import socketserver
from collections import deque  

from ci_system import config, helpers

# Global structures for tracking runners and commit assignments
# List of dicts: {"host": str, "port": int, "last_seen": float}
registered_runners = []
dispatched_commits = {}       # Mapping commit_id -> runner info
pending_commits = deque()    # Queue of commit IDs to be dispatched

# Locks for shared state
runners_lock = threading.Lock()
commits_lock = threading.Lock()


class DispatcherHandler(socketserver.BaseRequestHandler):
    BUF_SIZE = 1024
    # Matches command and optional arguments
    # 
    COMMAND_REGEX = re.compile(r"(\w+)(:.+)*")
    # matches command:host:port for example register:localhost:8888
    
    def handle(self):
        try:
            raw_data = self.request.recv(self.BUF_SIZE).strip().decode()
            print(f"[Dispatcher] Received: {raw_data}")
        except Exception as e:
            self.request.sendall(f"Error receiving data: {e}".encode())
            return

        match = self.COMMAND_REGEX.match(raw_data)
        if not match:
            self.request.sendall("Invalid command".encode())
            return

        command = match.group(1)
        argument = match.group(2)[1:] if match.group(2) else None

        if command == "status":
            print("[Dispatcher] Status check received")
            self.request.sendall("OK".encode())

        elif command == "register":
            self._handle_register(argument)

        elif command == "dispatch":
            self._handle_dispatch(argument)

        elif command == "results":
            self._handle_results(argument)

        else:
            self.request.sendall("Unknown command".encode())

    def _handle_register(self, argument):
        if not argument:
            self.request.sendall("Missing runner info".encode())
            return

        try:
            host, port_str = argument.split(":")
            port = int(port_str)
            runner = {"host": host, "port": port, "last_seen": time.time()}

            with runners_lock:
                # Prevent duplicate registrations
                if not any(r["host"] == host and r["port"] == port for r in registered_runners):
                    registered_runners.append(runner)
                    print(f"[Dispatcher] Registered runner: {host}:{port}")
                    self.request.sendall("OK".encode())
                else:
                    self.request.sendall("Runner already registered".encode())

        except Exception as e:
            error_msg = f"Invalid registration: {e}"
            print(f"[Dispatcher] {error_msg}")
            self.request.sendall(error_msg.encode())

    def _handle_dispatch(self, argument):
        commit_id = argument if argument else ""
        with runners_lock:
            if not registered_runners:
                self.request.sendall("No runners available".encode())
                return

        self.request.sendall("OK".encode())
        dispatch_tests(commit_id)

    def _handle_results(self, argument):
        if not argument:
            self.request.sendall("Missing results data".encode())
            return

        parts = argument.split(":", 2)
        if len(parts) < 3:
            self.request.sendall("Invalid results format".encode())
            return

        commit_id, length_str, result_data = parts
        try:
            expected_length = int(length_str)
        except ValueError:
            self.request.sendall("Invalid length in results".encode())
            return

        # Collect complete result data
        while len(result_data) < expected_length:
            try:
                extra = self.request.recv(self.BUF_SIZE).decode()
                result_data += extra
            except Exception as e:
                error_msg = f"Error receiving results: {e}"
                self.request.sendall(error_msg.encode())
                return

        try:
            os.makedirs(config.TEST_RESULTS_DIR, exist_ok=True)
            file_path = os.path.join(config.TEST_RESULTS_DIR, commit_id)
            with open(file_path, "w") as f:
                f.write(result_data)

            with commits_lock:
                if commit_id in dispatched_commits:
                    del dispatched_commits[commit_id]

            print(f"[Dispatcher] Results received for commit {commit_id}")
            self.request.sendall("OK".encode())

        except Exception as e:
            error_msg = f"Error saving results: {e}"
            print(f"[Dispatcher] {error_msg}")
            self.request.sendall(error_msg.encode())


class ThreadingTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    dead = False  # Shutdown flag


def runner_checker(server):
    """Periodically verify runner health with thread-safe operations"""
    while not server.dead:
        time.sleep(1)

        # Create safe snapshot of runners
        with runners_lock:
            current_runners = list(registered_runners)

        for runner in current_runners:
            try:
                response = helpers.communicate(
                    runner["host"], runner["port"], "ping")
                if response != "pong":
                    print(
                        f"[Dispatcher] Removing unresponsive runner: {runner['host']}:{runner['port']}")
                    remove_runner(runner)
            except Exception as e:
                print(
                    f"[Dispatcher] Connection failed to {runner['host']}:{runner['port']}: {e}")
                remove_runner(runner)


def remove_runner(runner):
    """Safely remove runner and requeue its commits"""
    with runners_lock:
        try:
            registered_runners.remove(runner)
            print(
                f"[Dispatcher] Removed runner: {runner['host']}:{runner['port']}")
        except ValueError:
            return

    requeued = []
    with commits_lock:
        # Find and requeue affected commits
        for commit_id, assigned in list(dispatched_commits.items()):
            if assigned == runner:
                del dispatched_commits[commit_id]
                pending_commits.append(commit_id)
                requeued.append(commit_id)

    if requeued:
        print(f"[Dispatcher] Requeued commits: {requeued}")


def redistribute(server):
    """Process pending commits in batches with thread-safe operations"""
    while not server.dead:
        time.sleep(1)

        # Get all pending commits atomically
        with commits_lock:
            current_pending = list(pending_commits)
            pending_commits.clear()

        for commit_id in current_pending:
            print(f"[Dispatcher] Re-dispatching {commit_id}")
            dispatch_tests(commit_id)


def dispatch_tests(commit_id):
    """Find and assign runner for commit with thread safety"""
    while True:
        # Get current runner snapshot
        with runners_lock:
            available_runners = list(registered_runners)

        for runner in available_runners:
            try:
                response = helpers.communicate(
                    runner["host"],
                    runner["port"],
                    f"runtest:{commit_id}"
                )
                if response == "OK":
                    with commits_lock:  # Atomic state update
                        dispatched_commits[commit_id] = runner
                        try:
                            # Remove from pending if still present
                            pending_commits.remove(commit_id)
                        except ValueError:
                            pass
                    print(
                        f"[Dispatcher] Dispatched {commit_id} to {runner['host']}:{runner['port']}")
                    return
            except Exception as e:
                print(f"[Dispatcher] Dispatch error to {runner['host']}: {e}")

        time.sleep(2)


def serve():
    """Main server function with graceful shutdown handling"""
    parser = argparse.ArgumentParser(
        description="Dispatcher Server for CI system")
    parser.add_argument("--host", default="localhost", type=str,
                        help="Dispatcher host (default: localhost)")
    parser.add_argument("--port", default=8888, type=int,
                        help="Dispatcher port (default: 8888)")
    args = parser.parse_args()

    server = ThreadingTCPServer((args.host, args.port), DispatcherHandler)
    print(f"[Dispatcher] Running on {args.host}:{args.port}")

    try:
        # Start maintenance threads (non-daemon)
        runner_thread = threading.Thread(target=runner_checker, args=(server,))
        redistributor_thread = threading.Thread(
            target=redistribute, args=(server,))

        runner_thread.start()
        redistributor_thread.start()

        server.serve_forever()

    except KeyboardInterrupt:
        print("\n[Dispatcher] Initiating graceful shutdown...")
        server.dead = True
        server.shutdown()

        # Allow threads to finish current operations
        runner_thread.join(timeout=2)
        redistributor_thread.join(timeout=2)

    finally:
        server.server_close()
        print("[Dispatcher] Server shut down complete")


if __name__ == "__main__":
    serve()
