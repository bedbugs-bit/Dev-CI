"""
 Test runner register itself with the dispatcher and listens for commands:
    - "ping": returns "pong" for health checks.
    - "runtest:<commit_id>": upon receiving a commit ID, updates its repository clone,
     runs tests using unittest, and sends the test results back to the dispatcher.
"""

import argparse
import os
import socket
import socketserver
import subprocess
import threading
import time
import unittest

from ci_system import config, helpers

class TestHandler(socketserver.BaseRequestHandler):
    BUF_SIZE = 1024

    def handle(self):
        data = self.request.recv(self.BUF_SIZE).strip().decode()
        print("Test Runner received:", data)
        parts = data.split(":", 1)
        command = parts[0]
        argument = parts[1] if len(parts) > 1 else None

        if command == "ping":
            self.server.last_communication = time.time()
            self.request.sendall("pong".encode())

        elif command == "runtest":
            if self.server.busy:
                self.request.sendall("BUSY".encode())
            else:
                self.request.sendall("OK".encode())
                commit_id = argument if argument else ""
                self.server.busy = True
                threading.Thread(target=self.run_tests, args=(commit_id,), daemon=True).start()
        else:
            self.request.sendall("Unknown command".encode())

    def run_tests(self, commit_id):
        repo_folder = self.server.repo_folder
        try:
            # Update the repository clone to the given commit.
            output = subprocess.check_output(["./scripts/test_runner_script.sh", repo_folder, commit_id])
            print(f"Repository updated to commit {commit_id}: {output.decode()}")
        except subprocess.CalledProcessError as e:
            result_data = f"Error updating repository: {e.output.decode()}"
            self.send_results(commit_id, result_data)
            self.server.busy = False
            return

        # Discover and run tests in the repository's "tests" directory.
        test_folder = os.path.join(repo_folder, "tests")
        suite = unittest.TestLoader().discover(test_folder)
        with open("results.txt", "w") as result_file:
            unittest.TextTestRunner(stream=result_file).run(suite)
        with open("results.txt", "r") as result_file:
            result_data = result_file.read()
        self.send_results(commit_id, result_data)
        self.server.busy = False

    def send_results(self, commit_id, result_data):
        dispatcher_host = self.server.dispatcher_server["host"]
        dispatcher_port = self.server.dispatcher_server["port"]
        message = f"results:{commit_id}:{len(result_data)}:{result_data}"
        try:
            response = helpers.communicate(dispatcher_host, dispatcher_port, message)
            if response == "OK":
                print(f"Results for commit {commit_id} sent successfully.")
            else:
                print(f"Error sending results: {response}")
        except Exception as e:
            print(f"Exception sending results: {e}")

class ThreadingTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    def __init__(self, server_address, RequestHandlerClass, repo_folder, dispatcher_server):
        super().__init__(server_address, RequestHandlerClass)
        self.repo_folder = repo_folder
        self.dispatcher_server = dispatcher_server  # Dictionary: {"host": str, "port": int}
        self.last_communication = time.time()
        self.busy = False
        self.dead = False

def dispatcher_checker(server):
    """
    Periodically checks whether the dispatcher is still available.
    If the dispatcher is unresponsive, shuts down the test runner.
    """
    while not server.dead:
        time.sleep(5)
        if time.time() - server.last_communication > config.HEARTBEAT_TIMEOUT:
            try:
                response = helpers.communicate(server.dispatcher_server["host"],
                                               server.dispatcher_server["port"],
                                               "status")
                if response != "OK":
                    print("Dispatcher unresponsive. Shutting down test runner.")
                    server.shutdown()
                    return
            except Exception as e:
                print(f"Dispatcher check error: {e}. Shutting down test runner.")
                server.shutdown()
                return

def serve():
    parser = argparse.ArgumentParser(description="Test Runner for the CI system")
    parser.add_argument("repo_folder", help="Path to repository clone for testing")
    parser.add_argument("--host", default="localhost", help="Test Runner host (default: localhost)")
    parser.add_argument("--port", default=0, type=int, help="Test Runner port (0 for auto-assignment)")
    parser.add_argument("--dispatcher-server", default="localhost:8888",
                        help="Dispatcher server host:port (default: localhost:8888)")
    args = parser.parse_args()

    dispatcher_host, dispatcher_port = args.dispatcher_server.split(":")
    dispatcher_server_info = {"host": dispatcher_host, "port": int(dispatcher_port)}

    server = ThreadingTCPServer((args.host, args.port), TestHandler, args.repo_folder, dispatcher_server_info)
    assigned_port = server.server_address[1]
    print(f"Test Runner running on {args.host}:{assigned_port}")

    # Register with the dispatcher.
    register_message = f"register:{args.host}:{assigned_port}"
    try:
        response = helpers.communicate(dispatcher_host, int(dispatcher_port), register_message)
        if response != "OK":
            print("Registration with dispatcher failed:", response)
            return
    except Exception as e:
        print("Error during registration with dispatcher:", e)
        return

    threading.Thread(target=dispatcher_checker, args=(server,), daemon=True).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Test Runner shutting down.")
        server.dead = True
        server.shutdown()

if __name__ == "__main__":
    serve()