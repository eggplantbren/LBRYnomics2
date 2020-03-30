import config
import json
import os

def daemon_command(command):
    """
    Run a daemon command and return its output.
    """
    command = config.lbrynet_bin + " " + command
    os.system(command + " > daemon.out")
    f = open("daemon.out")
    result = json.load(f)
    f.close()
    os.system("rm daemon.out")
    return result

