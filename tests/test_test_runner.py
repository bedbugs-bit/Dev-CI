"""
tests/test_test_runner.py

Unit tests for the test runner module. This test simulates a "ping" command to ensure
the test runner responds with "pong" for health checks.
"""

import unittest
from ci_system import test_runner

class DummyRequest:
    def __init__(self, data):
        self.data = data.encode()
    def recv(self, bufsize):
        return self.data
    def sendall(self, data):
        self.response = data.decode()

class DummyTestHandler(test_runner.TestHandler):
    def __init__(self, data, server):
        self.request = DummyRequest(data)
        self.server = server
    def handle(self):
        super().handle()

class DummyServer:
    def __init__(self):
        self.repo_folder = "."
        self.dispatcher_server = {"host": "localhost", "port": 8888}
        self.last_communication = 0
        self.busy = False
        self.dead = False

class TestTestRunner(unittest.TestCase):
    def test_ping(self):
        server = DummyServer()
        handler = DummyTestHandler("ping", server)
        handler.handle()
        self.assertEqual(handler.request.response, "pong")

if __name__ == "__main__":
    unittest.main()
