#!/bin/bash
# scripts/run_or_fail.sh
# ------------------------------------------------------------------------------
# A helper function to run a command and, if it fails, print an error message and exit.
# ------------------------------------------------------------------------------
run_or_fail() {
    MESSAGE=$1
    shift
    "$@"
    if [ $? -ne 0 ]; then
        echo "$MESSAGE"
        exit 1
    fi
}
