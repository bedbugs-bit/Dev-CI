#!/bin/bash
# scripts/update_repo.sh
# ------------------------------------------------------------------------------
# This script updates the Git repository located at the provided path.
# It resets the repository, pulls the latest changes, and compares commit IDs.
# If a new commit is detected, it writes the new commit hash to a file named .commit_id.
# ------------------------------------------------------------------------------

source scripts/run_or_fail.sh

# Remove previous .commit_id file if it exists.
rm -f .commit_id

# Change to the repository directory.
pushd "$1" > /dev/null || { echo "Repository folder not found!"; exit 1; }

# Reset the repository to HEAD.
run_or_fail "Could not reset git" git reset --hard HEAD

# Capture the current commit ID.
COMMIT_ID=$(git log -n1 --pretty=format:"%H") || { echo "Could not get current commit"; popd > /dev/null; exit 1; }

# Pull the latest changes.
run_or_fail "Could not pull repository" git pull

# Capture the new commit ID.
NEW_COMMIT_ID=$(git log -n1 --pretty=format:"%H") || { echo "Could not get new commit"; popd > /dev/null; exit 1; }

# Always revert to the previous directory.
popd > /dev/null

# If the commit IDs differ, output the new commit hash.
if [ "$NEW_COMMIT_ID" != "$COMMIT_ID" ]; then
    echo "$NEW_COMMIT_ID" > .commit_id
    echo "Repository updated! New commit ID: $NEW_COMMIT_ID"
else
    echo "No changes detected"
fi
