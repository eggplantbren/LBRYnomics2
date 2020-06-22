import apsw
from databases import dbs
import lists

"""
A rewrite and simplification of the top channel table code.
It will run separately and have its own database.
"""

# Claims DB
cdb = dbs["claims"]

# LBRYnomics DB
lconn = apsw.Connection("db/lbrynomics.db", flags=apsw.SQLITE_OPEN_READONLY)
ldb = lconn.cursor()

# Connection to top channel DB
conn = apsw.Connection("db/top_channels.db")
db = conn.cursor()

# LBC threshold for auto-qualification
LBC_THRESHOLD = 20000.0


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
        (id   INTEGER PRIMARY KEY,
         time REAL NOT NULL);
    """)

    db.execute("""
    CREATE TABLE IF NOT EXISTS measurements
        (id        INTEGER PRIMARY KEY,
         channel   BYTES NOT NULL,
         epoch     INTEGER NOT NULL,
         views     INTEGER,
         followers INTEGER,
         reposts   INTEGER,
         lbc       REAL,
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
    for row in ldb.execute("""SELECT claim_id, epoch, num_followers, views,
                           times_reposted, lbc FROM channel_measurements;"""):
        channel = bytes.fromhex(row[0])[::-1]
        db.execute("""INSERT INTO measurements
                   (channel, epoch, views, followers, reposts, lbc)
                   VALUES (?, ?, ?, ?, ?, ?)
                   ON CONFLICT (channel, epoch) DO NOTHING;""",
                   (channel, row[1], row[3], row[2], row[4], row[5]))
    db.execute("COMMIT;")


def get_vanity_name(claim_hash):
    """
    Get the vanity name of a channel.
    """
    rows = cdb.execute("""SELECT claim_name FROM claim
                          WHERE claim_hash = ?;""", (claim_hash, )).fetchall()
    result = None
    if len(rows) == 1:
        result = rows[0][0]
    return result


def get_lbc(claim_hash):
    lbc = 0.0
    rows = cdb.execute("""SELECT (amount + support_amount) FROM claim
                          WHERE claim_hash = ?;""", (claim_hash, )).fetchall()
    if len(rows) == 1:
        lbc += rows[0][0]/1E8
    rows = cdb.execute("""SELECT SUM(amount + support_amount) FROM claim
                          WHERE channel_hash=?;""", (claim_hash, )).fetchall()
    if len(rows) == 1:
        lbc += rows[0][0]/1E8
    return lbc


def get_reposts(claim_hash):
    reposts = 0
    rows = cdb.execute("""SELECT SUM(reposted) FROM claim
                          WHERE channel_hash=?;""", (claim_hash, )).fetchall()
    if len(rows) == 1:
        reposts = rows[0][0]
    return reposts


def get_nsfw(claim_hash):
    nsfw = False
    rows = cdb.execute("""SELECT COUNT(*) FROM tag WHERE claim_hash = ?
                          AND tag.tag IN ('mature', 'xxx', 'sex', 'porn', 'nsfw');""",
                       (claim_hash, )).fetchall()
    if len(rows) > 0:
        nsfw = rows[0][0] > 0
    return nsfw

def qualifying_channels():
    """
    Return a set of all channels with either (i) at least one stream, or
    (ii) more than LBC_THRESHOLD staked ON THE CHANNEL CLAIM.
    """
    print("    Finding eligible channels...", end="", flush=True)

    # Convert claim_ids to claim_hashes
    black_list = set([bytes.fromhex(cid)[::-1] for cid in lists.black_list])

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
    print("done. Found {k} channels.".format(k=len(result)), flush=True)
    return result


if __name__ == "__main__":
    create_tables()
    import_from_ldb()

    qualifying_channels()
#    claim_id = "36b7bd81c1f975878da8cfe2960ed819a1c85bb5"
#    claim_hash = bytes.fromhex(claim_id)[::-1]
#    print(get_vanity_name(claim_hash))
#    print(get_lbc(claim_hash))
#    print(get_reposts(claim_hash))
#    print(get_nsfw(claim_hash))

