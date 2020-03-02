import apsw
import collections
from databases import dbs
import datetime
import config
import json
import requests
import time




def make_measurement(k):

    # Get current timestamp
    now = time.time()

    m = 1 + dbs["lbrynomics"].execute("SELECT COUNT(*) FROM measurements;")\
                .fetchone()[0]
    print(f"Making measurement {m}. ", end="")
    print("The time is " + str(datetime.datetime.utcfromtimestamp(int(now)))\
                 + " UTC.", flush=True)

    # Measurement measurement
    measurement = collections.OrderedDict()
    measurement["time"] = now

    # Query claims.db to get some measurement info
    query = """
            SELECT COUNT(*), claim_type FROM claim
            GROUP BY claim_type
            HAVING claim_type = 1 OR claim_type = 2
            ORDER BY claim_type DESC;
            """
    output = dbs["claims"].execute(query)
    measurement["num_channels"] = output.fetchone()[0]
    measurement["num_streams"]  = output.fetchone()[0]

    # Query claims.db to get some measurement info
    query = """
            SELECT SUM(amount)/1E8 FROM claim;
            """
    output = dbs["claims"].execute(query)
    measurement["lbc_deposits"] = output.fetchone()[0]


    # Query claims.db to get some measurement info
    query = """
            SELECT COUNT(*), SUM(amount)/1E8 FROM support;
            """
    output = dbs["claims"].execute(query)
    row = output.fetchone()
    measurement["num_supports"], measurement["lbc_supports"] = row

    # Get ytsync numbers
    url = "https://api.lbry.com/yt/queue_status"
    try:
        response = requests.get(url, timeout=5).json()
    except:
        response = { "success": False }
    if response["success"]:
        data = response["data"]
        measurement["ytsync_new_pending"] = data["NewPending"]
        measurement["ytsync_pending_update"] = data["PendingUpdate"]
        measurement["ytsync_pending_upgrade"] = data["PendingUpgrade"]
        measurement["ytsync_failed"] = data["Failed"]
    else:
        measurement["ytsync_new_pending"] = None
        measurement["ytsync_pending_update"] = None
        measurement["ytsync_pending_upgrade"] = None
        measurement["ytsync_failed"] = None

    # Get circulating supply
    measurement["circulating_supply"] = None
    url = "https://explorer.lbry.com/api/v1/supply"
    if k % 10 == 0:

        try:
            response = requests.get(url, timeout=5).json()
        except:
            response = { "success": False }

        if response["success"]:
            measurement["circulating_supply"] = response["utxosupply"]["circulating"]

    # Count reposts
    query = "SELECT SUM(reposted) FROM claim;"
    measurement["num_reposts"] = None
    try:
        measurement["num_reposts"] = dbs["claims"].execute(query).fetchone()[0]
    except:
        pass

    # Open output DB and write to it
    lbrynomics_db = apsw.Connection("db/lbrynomics.db")
    query = """
            INSERT INTO measurements (time, num_channels, num_streams,
                                      lbc_deposits, num_supports, lbc_supports,
                                      ytsync_new_pending, ytsync_pending_update,
                                      ytsync_pending_upgrade, ytsync_failed,
                                      circulating_supply, num_reposts)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """
    dbs["lbrynomics"].execute("BEGIN;")
    dbs["lbrynomics"].execute(query, tuple(measurement.values()))
    dbs["lbrynomics"].execute("COMMIT;")

    print("    " + json.dumps(measurement, indent=4).replace("\n", "\n    "))
    print("Done.\n")
    return measurement

