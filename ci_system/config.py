"""
This module defines constants for the distributed CI system.
It includes host/port settings for the dispatcher, test runner configuration,
repository polling intervals, heartbeat timeouts, result storage paths, and logging levels.
"""
from pathlib import Path
# import os

# ------------------------------------------------------------------------------
# Dispatcher Server Configuration
# ------------------------------------------------------------------------------

DISPATCHER_HOST = "localhost"
DISPATCHER_PORT = 8888

# ------------------------------------------------------------------------------
# Test Runner Configuration
# ------------------------------------------------------------------------------
# If not explicitly provided, test runners may use an auto-assigned port.
TEST_RUNNER_PORT_RANGE = (8900, 9000)

# ------------------------------------------------------------------------------
# Repository Observer Settings
# ------------------------------------------------------------------------------
REPO_POLL_INTERVAL = 5  # seconds between polling cycles

# ------------------------------------------------------------------------------
# Heartbeat Settings
# ------------------------------------------------------------------------------
HEARTBEAT_TIMEOUT = 10  # seconds before considering a runner unresponsive

# ------------------------------------------------------------------------------
# Test Results Directory
# ------------------------------------------------------------------------------
# TEST_RESULTS_DIR = os.path.join(os.getcwd(), "test_results")
# if not os.path.exists(TEST_RESULTS_DIR):
#     os.makedirs(TEST_RESULTS_DIR)

TEST_RESULTS_DIR = Path.cwd() / "test_results"
TEST_RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------------------------
# Logging Settings
# ------------------------------------------------------------------------------
LOG_LEVEL = "DEBUG"

