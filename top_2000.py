#!/usr/bin/env python

import apsw
from channel_measurement import *
import config
import datetime
import json
import lists
import numpy as np
import requests
from robust_post import get_counts
import sys
import time
import upload
import yaml

"""
A rewrite and simplification of the top channel table code.
It will run separately and have its own database.
"""

# LBRYnomics DB
lconn = apsw.Connection("db/lbrynomics.db", flags=apsw.SQLITE_OPEN_READONLY)
ldb = lconn.cursor()

# Connection to top channel DB
conn = apsw.Connection("db/top_channels.db")
db = conn.cursor()
db.execute("PRAGMA JOURNAL_MODE=WAL;")

# LBC threshold for auto-qualification
LBC_THRESHOLD = 10000.0

# Quality filter parameters
QUALITY_FILTER = [0.1, 0.5]

# Size of table to maintain in the database
TABLE_SIZE = 2050

# Size of the exported JSON
EXPORT_SIZE = 2000


def create_tables():
    """
    Create tables in the top channels database (if they don't already exit)
    """
    db.execute("BEGIN;")
    db.execute("""
    CREATE TABLE IF NOT EXISTS channels
        (claim_hash  BYTES PRIMARY KEY,
         vanity_name TEXT NOT NULL)
    WITHOUT ROWID;
    """)

    db.execute("""
    CREATE TABLE IF NOT EXISTS epochs
        (id   INTEGER NOT NULL PRIMARY KEY,
         time REAL NOT NULL);
    """)

    db.execute("""
    CREATE TABLE IF NOT EXISTS measurements
        (id        INTEGER NOT NULL PRIMARY KEY,
         channel   BYTES NOT NULL,
         epoch     INTEGER NOT NULL,
         rank      INTEGER,
         followers INTEGER,
         views     INTEGER,
         reposts   INTEGER,
         lbc       REAL,
         likes     INTEGER,
         dislikes  INTEGER,
         FOREIGN KEY (channel) REFERENCES channels (claim_hash),
         FOREIGN KEY (epoch) REFERENCES epochs (id),
         UNIQUE (channel, epoch));
    """)

    db.execute("""
    CREATE INDEX IF NOT EXISTS epoch_idx ON measurements (epoch);
    """)

    db.execute("""
    CREATE INDEX IF NOT EXISTS channel_idx ON measurements (channel, epoch);
    """)
    db.execute("COMMIT;")


def import_from_ldb():
    """
    Copy epochs and measurements from the old database to the new one.
    """
    db.execute("BEGIN;")

    # Import epochs
    for row in ldb.execute("SELECT * FROM epochs;"):
        db.execute("""INSERT INTO epochs VALUES (?, ?)
                      ON CONFLICT (id) DO NOTHING;""", row)

    # Import channels and vanity names
    for row in ldb.execute("""SELECT claim_id, vanity_name
                              FROM channel_measurements;"""):
        claim_hash = bytes.fromhex(row[0])[::-1]
        vanity_name = row[1]
        db.execute("""INSERT INTO channels VALUES (?, ?)
                      ON CONFLICT (claim_hash) DO NOTHING;""",
                   (claim_hash, vanity_name))

    # Import measurements
    for row in ldb.execute("""SELECT claim_id, epoch, rank, num_followers, views,
                           times_reposted, lbc FROM channel_measurements;"""):
        channel = bytes.fromhex(row[0])[::-1]
        db.execute("""INSERT INTO measurements
                   (channel, epoch, rank, followers, views, reposts, lbc)
                   VALUES (?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT (channel, epoch) DO NOTHING;""",
                   (channel, row[1], row[2], row[3], row[4], row[5], row[6]))
    db.execute("COMMIT;")


def quality_filter(followers, views, lbc):
    if lbc >= LBC_THRESHOLD:
        return True
    if views/followers >= min(QUALITY_FILTER) and\
       lbc/followers >= max(QUALITY_FILTER):
        return True
    if views/followers >= max(QUALITY_FILTER) and\
       lbc/followers >= min(QUALITY_FILTER):
        return True
    return False


