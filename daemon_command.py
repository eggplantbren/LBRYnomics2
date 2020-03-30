import config
import json
import os
import time

def daemon_command(command):
    """
    Run a daemon command and return its output.
    """
    command = config.lbrynet_bin + " " + command
    os.system(command + " > daemon.out 2>&1")
    time.sleep(5.0)
    f = open("daemon.out")
    result = json.load(f)
    f.close()
    os.system("rm daemon.out")
    return result

