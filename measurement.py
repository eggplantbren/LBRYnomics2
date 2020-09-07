import apsw
import collections
import datetime
import config
import json
import numpy as np
import requests
import time


# Database connections
ldb_conn = apsw.Connection("db/lbrynomics.db")
ldb = ldb_conn.cursor()
ldb.execute("PRAGMA JOURNAL_MODE=WAL;")

def make_measurement(k):

    # Get reader
    cdb_conn = apsw.Connection(config.claims_db_file,
                                flags=apsw.SQLITE_OPEN_READONLY)
    cdb_conn.setbusytimeout(60000)
    cdb = cdb_conn.cursor()


    # Get current timestamp
    now = time.time()

    m = 1 + ldb.execute("SELECT COUNT(*) FROM measurements;")\
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
    output = cdb.execute(query)
    measurement["num_channels"] = output.fetchone()[0]
    measurement["num_streams"]  = output.fetchone()[0]
#    measurement["num_reposts"] = output.fetchone()[0]

    # Query claims.db to get some measurement info
    query = """
            SELECT SUM(amount)/1E8 FROM claim;
            """
    output = cdb.execute(query)
    measurement["lbc_deposits"] = output.fetchone()[0]


    # Query claims.db to get some measurement info
    query = """
            SELECT COUNT(*), SUM(amount)/1E8 FROM support;
            """
    output = cdb.execute(query)
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
            if measurement["circulating_supply"] <= 0.0:
                measurement["circulating_supply"] = None

    # Count reposts
    query = "SELECT COUNT(claim_hash) FROM claim WHERE claim_type=3;"
    measurement["num_reposts"] = None
    try:
        measurement["num_reposts"] = cdb.execute(query).fetchone()[0]
    except:
        pass

    # Measure number of claims over which LBC is spread (exp of shannon entropy)
    ps = []
    if k % 20 == 0:
        for row in cdb.execute("SELECT (amount + support_amount) FROM claim;"):
            ps.append(row[0])
        ps = np.array(ps)
        ps = ps/ps.sum()
        measurement["lbc_spread"] = np.exp(-np.sum(ps*np.log(ps)))
    else:
        measurement["lbc_spread"] = None

    # Open output DB and write to it
    lbrynomics_db = apsw.Connection("db/lbrynomics.db")
    query = """
            INSERT INTO measurements (time, num_channels, num_streams,
                                      lbc_deposits, num_supports, lbc_supports,
                                      ytsync_new_pending, ytsync_pending_update,
                                      ytsync_pending_upgrade, ytsync_failed,
                                      circulating_supply, num_reposts, lbc_spread)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """
    ldb.execute("BEGIN;")
    ldb.execute(query, tuple(measurement.values()))
    ldb.execute("COMMIT;")

    cdb_conn.close()

    print("    " + json.dumps(measurement, indent=4).replace("\n", "\n    "))
    print("Done.\n", flush=True)
    return measurement