def get_lbc(claim_hash):
    lbc = 0.0

    # Claims DB
    cdb_conn = apsw.Connection(config.claims_db_file,
                              flags=apsw.SQLITE_OPEN_READONLY)
    cdb_conn.setbusytimeout(60000)
    cdb = cdb_conn.cursor()

    try:
        rows = cdb.execute("""SELECT (amount + support_amount) FROM claim
                              WHERE claim_hash = ?;""", (claim_hash, )).fetchall()
        if len(rows) == 1:
            lbc += rows[0][0]/1E8
        rows = cdb.execute("""SELECT SUM(amount + support_amount) FROM claim
                              WHERE channel_hash=?;""", (claim_hash, )).fetchall()
        if len(rows) == 1:
            lbc += rows[0][0]/1E8
    except:
        pass

    cdb_conn.close()

    return lbc


def get_reposts(claim_hash):

    # Claims DB
    cdb_conn = apsw.Connection(config.claims_db_file,
                              flags=apsw.SQLITE_OPEN_READONLY)
    cdb_conn.setbusytimeout(60000)
    cdb = cdb_conn.cursor()

    reposts = cdb.execute("""SELECT SUM(reposted) FROM claim
                             WHERE channel_hash=?;""",
                          (claim_hash, )).fetchone()[0]

    cdb_conn.close()

    if reposts is None:
        reposts = 0
    return reposts


def get_nsfw(claim_hash):
    manual_mature = [bytes.fromhex(claim_id)[::-1] for claim_id in lists.manual_mature]
    if claim_hash in manual_mature:
        return True

    # Claims DB
    cdb_conn = apsw.Connection(config.claims_db_file,
                              flags=apsw.SQLITE_OPEN_READONLY)
    cdb_conn.setbusytimeout(60000)
    cdb = cdb_conn.cursor()

    nsfw = False
    rows = cdb.execute("""SELECT COUNT(*) FROM tag WHERE claim_hash = ?
                          AND tag.tag IN ('mature', 'xxx', 'sex', 'porn', 'nsfw');""",
                       (claim_hash, )).fetchall()
    if len(rows) > 0:
        nsfw = rows[0][0] > 0

    cdb_conn.close()

    return nsfw


def qualifying_channels():
    """
    Return a list of all channels with either (i) at least one stream, or
    (ii) more than LBC_THRESHOLD staked ON THE CHANNEL CLAIM.
    """
    print("    Finding eligible channels...", end="", flush=True)

    # Convert claim_ids to claim_hashes
    black_list = set([bytes.fromhex(cid)[::-1] for cid in lists.black_list])

    # Claims DB
    cdb_conn = apsw.Connection(config.claims_db_file,
                              flags=apsw.SQLITE_OPEN_READONLY)
    cdb_conn.setbusytimeout(60000)
    cdb = cdb_conn.cursor()

    # LBC qualification
    result = set()
    for row in cdb.execute("""
        SELECT claim_hash
        FROM
            claim
        WHERE
            claim_type = 2 AND 1E-8*(amount + support_amount) >= ?;
        """, (LBC_THRESHOLD, )):
        if row[0] not in black_list:
            result.add(row[0])

    # Having streams qualification
    for row in cdb.execute("""
        SELECT c.claim_hash, COUNT(*) num_streams
        FROM
            claim c, claim s
        WHERE
            s.channel_hash = c.claim_hash AND
            s.claim_type = 1
        GROUP BY c.claim_hash
        HAVING num_streams >= 1;
        """):
        if row[0] not in black_list:
            result.add(row[0])
    cdb_conn.close()

    print("done. Found {k} channels.".format(k=len(result)), flush=True)
    return list(result)


