"""
This module defines constants for the distributed CI system.
It includes host/port settings for the dispatcher, test runner configuration,
repository polling intervals, heartbeat timeouts, result storage paths, and logging levels.
"""


from pathlib import Path

# Base directory for test results
TEST_RESULTS_DIR = Path(__file__).parent / "test_results"
TEST_RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Network configurations
DISPATCHER_HOST = "localhost"
DISPATCHER_PORT = 8888

# Test runner settings
TEST_RUNNER_HOST = "localhost"
TEST_RUNNER_PORT_RANGE = (8900, 9000)

# Timing configurations
REPO_POLL_INTERVAL = 5  # Seconds between repository checks
HEARTBEAT_TIMEOUT = 10  # Seconds before considering a component unresponsive
RUNNER_CHECK_INTERVAL = 5  # Seconds between runner health checks

# Logging configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Web reporter settings
REPORTER_HOST = "0.0.0.0"
REPORTER_PORT = 5050
