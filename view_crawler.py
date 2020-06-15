import apsw
from databases import dbs
import json
import numpy as np
import numpy.random as rng
import time
from top_channels import get_view_counts

VIEWS_THRESHOLD = 100
LBC_THRESHOLD = 0.0
SLEEP = 1.0

conn = apsw.Connection("db/view_crawler.db")
db = conn.cursor()


def initialise_database():
    db.execute("PRAGMA JOURNAL_MODE=WAL;")
    db.execute("BEGIN;")

    db.execute("""
        CREATE TABLE IF NOT EXISTS streams
            (claim_hash BYTES PRIMARY KEY,
             name       TEXT NOT NULL)
        WITHOUT ROWID;
                """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS stream_measurements
            (id INTEGER PRIMARY KEY,
             time   REAL NOT NULL,
             stream BYTES NOT NULL,
             views  INTEGER NOT NULL DEFAULT 0,
             lbc    REAL NOT NULL DEFAULT 0.0,
             FOREIGN KEY (stream) REFERENCES streams(claim_hash));
                """)
    db.execute("""CREATE TABLE IF NOT EXISTS metadata
            (id    INTEGER PRIMARY KEY,
             name  TEXT UNIQUE NOT NULL,
             value INTEGER);""")
    db.execute("""
                INSERT INTO metadata (name, value)
                VALUES ('lbry_api_calls', 0)
                ON CONFLICT (name) DO NOTHING;
               """)

    # An index. Could probably be improved.
    db.execute("""CREATE INDEX IF NOT EXISTS idx1 ON stream_measurements
                    (views DESC, stream);""")
    db.execute("COMMIT;")


def do_100():

    now = time.time()

    # Get the range of rowids
    result = dbs["claims"].execute("SELECT MIN(rowid), MAX(rowid) FROM claim;")\
                                    .fetchall()[0]
    min_rowid, max_rowid = result

    # Put up to 100 claim hashes in here
    measurements = dict()
    while len(measurements) < 100:
        rowid = min_rowid + rng.randint(max_rowid - min_rowid + 1)
        row = dbs["claims"].execute("""SELECT claim_hash,
                                       claim_name,
                                       (amount+support_amount)/1E8 lbc
                                       FROM claim
                                       WHERE claim_type=1 AND rowid=?
                                       AND lbc >= ?;""",
                                    (rowid, LBC_THRESHOLD)).fetchone()

        if row is not None:
            nsfw = dbs["claims"].execute("""SELECT COUNT(*) FROM tag
                                            WHERE claim_hash = ?
                                            AND tag in
                                            ('nsfw', 'xxx', 'sex',
                                             'porn', 'mature')""", (row[0], )
                                        ).fetchone()[0]
            if nsfw == 0:
                measurements[row[0]] = dict(name=row[1], lbc=row[2])

    # Get the view counts and prepare to add to DB
    claim_hashes = list(measurements.keys())
    claim_ids = [ch[::-1].hex() for ch in claim_hashes]
    views = get_view_counts(claim_ids, 0, len(claim_ids))

    # Rows to insert new streams and new measurements
    zipped0 = []
    zipped1 = []

    for i in range(len(views)):
        ch = claim_hashes[i]
        zipped0.append((ch, measurements[ch]["name"]))

        if views[i] >= VIEWS_THRESHOLD and \
                        measurements[ch]["lbc"] >= LBC_THRESHOLD:
            ch = claim_hashes[i]
            zipped1.append((now, ch, views[i], measurements[ch]["lbc"]))

    db.execute("BEGIN;")
    db.executemany("""INSERT INTO streams (claim_hash, name)
                      VALUES (?, ?)
                      ON CONFLICT (claim_hash) DO NOTHING;""", zipped0)
    db.executemany("""INSERT INTO stream_measurements (time, stream, views, lbc)
                      VALUES (?, ?, ?, ?);""", zipped1)
    db.execute("UPDATE metadata set value=value+1 WHERE name='lbry_api_calls';")
    db.execute("COMMIT;")

def status():

    # Preparing for when we'll want more status measurements
    result = dict()
    result["lbry_api_calls"] = db.execute("""SELECT value FROM metadata WHERE
                                              name='lbry_api_calls';""")\
                                            .fetchone()[0]
    result["streams_in_db"] = db.execute("""SELECT COUNT(claim_hash)
                                            FROM streams;""").fetchone()[0]
    result["measurements_in_db"] = db.execute("""SELECT COUNT(id)
                                                 FROM stream_measurements;""")\
                                                            .fetchone()[0]
    return result


def read_top(num=1000):
    k = 1
    result = []
    for row in db.execute("""SELECT s.claim_hash, s.name, MAX(sm.views) v
                             FROM streams s INNER JOIN stream_measurements sm
                                    ON s.claim_hash = sm.stream
                             GROUP BY s.claim_hash
                             ORDER BY v DESC LIMIT ?;""", (num, )):
        claim_id = row[0][::-1].hex()
        result.append(dict(rank=k, name=row[1], claim_id=claim_id,
                           tv_url="https://lbry.tv/" + row[1] + ":" + claim_id,
                           views=row[2]))
        k += 1
    return result

if __name__ == "__main__":
    initialise_database()

    k = 1
    while True:
        print(f"Checking 100 streams...", end="", flush=True)
        try:
            do_100()
            s = status()
            print(f"done.\n Status: {s}.\n\n", end="", flush=True)
        except:
            print("Something went wrong.\n\n", end="", flush=True)
        time.sleep(SLEEP)
        k += 1

        if k % 10 == 0:
            print("Saving JSON...", end="", flush=True)
            f = open("json/view_crawler.json", "w")
            json.dump(read_top(), f, indent=2)
            f.close()
            print("done.\n\n", end="", flush=True)

        if k % 1000 == 0:
            print("Vacuuming database...", end="", flush=True)
            db.execute("VACUUM;")
            print("done.\n\n", end="", flush=True)

