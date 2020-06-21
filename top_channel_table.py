import apsw
from databases import dbs

"""
A rewrite and simplification of the top channel table code.
It will run separately and have its own database.
"""

# Claims DB
cdb = dbs["claims"]

# Connection to top channel DB
conn = apsw.Connection("db/top_channels.db")
db = conn.cursor()

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
         views     INTEGER NOT NULL,
         followers INTEGER NOT NULL,
         reposts   INTEGER NOT NULL,
         lbc       REAL NOT NULL,
         FOREIGN KEY (channel) REFERENCES channels (claim_hash),
         FOREIGN KEY (epoch) REFERENCES epochs (id));
    """)
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


if __name__ == "__main__":
    create_tables()
    claim_id = "36b7bd81c1f975878da8cfe2960ed819a1c85bb5"
    claim_hash = bytes.fromhex(claim_id)[::-1]
    print(get_vanity_name(claim_hash))
    print(get_lbc(claim_hash))
    print(get_reposts(claim_hash))
    print(get_nsfw(claim_hash))

