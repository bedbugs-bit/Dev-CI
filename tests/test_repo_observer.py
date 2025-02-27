"""
tests/test_repo_observer.py

A basic test for the repository observer. It creates a temporary Git repository,
runs the update_repo.sh script, and checks that no .commit_id file is created when
there is no new commit.
"""

import unittest
import os
import subprocess

class TestRepoObserver(unittest.TestCase):
    def test_no_new_commit(self):
        temp_repo = "temp_repo"
        os.makedirs(temp_repo, exist_ok=True)
        subprocess.call(["git", "init", temp_repo])
        subprocess.call(["./scripts/update_repo.sh", temp_repo])
        self.assertFalse(os.path.isfile(".commit_id"))
        subprocess.call(["rm", "-rf", temp_repo])

if __name__ == "__main__":
    unittest.main()
