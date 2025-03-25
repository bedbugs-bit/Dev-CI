# Continuous Integration System

Welcome! DevCI is a distributed Continuous Integration (CI) system comprising multiple components that work together to manage repositories, execute tasks, and report results. Below are instructions for setting up and running the system.

## Table of Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Setup and Execution](#setup-and-execution)
  - [Terminal 1: Dispatcher](#terminal-1-dispatcher)
  - [Terminal 2: Runner Manager](#terminal-2-runner-manager)
  - [Terminal 3: Repository Observer](#terminal-3-repository-observer)
  - [Terminal 4: Web Reporter](#terminal-4-web-reporter)
- [Troubleshooting](#troubleshooting)
- [Why Use Modules?](#why-use-modules)


## Overview

The Distributed CI system is designed to:
- Monitor repositories for changes.
- Dispatch tasks to runners for execution.
- Report the results of tasks via a web interface.

The system is composed of the following components:
1. **Dispatcher**: Manages communication between components.
2. **Runner Manager**: Manages task runners.
3. **Repository Observer**: Observes repositories for changes.
4. **Web Reporter**: Flask Web app that reports the status of tasks via a web interface.


## Prerequisites

- Python 3.8 or higher
- Required Python packages (install via `pip install -r requirements.txt`)
- A local or remote repository to monitor


## Setup and Execution

### Terminal 1: Dispatcher
The dispatcher is the central communication hub for the system.

```bash
cd ci_system
python3 dispatcher.py --host 0.0.0.0 --port 8888
```

### Terminal 2: Runner Manager
The runner manager handles task runners. Start it as follows:

```bash
python3 -m ci_system.runner_manager ../test_repo_clone_runner \
  --dispatcher-server localhost:8888 \
  --desired-count 3
```

### Terminal 3: Repository Observer
The repository observer monitors repositories for changes. Start it for each repository:

```bash
python3 -m ci_system.repo_observer ../test_repo_clone_obs --dispatcher-server localhost:8888
```

### Terminal 4: Web Reporter
The web reporter provides a web interface for reporting task statuses. Start it as follows:

```bash
python3 -m ci_system.reporter
```

## Troubleshooting

### Git Pull Failing in `update_repo.sh`
If `git pull` fails for local repositories, ensure:
1. The repository has no uncommitted changes.
2. The repository is accessible and the correct branch is checked out.
3. The script has the necessary permissions to execute.


## Why Use Modules?

Some components are started as modules (e.g., `python3 -m ci_system.runner_manager`) instead of directly running scripts. This approach:
- Ensures proper module resolution within the package.
- Allows relative imports to work correctly.
- Makes the system more modular and maintainable.
