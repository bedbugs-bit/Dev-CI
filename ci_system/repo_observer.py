"""
Monitors a Git repository for new commits.
Periodically, it invokes a shell script (update_repo.sh) that pulls the latest changes.
If a new commit is detected (indicated by a .commit_id file),
the dispatcher triggers a test run for that commit.
"""


import argparse
import subprocess
import time
import socket
from pathlib import Path

from ci_system import config, helpers


def scan():
    # Parse command-line arguments.
    parser = argparse.ArgumentParser(
        description="Repository Observer for the CI system")
    parser.add_argument("--dispatcher-server", default="localhost:8888",
                        help="Dispatcher host:port (default: localhost:8888)")
    parser.add_argument("repo", metavar="REPO", type=str,
                        help="Path to the repository to observe")
    args = parser.parse_args()

    dispatcher_host, dispatcher_port = args.dispatcher_server.split(":")
    dispatcher_port = int(dispatcher_port)

    # Main scanning loop, infinite while loop
    while True:
        try:
            # Update the repository using the shell script.
            subprocess.check_output(["./scripts/update_repo.sh", args.repo])
        except subprocess.CalledProcessError as err:
            raise Exception("Repository update failed: " + err.output.decode())

        # If a new commit is detected, the update script creates .commit_id.
        commit_id_file = Path(".commit_id")
        if commit_id_file.is_file():
            try:
                # Ensure dispatcher is available.
                response = helpers.communicate(
                    dispatcher_host, dispatcher_port, "status")
            except socket.error as err:
                raise Exception("Could not contact dispatcher: " + str(err))
            if response == "OK":
                # Read the commit ID from the file.
                commit = commit_id_file.read_text().strip()
                # Send a dispatch request for the new commit.
                dispatch_message = f"dispatch:{commit}"
                response = helpers.communicate(
                    dispatcher_host, dispatcher_port, dispatch_message)
                if response != "OK":
                    # TODO: add more error handling, the commit might already be dispatched
                    raise Exception("Dispatcher error: " + response)
                print(f"Dispatched commit {commit}")
                # Remove the .commit_id file.
                commit_id_file.unlink()
            else:
                # TODO: add more error handling, the dispatcher might be down
                raise Exception("Dispatcher returned error: " + response)
        time.sleep(config.REPO_POLL_INTERVAL)


if __name__ == "__main__":
    scan()
