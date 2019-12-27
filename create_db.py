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
         num_channels INTEGER,
         num_streams INTEGER,
         lbc_deposits REAL,
         num_supports INTEGER,
         lbc_supports REAL);
    """)

    # Create table for imputed measurements from history
    c.execute("""
    CREATE TABLE IF NOT EXISTS history
        (id INTEGER PRIMARY KEY,
         time REAL NOT NULL,
         num_channels INTEGER,
         num_streams INTEGER);
    """)


    # Create indices
    c.execute("""
    CREATE INDEX IF NOT EXISTS time ON measurements (time);
    """)

    c.execute("""
    CREATE INDEX IF NOT EXISTS time ON history (time);
    """)

    conn.close()


    
def test_history():

    print("Generating approximate historical data...", end="", flush=True)

    # Connect to database file
    conn = sqlite3.connect("db/lbrynomics.db")
    c = conn.cursor()

    # Count rows in history table
    rows = c.execute("SELECT COUNT(*) FROM history;").fetchone()[0]
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

    # Make 1000 fake measurements
    start = min(min(ts_channels), min(ts_streams))
    now = time.time()
    dt = (now - start)/1000

    conn = sqlite3.connect("db/lbrynomics.db")
    c = conn.cursor()
    for i in range(1000):
        cutoff = start + i*dt
        c.execute("""INSERT INTO history (time, num_channels, num_streams)
                     VALUES (?, ?, ?);""", (cutoff,
                                            int(np.sum(ts_channels <= cutoff)),
                                            int(np.sum(ts_streams <= cutoff))))
    c.execute("COMMIT;")
    conn.close()
    print("done.")