def do_epoch(force=False):
    """
    Do one epoch of measurements, if the time is right.
    Returns True if it does anything, False if the time wasn't right.
    """
    rows = db.execute("SELECT id, time FROM epochs ORDER BY time DESC LIMIT 1;")\
                .fetchall()
    if len(rows) == 0:
        last_epoch = (0, 0.0)
    else:
        last_epoch = rows[0]

    # How much time has passed?
    now = time.time()
    gap = now - last_epoch[1]

    # Whether to do anything
    do = force or (datetime.datetime.utcnow().hour == 0 and \
                        gap >= 0.25*86400.0) \
               or (gap > 86400.0)
    if not do:
        return False

    # Print message
    print("Performing top channel measurements.", flush=True)

    # Save the epoch
    epoch_id = last_epoch[0] + 1
    db.execute("BEGIN;")
    db.execute("INSERT INTO epochs VALUES (?, ?);", (epoch_id, now))
    db.execute("COMMIT;")

    # Get channels
    channels = qualifying_channels()

    # Get the follower counts
    print("Getting follower counts: ", flush=True, end="")
    followers = get_counts([ch[::-1].hex() for ch in channels], "followers")
    print("done.", flush=True)

    # Sort in descending order by followers
    ii = np.argsort(followers)[::-1]
    channels, followers = np.array(channels)[ii], np.array(followers)[ii]

    # Put measurements into database, until 2000 have passed the quality filter
    passed = []
    rank = 1
    db.execute("BEGIN;")
    for i in range(len(channels)):

        # Get vanity name
        try:
            # Claims DB
            cdb_conn = apsw.Connection(config.claims_db_file,
                                      flags=apsw.SQLITE_OPEN_READONLY)
            cdb_conn.setbusytimeout(60000)
            cdb = cdb_conn.cursor()
            vanity_name = cdb.execute("SELECT claim_name FROM claim\
                                       WHERE claim_hash=?;", (channels[i], ))\
                                        .fetchone()[0]
            cdb_conn.close()
        except:
            vanity_name = "N/A"

        print(f"({i+1}) Getting view counts for channel {vanity_name}: ",
              end="", flush=True)

        # View counts etc.
        m = measure_channel(channels[i])
        views, likes, dislikes = m["total_views"], m["total_likes"], m["total_dislikes"]

        lbc = get_lbc(channels[i])
        passed.append(quality_filter(followers[i], views, lbc)\
                        or channels[i][::-1].hex() in lists.white_list)
        print(f"\nDone. Quality filter passed = {passed[-1]}.\n", flush=True)

        _rank = None
        if passed[-1]:
            _rank = rank

        row = (bytes(channels[i]), epoch_id, _rank, int(followers[i]), views,
               get_reposts(channels[i]), lbc, likes, dislikes)
        db.execute("""INSERT INTO channels VALUES (?, ?)
                        ON CONFLICT (claim_hash) DO NOTHING;""", (channels[i], vanity_name))
        db.execute("""INSERT INTO measurements
                   (channel, epoch, rank, followers, views, reposts, lbc,
                    likes, dislikes)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);""", row)
        if passed[-1]:
            rank += 1

        if rank > TABLE_SIZE:
            break

    db.execute("COMMIT;")


    export_json()
    db.execute("PRAGMA main.WAL_CHECKPOINT(TRUNCATE);")

    return True


