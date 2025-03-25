"""
tests/test_test_runner.py

Unit tests for the test runner module. This test simulates a "ping" command to ensure
the test runner responds with "pong" (with an OK prefix) for health checks.
"""

import unittest
from ci_system import test_runner

class DummyRequest:
    def __init__(self, data):
        # Encode the provided data to bytes as if it were coming from a socket.
        self.data = data.encode()
        self.response = None

    def recv(self, bufsize):
        return self.data

    def sendall(self, data):
        # Capture the sent data after decoding.
        self.response = data.decode()

class DummyTestHandler(test_runner.TestRunnerHandler):
    def __init__(self, data, server):
        # Bypass the normal socketserver initialization and set attributes manually.
        self.request = DummyRequest(data)
        self.server = server

    def handle(self):
        # Call the parent class's handle method to process the request.
        super().handle()

class DummyServer:
    def __init__(self):
        # Set up the dummy server with attributes expected by TestRunnerHandler.
        self.repo_folder = "."
        self.dispatcher_server = {"host": "localhost", "port": 8888}
        self.last_communication = 0
        self.busy = False

class TestTestRunner(unittest.TestCase):
    def test_ping(self):
        # Create a dummy server instance.
        server = DummyServer()
        # Instantiate the DummyTestHandler with the "ping" command.
        handler = DummyTestHandler("ping", server)
        # Run the handler.
        handler.handle()
        # The _handle_ping method calls _send_response("pong"), and _send_response prefixes the message with "OK:".
        self.assertEqual(handler.request.response, "OK:pong")

if __name__ == "__main__":
    unittest.main()
