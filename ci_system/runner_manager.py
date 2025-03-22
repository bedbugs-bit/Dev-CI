"""
A Test runner manager that monitors the number of active test runners and
spawns new ones if the number falls bellow a desired threshold.

It uses subprocess to launch new test runner processes
"""

import argparse
import subprocess
import time
from ci_system import config


def spawn_test_runner(repo_clone_path, dispatcher_server, host="localhost", port=0):
    """
    Spawns a new test runner process.

    Args:
        repo_clone_path (str): Path to the repository clone.
        dispatcher_server (str): Dispatcher server in the form host:port.
        host (str): Host on which to run the test runner.
        port (int): Port for the test runner (0 for auto-assignment).

    Returns:
        subprocess.Popen: Handle to the spawned process.
    """
    command = ["python", "ci_system/test_runner.py", repo_clone_path,
               "--host", host,
               "--port", str(port),
               "--dispatcher-server", dispatcher_server]
    proc = subprocess.Popen(command)
    return proc


def monitor_and_scale(repo_clone_path, dispatcher_server, desired_count):
    """
    Monitors active test runner processes and spawns new ones to meet the desired count.

    Args:
        repo_clone_path (str): Path to repository clone.
        dispatcher_server (str): Dispatcher server address (host:port).
        desired_count (int): Desired number of concurrent test runners.
    """
    runners = []
    while True:
        # Filter out processes that have terminated.
        runners = [r for r in runners if r.poll() is None]
        if len(runners) < desired_count:
            new_runner = spawn_test_runner(repo_clone_path, dispatcher_server)
            runners.append(new_runner)
            print(f"Spawned new test runner. Total active runners: {len(runners)}")
        time.sleep(10)  # Check every 10 seconds.


def main():
    parser = argparse.ArgumentParser(description="Test Runner Manager for CI system")
    parser.add_argument("repo_clone_path", help="Path to repository clone for testing")
    parser.add_argument("--dispatcher-server", default="localhost:8888",
                        help="Dispatcher server host:port (default: localhost:8888)")
    parser.add_argument("--desired-count", default=2, type=int,
                        help="Desired number of active test runners")
    args = parser.parse_args()
    monitor_and_scale(args.repo_clone_path, args.dispatcher_server, args.desired_count)


if __name__ == "__main__":
    main()