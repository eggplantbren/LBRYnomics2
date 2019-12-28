import json
import subprocess


claims_db_file = "/home/brewer/local/lbry-sdk/lbry/lbryum_data/claims.db"
interval = 300.0
lbrynet_bin = "/opt/LBRY/resources/static/daemon/lbrynet"
backup_dir = "/keybase/public/brendonbrewer/lbrynomics/"

def daemon_command(command):
    """
    Run a daemon command and return its output.
    """
    command = lbrynet_bin + " " + command
    parts = command.split(" ")
    output = subprocess.run(parts, capture_output=True)
    return json.loads(output.stdout)

