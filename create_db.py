import config
import numpy as np
import sqlite3
import time


def create_db():

    # Connect to database file
    conn = sqlite3.connect("db/lbrynomics.db")
    c = conn.cursor()

    # Set pragmas
    c.execute("""
    PRAGMA journal_mode = WAL;
    """)

    # Create table for actual measurements
    c.execute("""
    CREATE TABLE IF NOT EXISTS measurements
        (id INTEGER PRIMARY KEY,
         time REAL NOT NULL,
         num_channels INTEGER NOT NULL,
         num_streams INTEGER NOT NULL,
         lbc_deposits REAL,
         num_supports INTEGER,
         lbc_supports REAL);
    """)

    # Create indices
    c.execute("""
    CREATE INDEX IF NOT EXISTS time ON measurements (time);
    """)

    conn.close()


    
def test_history():
    """
    See whether the history table is populated. If not, populate it.
    Not the fastest ever method but this shouldn't really be needed very
    much.
    """

    print("Generating approximate historical data...", end="", flush=True)

    # Connect to database file
    conn = sqlite3.connect("db/lbrynomics.db")
    c = conn.cursor()

    # Count rows of history in table
    rows = c.execute("""SELECT COUNT(*) FROM measurements
                        WHERE lbc_deposits IS NULL;""").fetchone()[0]
    if rows > 0:
        # No need to do anything if history exists
        conn.close()
        print("done.")
        return

    # Estimate history
    conn = sqlite3.connect(config.claims_db_file)
    c = conn.cursor()

    # Obtain creation times from claims.db
    ts_channels = []
    ts_streams  = []
    for row in c.execute("SELECT creation_timestamp, claim_type FROM claim;"):
        if row[1] == 2:
            ts_channels.append(row[0])
        elif row[1] == 1:
            ts_streams.append(row[0])
    conn.close()

    # Sort times
    ts_channels = np.sort(np.array(ts_channels))
    ts_streams = np.sort(np.array(ts_streams))

    # Make fake measurements
    start = min(min(ts_channels), min(ts_streams)) - 0.5
    now = time.time()

    conn = sqlite3.connect("db/lbrynomics.db")
    c = conn.cursor()
    t = start
    rows = 0
    while True:
        c.execute("""INSERT INTO measurements (time, num_channels, num_streams)
                     VALUES (?, ?, ?);""", (t,
                                            int(np.sum(ts_channels <= t)),
                                            int(np.sum(ts_streams <= t))))
        t += config.interval
        rows += 1
        print("\r", end="")
        print("Generating approximate historical data...", end="")
        print("Inserted {rows} rows.".format(rows=rows), end="\r", flush=True)
        if t > now:
            break

    c.execute("COMMIT;")
    conn.close()
    print("done.")

