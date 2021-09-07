import apsw
import collections
import datetime
import config
import hot_tags
import json
from lbrycrd_nodes import lbrycrd_nodes
import numpy as np
import subprocess
import requests
import time

# Database connections
ldb_conn = apsw.Connection("db/lbrynomics.db")
ldb = ldb_conn.cursor()
ldb.execute("PRAGMA JOURNAL_MODE=WAL;")
ldb.execute("PRAGMA SYNCHRONOUS=0;")
ldb.execute("PRAGMA AUTOVACUUM=ON;")

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
            SELECT num_streams, num_channels, num_reposts,
                   deposits_deweys, supports_deweys, num_supports,
                   num_collections FROM totals;
            """
    cdb.execute("BEGIN;")
    output = cdb.execute(query).fetchall()[0]
    cdb.execute("COMMIT;")

    measurement["num_streams"] = output[0]
    measurement["num_channels"]  = output[1]
    measurement["num_reposts"]  = output[2]
    measurement["lbc_deposits"] = output[3] / 1E8
    measurement["lbc_supports"] = output[4] / 1E8
    measurement["num_supports"] = output[5]
    measurement["num_collections"] = output[6]

    print(f"    num_streams = {measurement['num_streams']}.", flush=True)
    print(f"    num_channels = {measurement['num_channels']}.", flush=True)
    print(f"    num_reposts = {measurement['num_reposts']}.", flush=True)
    print(f"    num_collections = {measurement['num_collections']}.", flush=True)
    print(f"    lbc_deposits = {measurement['lbc_deposits']}.", flush=True)
    print(f"    lbc_supports = {measurement['lbc_supports']}.", flush=True)
    print(f"    num_supports = {measurement['num_supports']}.", flush=True)

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
    for key in measurement:
        if key[0:6] == "ytsync":
            print(f"    {key} = {measurement[key]}.", flush=True)

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
    print(f"    circulating_supply = {measurement['circulating_supply']}.",
          flush=True)

    # Measure number of claims over which LBC is spread (exp of shannon entropy)
    ps = []
    if k % 20 == 0:
        #cdb.execute("PRAGMA THREADS = 3;")
        cdb.execute("BEGIN;")
        for row in cdb.execute("SELECT (amount + support_amount) FROM claim;"):
            ps.append(row[0])
        cdb.execute("COMMIT;")
        ps = np.array(ps)
        ps = ps/ps.sum()
        measurement["lbc_spread"] = np.exp(-np.sum(ps*np.log(ps)))
    else:
        measurement["lbc_spread"] = None
    print(f"    lbc_spread = {measurement['lbc_spread']}.", flush=True)


    # Get number of purchases from chainquery
    measurement["purchases"] = None
    if k % 10 == 0:
        try:
            response = requests.get("http://chainquery.lbry.com/api/sql?query=" \
                                + "select count(*) as count from purchase;")
            measurement["purchases"] = response.json()["data"][0]["count"]
        except:
            pass
    print(f"    purchases = {measurement['purchases']}.", flush=True)

    # Get number of transactions
    measurement["transactions"] = None
    output = subprocess.run([config.lbrycrd_cli,
                    "getchaintxstats"],
                    capture_output=True).stdout.decode("utf8")
    data = json.loads(output)
    measurement["transactions"] = data["txcount"]
    print(f"    transactions = {measurement['transactions']}.", flush=True)


    # Get number of lbrycrd nodes
    nodes = None
    if (k + 5) % 10 == 0:
        nodes = lbrycrd_nodes()
    measurement["lbrycrd_nodes"] = nodes
    print(f"    lbrycrd_nodes = {nodes}.", flush=True)


    # Open output DB and write to it
    lbrynomics_db = apsw.Connection("db/lbrynomics.db")
    query = """
            INSERT INTO measurements (time, num_streams, num_channels, num_reposts,
                                      lbc_deposits, lbc_supports, num_supports,
                                      collections,
                                      ytsync_new_pending, ytsync_pending_update,
                                      ytsync_pending_upgrade, ytsync_failed,
                                      circulating_supply, lbc_spread, purchases,
                                      transactions, lbrycrd_nodes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """
    ldb.execute("BEGIN;")
    ldb.execute(query, tuple(measurement.values()))
    ldb.execute("COMMIT;")

    cdb_conn.close()


    # Do trending tags
    if (k + 5)%10 == 0:
        print("    ", end="")
        for mode in ["day", "week", "month", "year"]:
            hot_tags.run(mode)

    seconds = int(time.time() - now)
    print(f"Measurement completed in {seconds} seconds.\n", flush=True)
    return measurement

