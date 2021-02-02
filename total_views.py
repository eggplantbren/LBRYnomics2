import apsw
from config import claims_db_file
import requests
import time
import yaml



# Get auth token
f = open("secrets.yaml")
secrets = yaml.load(f, Loader=yaml.SafeLoader)
auth_token = secrets["auth_token"]
f.close()

BATCH_SIZE = 22500


def batch_views(claim_ids):

    url = "https://api.lbry.com/file/view_count"
    cids = ",".join(claim_ids)
    data = dict(claim_id=cids, auth_token=auth_token)
    response = requests.post(url, data=data, timeout=30)
    result = response.json()
    if result["success"]:
        views = result["data"]
    else:
        views = None
    return views


def do_measurement():

    cconn = apsw.Connection(claims_db_file,
                            flags=apsw.SQLITE_OPEN_READONLY)
    cdb = cconn.cursor()
    conn = apsw.Connection("db/total_views.db")
    db = conn.cursor()
    db.execute("PRAGMA SYNCHRONOUS = 0;")
    db.execute("PRAGMA JOURNAL_MODE = WAL;")
    db.execute("BEGIN;")
    db.execute("""CREATE TABLE IF NOT EXISTS measurements
    (id          INTEGER NOT NULL PRIMARY KEY,
     time        REAL NOT NULL,
     total_views INTEGER NOT NULL);""")
    db.execute("COMMIT;")

    now = time.time()
    cdb.execute("BEGIN;")
    total_views = 0
    num_claims = 0
    claim_ids = []
    for row in cdb.execute("""SELECT claim_id FROM claim
                              WHERE claim_type = 1;"""):
        claim_ids.append(row[0])

        if len(claim_ids) == BATCH_SIZE:
            num_claims += len(claim_ids)
            total_views += sum(batch_views(claim_ids))
            claim_ids = []
            print("\r", end="")
            print(num_claims, total_views)

    cdb.execute("COMMIT;")

    num_claims += len(claim_ids)
    total_views += sum(batch_views(claim_ids))
    claim_ids = []
    print("\r", end="")
    print(num_claims, total_views)
    db.execute("BEGIN;")
    db.execute("INSERT INTO measurements (time, total_views) VALUES (?, ?);",
               (now, total_views))
    db.execute("COMMIT;")

