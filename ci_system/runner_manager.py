"""
A Test runner manager that monitors the number of active test runners and
spawns new ones if the number falls bellow a desired threshold.

It uses subprocess to launch new test runner processes
"""

import argparse
import logging
import subprocess
import time
from typing import List

from ci_system import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class RunnerManager:
    """Manages test runner processes"""
    def __init__(self, repo_path: str, dispatcher_server: str):
        self.repo_path = repo_path
        self.dispatcher_server = dispatcher_server
        self.processes: List[subprocess.Popen] = []

    def maintain_pool(self, desired_count: int) -> None:
        """Maintain desired number of runners"""
        # Clean up terminated processes
        self.processes = [p for p in self.processes if p.poll() is None]
        
        # Spawn new runners if needed
        while len(self.processes) < desired_count:
            self._spawn_runner()
            
    def _spawn_runner(self) -> None:
        """Launch new test runner process"""
        try:
            proc = subprocess.Popen([
                "python", "ci_system/test_runner.py",
                self.repo_path,
                "--dispatcher-server", self.dispatcher_server,
                "--host", config.TEST_RUNNER_HOST,
                "--port", str(config.TEST_RUNNER_PORT)
            ])
            self.processes.append(proc)
            logger.info(f"Spawned runner PID: {proc.pid}")
        except Exception as e:
            logger.error(f"Failed to spawn runner: {e}")

def main():
    parser = argparse.ArgumentParser(description="Test Runner Manager")
    parser.add_argument("repo_path", help="Path to repository clone")
    parser.add_argument("--dispatcher-server", default="localhost:8888",
                        help="Dispatcher server host:port")
    parser.add_argument("--desired-count", type=int, default=2,
                        help="Target number of runners")
    
    args = parser.parse_args()
    manager = RunnerManager(args.repo_path, args.dispatcher_server)
    
    logger.info("Starting runner manager")
    try:
        while True:
            manager.maintain_pool(args.desired_count)
            time.sleep(config.RUNNER_CHECK_INTERVAL)
    except KeyboardInterrupt:
        logger.info("Shutting down manager")
        for proc in manager.processes:
            proc.terminate()

if __name__ == "__main__":
    main()