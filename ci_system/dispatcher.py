"""
The dispatcher is the central coordinator. It receives:
  - "status" requests (to verify its availability)
  - "register" requests (from test runners)
  - "dispatch" requests (with commit IDs from the repository observer)
  - "results" requests (with test outcomes from runners)

  It also monitors the health of registered test runners and reassigns jobs as needed.
"""

import argparse
import os
import socket
import threading
import time
import socketserver

from ci_system import config, helpers

# Global structures for runner and commit tracking.
registered_runners = []       # List of dicts: {"host": str, "port": int, "last_seen": float}
dispatched_commits = {}       # Mapping commit_id -> runner info
pending_commits = []          # Queue of commits waiting to be dispatched

class DispatcherHandler(socketserver.BaseRequestHandler):
    BUF_SIZE = 1024

    def handle(self):
        """
        handle incoming request from clients based on commands(status, register, dispatch, results)
        :return:
        """
        data = self.request.recv(DispatcherHandler.BUF_SIZE).strip().decode()
        print("Dispatcher received:", data)
        parts = data.split(":", 1)
        command = parts[0]
        argument = parts[1] if len(parts) > 1 else None

        if command == "status":
            self.request.sendall("OK".encode())

        elif command == "register":
            if argument:
                try:
                    host, port = argument.split(":")
                    runner = {"host": host, "port": int(port), "last_seen": time.time()}
                    registered_runners.append(runner)
                    print(f"Registered runner: {host}:{port}")
                    self.request.sendall("OK".encode())
                except Exception as e:
                    self.request.sendall(f"Invalid register info: {e}".encode())
            else:
                self.request.sendall("Missing runner info".encode())

        elif command == "dispatch":
            commit_id = argument if argument else ""
            if not registered_runners:
                self.request.sendall("No runners available".encode())
            else:
                self.request.sendall("OK".encode())
                dispatch_tests(commit_id)

        elif command == "results":
            # Expected format: results:<commit_id>:<length>:<result_data>
            if argument:
                args = argument.split(":", 2)
                if len(args) < 3:
                    self.request.sendall("Invalid results format".encode())
                    return
                commit_id, length_str, result_data = args
                try:
                    expected_length = int(length_str)
                except ValueError:
                    self.request.sendall("Invalid length in results".encode())
                    return
                # Ensure full data is received.
                while len(result_data) < expected_length:
                    result_data += self.request.recv(DispatcherHandler.BUF_SIZE).decode()
                os.makedirs(config.TEST_RESULTS_DIR, exist_ok=True)
                file_path = os.path.join(config.TEST_RESULTS_DIR, commit_id)
                with open(file_path, "w") as f:
                    f.write(result_data)
                if commit_id in dispatched_commits:
                    del dispatched_commits[commit_id]
                print(f"Results received for commit {commit_id}")
                self.request.sendall("OK".encode())
            else:
                self.request.sendall("Missing results data".encode())
        else:
            self.request.sendall("Unknown command".encode())

class ThreadingTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    def __init__(self, server_address, RequestHandlerClass):
        super().__init__(server_address, RequestHandlerClass)
        self.dead = False

def runner_checker(server):
    """
    Periodically pings all registered test runners.
    If a runner is unresponsive, removes it and reassigns its commit.
    """
    global registered_runners, dispatched_commits, pending_commits
    while not server.dead:
        time.sleep(1)
        for runner in list(registered_runners):
            try:
                response = helpers.communicate(runner["host"], runner["port"], "ping")
                if response != "pong":
                    print(f"Runner {runner['host']}:{runner['port']} unresponsive. Removing.")
                    remove_runner(runner)
            except Exception:
                print(f"Runner {runner['host']}:{runner['port']} failed to respond. Removing.")
                remove_runner(runner)

def remove_runner(runner):
    """
    Removes a runner from the registry and requeues its commit if needed.
    """
    global registered_runners, dispatched_commits, pending_commits
    if runner in registered_runners:
        registered_runners.remove(runner)
    for commit_id, assigned in list(dispatched_commits.items()):
        if assigned == runner:
            del dispatched_commits[commit_id]
            pending_commits.append(commit_id)
            print(f"Requeued commit {commit_id} due to runner removal.")

def redistribute(server):
    """
    Continuously checks for pending commits and attempts to dispatch them.
    """
    global pending_commits
    while not server.dead:
        if pending_commits:
            commit_id = pending_commits.pop(0)
            print(f"Redistributing commit {commit_id}")
            dispatch_tests(commit_id)
        time.sleep(5)

def dispatch_tests(commit_id):
    """
    Attempts to dispatch the given commit to an available runner.
    Retries until a runner accepts the job.
    """
    global registered_runners, dispatched_commits, pending_commits
    while True:
        for runner in registered_runners:
            try:
                response = helpers.communicate(runner["host"], runner["port"], f"runtest:{commit_id}")
                if response == "OK":
                    dispatched_commits[commit_id] = runner
                    print(f"Dispatched commit {commit_id} to runner {runner['host']}:{runner['port']}")
                    return
            except Exception as e:
                print(f"Error dispatching to runner {runner}: {e}")
        time.sleep(2)

def serve():
    parser = argparse.ArgumentParser(description="Dispatcher Server for CI system")
    parser.add_argument("--host", default="localhost", help="Dispatcher host (default: localhost)")
    parser.add_argument("--port", default=8888, type=int, help="Dispatcher port (default: 8888)")
    args = parser.parse_args()

    server = ThreadingTCPServer((args.host, args.port), DispatcherHandler)
    print(f"Dispatcher running on {args.host}:{args.port}")

    # Start background threads for runner health checking and commit redistribution.
    threading.Thread(target=runner_checker, args=(server,), daemon=True).start()
    threading.Thread(target=redistribute, args=(server,), daemon=True).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Dispatcher shutting down.")
        server.dead = True
        server.shutdown()

if __name__ == "__main__":
    serve()

