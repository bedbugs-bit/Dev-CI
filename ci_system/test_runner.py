"""
 Test runner register itself with the dispatcher and listens for commands:
    - "ping": returns "pong" for health checks.
    - "runtest:<commit_id>": upon receiving a commit ID, updates its repository clone,
     runs tests using unittest, and sends the test results back to the dispatcher.
"""

import argparse
import logging
import os
import socketserver
import subprocess
import threading
import time
import unittest
from typing import Dict, Tuple

from ci_system import helpers

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class TestRunnerHandler(socketserver.BaseRequestHandler):
    """Handles incoming test execution requests"""
    BUFFER_SIZE = 4096  # For large test results
    
    def handle(self) -> None:
        try:
            data = self.request.recv(self.BUFFER_SIZE).decode().strip()
            if ':' in data:
                command, argument = data.split(':', 1)
            else:
                command, argument = data, None

            if command == "ping":
                self._handle_ping()
            elif command == "runtest":
                self._handle_runtest(argument)
            else:
                self._send_response("Unknown command", error=True)
        except Exception as e:
            logger.error(f"Request handling error: {e}")
            self._send_response(f"Internal error: {e}", error=True)

    def _handle_ping(self) -> None:
        """Update last communication timestamp"""
        self.server.last_communication = time.time()
        self._send_response("pong")

    def _handle_runtest(self, commit_id: str) -> None:
        """Handle test execution request"""
        if self.server.busy:
            self._send_response("BUSY")
            return

        self.server.busy = True
        self._send_response("OK")
        
        try:
            threading.Thread(
                target=self._execute_test_run,
                args=(commit_id,),
                daemon=True
            ).start()
        except Exception as e:
            logger.error(f"Failed to start test thread: {e}")
            self.server.busy = False

    def _execute_test_run(self, commit_id: str) -> None:
        """Full test execution workflow"""
        try:
            self._update_repository(commit_id)
            results = self._run_test_suite()
            self._report_results(commit_id, results)
        except subprocess.CalledProcessError as e:
            error_msg = f"Repository update failed: {e.output.decode()}"
            self._report_results(commit_id, error_msg, error=True)
        except Exception as e:
            error_msg = f"Test execution error: {str(e)}"
            self._report_results(commit_id, error_msg, error=True)
        finally:
            self.server.busy = False

    def _update_repository(self, commit_id: str) -> None:
        """Update repository to specified commit"""
        logger.info(f"Updating to commit {commit_id}")
        result = subprocess.run(
            ["./scripts/test_runner_script.sh", self.server.repo_folder, commit_id],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        logger.debug(f"Update output: {result.stdout.decode()}")

    def _run_test_suite(self) -> str:
        """Execute tests and return results"""
        test_dir = os.path.join(self.server.repo_folder, "tests")
        logger.info(f"Running tests in {test_dir}")
        
        with open("test_results.tmp", "w") as f:
            runner = unittest.TextTestRunner(stream=f, verbosity=2)
            suite = unittest.TestLoader().discover(test_dir)
            runner.run(suite)
        
        with open("test_results.tmp", "r") as f:
            return f.read()

    def _report_results(self, commit_id: str, results: str, error: bool = False) -> None:
        """Send results to dispatcher"""
        try:
            status = "error" if error else "results"
            response = helpers.communicate(
                self.server.dispatcher_server["host"],
                self.server.dispatcher_server["port"],
                f"{status}:{commit_id}:{len(results)}:{results}"
            )
            logger.info(f"Results for {commit_id} {'failed' if error else 'sent'}")
        except Exception as e:
            logger.error(f"Failed to report results: {e}")

    def _send_response(self, message: str, error: bool = False) -> None:
        """Send response to dispatcher"""
        try:
            prefix = "ERROR:" if error else "OK:"
            self.request.sendall(f"{prefix}{message}".encode())
        except Exception as e:
            logger.error(f"Response failed: {e}")

class ThreadedTestRunner(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """Threaded test runner server"""
    allow_reuse_address = True
    daemon_threads = True
    
    def __init__(
        self,
        server_address: Tuple[str, int],
        handler_class,
        repo_folder: str,
        dispatcher_info: Dict[str, str]
    ):
        super().__init__(server_address, handler_class)
        self.repo_folder = repo_folder
        self.dispatcher_server = dispatcher_info
        self.last_communication = time.time()
        self.busy = False

def start_test_runner():
    """Main entry point for test runner service"""
    parser = argparse.ArgumentParser(description="CI Test Runner")
    parser.add_argument("repo_folder", help="Path to repository clone")
    parser.add_argument("--host", default="localhost", help="Binding host")
    parser.add_argument("--port", type=int, default=0, help="Listening port (0=auto)")
    parser.add_argument("--dispatcher-server", default="localhost:8888",
                        help="Dispatcher host:port")
    
    args = parser.parse_args()
    dispatcher_host, dispatcher_port = args.dispatcher_server.split(":")
    
    try:
        with ThreadedTestRunner(
            (args.host, args.port),
            TestRunnerHandler,
            args.repo_folder,
            {"host": dispatcher_host, "port": int(dispatcher_port)}
        ) as server:
            logger.info(f"Test runner started on {server.server_address[0]}:{server.server_address[1]}")
            
            # Register with dispatcher
            register_msg = f"register:{args.host}:{server.server_address[1]}"
            response = helpers.communicate(dispatcher_host, int(dispatcher_port), register_msg)
            if response != "OK":
                logger.error("Registration failed")
                return
                
            server.serve_forever()
            
    except KeyboardInterrupt:
        logger.info("Shutting down test runner")
    except Exception as e:
        logger.error(f"Fatal error: {e}")

if __name__ == "__main__":
    start_test_runner()