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



if __name__ == "__main__":
    create_tables()

