"""
deploy.py

A deployment script to launch the core services for Sprint One:
  - The dispatcher server.
  - A test runner (using a repository clone).
  - The repository observer.
  - The web reporter.

This script is intended for local development and testing.
"""

import subprocess

def deploy():
    # Start the dispatcher.
    dispatcher_proc = subprocess.Popen(["python", "ci_system/dispatcher.py", "--host", "0.0.0.0", "--port", "8888"])
    print("Dispatcher started on port 8888.")

    # Start one test runner (assumes repository clone exists in "./repo_clone").
    test_runner_proc = subprocess.Popen(["python", "ci_system/test_runner.py", "repo_clone",
                                           "--host", "0.0.0.0", "--port", "0",
                                           "--dispatcher-server", "localhost:8888"])
    print("Test Runner started.")

    # Start the repository observer.
    observer_proc = subprocess.Popen(["python", "ci_system/repo_observer.py", "--dispatcher-server", "localhost:8888", "repo_clone"])
    print("Repository Observer started.")

    # Start the web reporter.
    reporter_proc = subprocess.Popen(["python", "ci_system/reporter.py"])
    print("Web Reporter started on port 5000.")

    try:
        dispatcher_proc.wait()
        test_runner_proc.wait()
        observer_proc.wait()
        reporter_proc.wait()
    except KeyboardInterrupt:
        print("Shutting down CI system.")
        dispatcher_proc.terminate()
        test_runner_proc.terminate()
        observer_proc.terminate()
        reporter_proc.terminate()

if __name__ == "__main__":
    deploy()
