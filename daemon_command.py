import config
import json
import subprocess

def daemon_command(command):
    """
    Run a daemon command and return its output.
    """
    command = config.lbrynet_bin + " " + command
    parts = command.split(" ")
    output = subprocess.run(parts, capture_output=True)
    return json.loads(output.stdout)

