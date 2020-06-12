import apsw
from databases import dbs
import numpy as np
import numpy.random as rng
import time
from top_channels import get_view_counts

VIEWS_THRESHOLD = 100
LBC_THRESHOLD = 0.99999
SLEEP = 10.0

conn = apsw.Connection("db/view_counter.db")
db = conn.cursor()
db.execute("PRAGMA JOURNAL_MODE=DELETE;")
db.execute("BEGIN;")
db.execute("""
CREATE TABLE IF NOT EXISTS views
    (id         INTEGER PRIMARY KEY,
     time       REAL NOT NULL,
     claim_hash BYTES NOT NULL,
     views      INTEGER NOT NULL);
""")
db.execute("""
CREATE INDEX IF NOT EXISTS time_idx ON views (time DESC);
""")
db.execute("""
CREATE INDEX IF NOT EXISTS claim_time_idx ON views (time DESC, claim_hash);
""")
db.execute("COMMIT;")


def do_100():

    now = time.time()

    # Get the range of rowids
    result = dbs["claims"].execute("SELECT MIN(rowid), MAX(rowid) FROM claim;")\
                                    .fetchall()[0]
    min_rowid, max_rowid = result

    # Put up to 100 claim hashes in here
    claim_hashes = set()
    while len(claim_hashes) < 100:
        rowid = min_rowid + rng.randint(max_rowid - min_rowid + 1)
        row = dbs["claims"].execute("""SELECT claim_hash, (amount+support_amount)/1E8 lbc FROM claim
                                       WHERE claim_type=1 AND rowid=?
                                       AND lbc >= ?;""",
                                    (rowid, LBC_THRESHOLD)).fetchone()
        if row is not None:
            claim_hashes.add(row[0])

    # Get the view counts and prepare to add to DB
    claim_hashes = list(claim_hashes)
    claim_ids = dbs["claims"].execute(f"""SELECT claim_id FROM claim WHERE claim_hash IN\
                                ({','.join('?' for _ in claim_hashes)});""",
                                       claim_hashes).fetchall()
    claim_ids = [cid[0] for cid in claim_ids]
    views = get_view_counts(claim_ids, 0, len(claim_ids))
    zipped = []
    for i in range(len(views)):
        if views[i] >= VIEWS_THRESHOLD:
            zipped.append((now, claim_hashes[i], views[i]))

    db.execute("BEGIN;")
    db.executemany("""INSERT INTO views (time, claim_hash, views) VALUES (?, ?, ?);""",
                   zipped)
    db.execute("COMMIT;")

def claims_seen():
    return db.execute("SELECT COUNT(DISTINCT claim_hash) FROM views;").fetchone()[0]


k = 1
while True:
    print(f"Attempt {k}. Checking 100 streams...", end="", flush=True)
    try:
        do_100()
        c = claims_seen()
        print(f"done. Seen {c} with >= {VIEWS_THRESHOLD} views and >= {LBC_THRESHOLD} LBC.", flush=True)
    except:
        pass
    time.sleep(SLEEP)
    k += 1

conn.close()
