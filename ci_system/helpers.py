"""
Provides the utilities(functions) need for the CI system:
    - communicate
    - run-command
"""

import socket
import subprocess

def communicate(host: str, port: int, message: str) -> str:
    """
        Connect via TCP to the specified host and port.
        Sends the message and returns the decoded response

    :param host: The target hostname or IP
    :param port: The target port
    :param message: The message to edn
    :return:  The decoded response from the remote host.
    :raises Exception: if any error occurs
    """

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
        s.sendall(message.encode())
        response = s.recv(4096)
        s.close()

        return response.decode()

    except Exception as e:
        raise Exception(f"Communication error with {host}:{port} - {e}")

def run_command(command: str) -> str:
    """
    Execute a shell command and returns its output
    :param command: command to execute
    :return: decoded output of the command
    :raises Exception: If the command exits with a non-zero status
    """

    try:
        output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
        return output.decode()
    except subprocess.CalledProcessError as e:
        raise Exception(f"Command failed: {command}\nOutput: {e.output.decode()}")

