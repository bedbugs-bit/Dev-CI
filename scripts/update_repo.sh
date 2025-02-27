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
COMMIT=$(run_or_fail "Could not get current commit" git log -n1)
COMMIT_ID=$(echo $COMMIT | awk '{ print $2 }')

# Pull the latest changes.
run_or_fail "Could not pull repository" git pull

# Capture the new commit ID.
NEW_COMMIT=$(run_or_fail "Could not get new commit" git log -n1)
NEW_COMMIT_ID=$(echo $NEW_COMMIT | awk '{ print $2 }')

# If the commit IDs differ, output the new commit hash.
if [ "$NEW_COMMIT_ID" != "$COMMIT_ID" ]; then
    popd > /dev/null
    echo $NEW_COMMIT_ID > .commit_id
fi