def export_json():
    """
    Export the latest epoch as JSON for Electron.
    """

    now = time.time()

    result = dict()
    result["unix_time"] = now
    result["human_time_utc"] = str(datetime.datetime.utcfromtimestamp(int(now))) + " UTC"
    result["ranks"] = []
    result["claim_ids"] = []
    result["vanity_names"] = []
    result["views"] = []
    result["times_reposted"] = []
    result["lbc"] = []
    result["subscribers"] = []
    result["change"] = []
    result["rank_change"] = []
    result["views_change"] = []
    result["times_reposted_change"] = []
    result["is_nsfw"] = []
    result["grey"] = []
    result["new_type"] = []
    result["likes"] = []
    result["dislikes"] = []
    result["titles"] = []
    result["top_500"] = []

    latest_epoch = db.execute("""
                    SELECT id FROM epochs ORDER BY time DESC limit 1;""")\
                        .fetchone()[0]
    old_epoch = db.execute("""
                          SELECT id, abs(id-(?-7)) difference FROM epochs
                          ORDER BY difference ASC LIMIT 1;
                          """, (latest_epoch, )).fetchone()[0]

    rows = db.execute("""SELECT claim_hash, vanity_name, followers, views, reposts, lbc, likes, dislikes
                         FROM measurements INNER JOIN channels
                                ON channels.claim_hash = measurements.channel
                         WHERE epoch = ?
                         ORDER BY followers DESC;""",
                      (latest_epoch, )).fetchall()
    for row in rows:

        # Termination
        if len(result["ranks"]) >= EXPORT_SIZE:
            break

        claim_hash, vanity_name, followers, views, reposts, lbc, likes, dislikes = row
        passed = quality_filter(followers, views, lbc) or claim_hash[::-1].hex() in lists.white_list
        if passed:
            result["ranks"].append(len(result["ranks"]) + 1)
            result["claim_ids"].append(claim_hash[::-1].hex())
            result["vanity_names"].append(vanity_name[1:])
            result["views"].append(views)
            result["times_reposted"].append(reposts)
            result["lbc"].append(lbc)
            result["subscribers"].append(followers)
            result["likes"].append(likes)
            result["dislikes"].append(dislikes)
            result["new_type"].append(0)
            result["top_500"].append(result["ranks"][-1] <= 500)

            old = db.execute("""SELECT rank, followers, views, reposts
                                FROM measurements
                                WHERE channel = ? AND epoch = ?;""",
                            (claim_hash, old_epoch)).fetchall()
            if len(old) >= 1:
                old = old[0]
                rank = result["ranks"][-1]

                if old[1] is not None:
                    result["change"].append(followers - old[1])
                else:
                    result["change"].append(0)

                if old[0] is not None:
                    result["rank_change"].append(old[0] - rank)
                else:
                    result["rank_change"].append(0)

                if old[2] is not None:
                    result["views_change"].append(views - old[2])
                else:
                    result["views_change"].append(0)

                if old[3] is not None:
                    result["times_reposted_change"].append(reposts - old[3])
                else:
                    result["times_reposted_change"].append(0)

            else:
                result["change"].append(0)
                result["rank_change"].append(0)
                result["views_change"].append(0)
                result["times_reposted_change"].append(0)
                result["new_type"][-1] = "n2"



            # Fields for tags
            claim_id = claim_hash[::-1].hex()
            result["is_nsfw"].append(get_nsfw(claim_hash))
            result["grey"].append(claim_id in lists.grey_list)
            count = db.execute("SELECT COUNT(id) FROM measurements\
                                WHERE channel = ? AND rank <= ?;",
                                (claim_hash, EXPORT_SIZE))\
                                .fetchone()[0]
            if count == 1:
                result["new_type"][-1] = "n1"

    # Titles part. Initialise with Nones
    titles = [None for _ in range(EXPORT_SIZE)]

    # Map from claim id to index
    lookup = dict()
    urls = [] # List of unambiguous URLs
    for i in range(len(result["claim_ids"])):
        lookup[result["claim_ids"][i]] = i
        urls.append("@" + result["vanity_names"][i] + "#" + result["claim_ids"][i])

    # Paginated resolve
    response = requests.post("http://localhost:5279",
                             json={"method": "resolve",
                                   "params": {"urls": urls}})
    if response.status_code == 200:
        items = response.json()["result"]
        for key in items:
            item = items[key]
            claim_id = None
            title = None
            try:
                claim_id = item["claim_id"]
                title = item["value"]["title"]
            except:
                pass
            if claim_id is not None and title is not None:
                titles[lookup[claim_id]] = title
    else:
        print("Error getting titles.")
    result["titles"] = titles

    f = open("json/top_2000.json", "w")
    f.write(json.dumps(result))
    f.close()

    # Top 500
    small = dict()
    for key in result:
        small[key] = result[key]
        try:
            if len(small[key]) == EXPORT_SIZE:
                small[key] = small[key][0:500]
        except:
            pass
    f = open("json/top_500.json", "w")
    f.write(json.dumps(small))
    f.close()

if __name__ == "__main__":
    create_tables()

    k = 1
    while True:
        done = do_epoch()
        if done:
            import plotter2
            print("Making and uploading daily interactive graphs...",
                  flush=True, end="")
            plotter2.html_plot(mode="top")
            plotter2.html_plot(mode="random")
            upload.upload(html_plot=True)
            print("done.", flush=True)
        else:
            print(".", end="", flush=True)
            if k % 60 == 0:
                print("", flush=True)
        time.sleep(60.0)
        k = k + 1

