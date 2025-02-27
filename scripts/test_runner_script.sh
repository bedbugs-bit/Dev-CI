#!/bin/bash
# scripts/test_runner_script.sh
# ------------------------------------------------------------------------------
# This script resets the repository clone to the specified commit.
# It cleans the repository, pulls the latest changes, and resets to the given commit.
# ------------------------------------------------------------------------------
REPO=$1
COMMIT=$2

source scripts/run_or_fail.sh

pushd "$REPO" > /dev/null || { echo "Repository folder not found"; exit 1; }

# Clean untracked files.
run_or_fail "Could not clean repository" git clean -d -f -x

# Pull the latest changes.
run_or_fail "Could not pull repository" git pull

# Reset the repository to the given commit.
run_or_fail "Could not reset to commit" git reset --hard "$COMMIT"

popd > /dev/null
echo "Repository updated to commit $COMMIT"
