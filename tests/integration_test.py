"""
tests/integration_test.py

An integration test that simulates the full CI pipeline:
  - Creates a temporary Git repository with a dummy test.
  - Commits initial code and then a new change to trigger the CI.
  - Starts the dispatcher, test runner, and repository observer.
  - Verifies that a test result file is created in the test_results directory.
"""

import unittest
import subprocess
import time
import os


class IntegrationTest(unittest.TestCase):
    def test_full_pipeline(self):
        repo_dir = "temp_integration_repo"
        os.makedirs(repo_dir, exist_ok=True)
        subprocess.call(["git", "init", repo_dir])

        # Create a dummy test in tests directory.
        tests_dir = os.path.join(repo_dir, "tests")
        os.makedirs(tests_dir, exist_ok=True)
        with open(os.path.join(tests_dir, "test_dummy.py"), "w") as f:
            f.write("import unittest\n")
            f.write("class DummyTest(unittest.TestCase):\n")
            f.write("    def test_dummy(self):\n")
            f.write("        self.assertTrue(True)\n")
            f.write("if __name__ == '__main__':\n")
            f.write("    unittest.main()\n")

        # Initial commit.
        subprocess.call(["git", "-C", repo_dir, "add", "."])
        subprocess.call(["git", "-C", repo_dir, "commit", "-m", "Initial commit"])

        # Start dispatcher.
        dispatcher_proc = subprocess.Popen(
            ["python", "ci_system/dispatcher.py", "--host", "localhost", "--port", "8888"])
        # Start test runner.
        test_runner_proc = subprocess.Popen(
            ["python", "ci_system/test_runner.py", repo_dir, "--host", "localhost", "--port", "0",
             "--dispatcher-server", "localhost:8888"])
        # Start repository observer.
        observer_proc = subprocess.Popen(
            ["python", "ci_system/repo_observer.py", "--dispatcher-server", "localhost:8888", repo_dir])

        time.sleep(2)
        # Make a new commit to trigger CI.
        with open(os.path.join(repo_dir, "new_file.txt"), "w") as f:
            f.write("New commit content.\n")
        subprocess.call(["git", "-C", repo_dir, "add", "new_file.txt"])
        subprocess.call(["git", "-C", repo_dir, "commit", "-m", "New commit"])

        # Allow time for processing.
        time.sleep(10)

        result_files = os.listdir("test_results") if os.path.exists("test_results") else []
        self.assertTrue(len(result_files) > 0)

        # Cleanup.
        dispatcher_proc.terminate()
        test_runner_proc.terminate()
        observer_proc.terminate()
        subprocess.call(["rm", "-rf", repo_dir])


if __name__ == "__main__":
    unittest.main()
