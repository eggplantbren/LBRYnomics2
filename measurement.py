import apsw
import collections
import datetime
import config
import json
import requests
import time




def make_measurement():

    # Get current timestamp
    now = time.time()

    print("Making measurement. ", end="")
    print("The time is " + str(datetime.datetime.utcfromtimestamp(int(now)))\
                 + " UTC.", flush=True)

    # Connect to the wallet server DB and the output DB
    claims_db = apsw.Connection(config.claims_db_file)

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
    output = claims_db.cursor().execute(query)
    measurement["num_channels"] = output.fetchone()[0]
    measurement["num_streams"]  = output.fetchone()[0]

    # Query claims.db to get some measurement info
    query = """
            SELECT SUM(amount)/1E8 FROM claim;
            """
    output = claims_db.cursor().execute(query)
    measurement["lbc_deposits"] = output.fetchone()[0]


    # Query claims.db to get some measurement info
    query = """
            SELECT COUNT(*), SUM(amount)/1E8 FROM support;
            """
    output = claims_db.cursor().execute(query)
    row = output.fetchone()
    measurement["num_supports"], measurement["lbc_supports"] = row

    # Close claims.db
    claims_db.close()

    # Get ytsync numbers
    url = "https://api.lbry.com/yt/queue_status"
    try:
        response = requests.get(url, timeout=5).json()
    except:
        response = { "success": False }
    if response["success"]:
        data = response["data"]
        measurement["ytsyc_new_pending"] = data["NewPending"]
        measurement["ytsyc_pending_update"] = data["PendingUpdate"]
        measurement["ytsync_pending_upgrade"] = data["PendingUpgrade"]
        measurement["ytsync_failed"] = data["Failed"]
    else:
        measurement["ytsyc_new_pending"] = None
        measurement["ytsyc_pending_update"] = None
        measurement["ytsync_pending_upgrade"] = None
        measurement["ytsync_failed"] = None


    # Open output DB and write to it
    lbrynomics_db = apsw.Connection("db/lbrynomics.db")
    query = """
            INSERT INTO measurements (time, num_channels, num_streams,
                                      lbc_deposits, num_supports, lbc_supports,
                                      ytsync_new_pending, ytsync_pending_update,
                                      ytsync_pending_upgrade, ytsync_failed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """
    lbrynomics_db.cursor().execute("BEGIN;")
    lbrynomics_db.cursor().execute(query, tuple(measurement.values()))
    lbrynomics_db.cursor().execute("COMMIT;")
    lbrynomics_db.close()

    print("    " + json.dumps(measurement, indent=4).replace("\n", "\n    "))
    print("Done.\n")
    return measurement

