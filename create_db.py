import config
import numpy as np
import apsw
import time



def create_db():

    ldb_conn = apsw.Connection("db/lbrynomics.db")
    ldb = ldb_conn.cursor()

    cdb_conn = apsw.Connection(config.claims_db_file)
    cdb = cdb_conn.cursor()

    # Set pragmas
    ldb.execute("""
    PRAGMA synchronous = 0;
    PRAGMA journal_mode = WAL;
    """)

    # Add indices to claims.db
    cdb.execute("""create index if not exists lbrynomics_cti_idx
                on claim (claim_type, creation_timestamp);""")
    cdb.execute("""create index if not exists lbrynomics_test
                on claim (claim_type, channel_hash, claim_id)""")
    cdb.execute("""create index if not exists lbrynomics_height_amount_idx
                on support (height, amount);""")
    cdb.execute("""create index if not exists lbrynomics_amount_height_idx
                on support (amount, height);""")

    # Create tables for measurements etc.
    ldb.execute("""
    CREATE TABLE IF NOT EXISTS measurements
        (id INTEGER PRIMARY KEY,
         time REAL NOT NULL,
         num_channels INTEGER NOT NULL,
         num_streams INTEGER NOT NULL,
         lbc_deposits REAL,
         num_supports INTEGER,
         lbc_supports REAL,
         ytsync_new_pending INGEGER,
         ytsync_pending_update INTEGER,
         ytsync_pending_upgrade INTEGER,
         ytsync_failed INTEGER,
         circulating_supply REAL,
         num_reposts INTEGER,
         lbc_spread REAL);
    """)

    # Create indices
    ldb.execute("""
    CREATE INDEX IF NOT EXISTS time_idx ON measurements (time);
    """)

    ldb_conn.close()
    cdb_conn.close()
    
def test_history():
    """
    See whether the history table is populated. If not, populate it.
    Not the fastest ever method but this shouldn't really be needed very
    much.
    """

    ldb_conn = apsw.Connection("db/lbrynomics.db")
    ldb = ldb_conn.cursor()

    cdb_conn = apsw.Connection(config.claims_db_file,
                              flags=apsw.SQLITE_OPEN_READONLY)
    cdb = cdb_conn.cursor()

    print("Generating approximate historical data.", flush=True)

    # Count rows of history in table
    rows = ldb.execute("""SELECT COUNT(*) FROM measurements
                        WHERE lbc_deposits IS NULL;""").fetchone()[0]
    if rows > 0:
        # No need to do anything if history exists
        ldb_conn.close()
        cdb_conn.close()
        print("Done.\n")
        return

    # Obtain creation times from claims.db
    ts_channels = []
    ts_streams  = []
    for row in cdb.execute("SELECT creation_timestamp, claim_type FROM claim;"):
        if row[1] == 2:
            ts_channels.append(row[0])
        elif row[1] == 1:
            ts_streams.append(row[0])

    # Sort times
    ts_channels = np.sort(np.array(ts_channels))
    ts_streams = np.sort(np.array(ts_streams))

    # Make fake measurements
    start = min(min(ts_channels), min(ts_streams)) - 0.5
    now = time.time()
    num = int((now - start)/config.interval)
    counts = np.zeros((2, num))
    n = 0
    for t in ts_channels:
        k = int((t - start)/config.interval)
        if k < num:
            counts[0, k] += 1
        n += 1
        print("    Processed {n} claims.".format(n=n), end="\r", flush=True)

    for t in ts_streams:
        k = int((t - start)/config.interval)
        if k < num:
            counts[1, k] += 1
        n += 1
        print("    Processed {n} claims.".format(n=n), end="\r", flush=True)
    print("")

    counts = np.cumsum(counts, axis=1)

    ldb.execute("BEGIN;")

    for i in range(counts.shape[1]):
        t = start + i*config.interval
        ldb.execute("""INSERT INTO measurements (time, num_channels, num_streams)
                     VALUES (?, ?, ?);""", (t, counts[0, i], counts[1, i]))
        print("    Inserted {rows} rows into database."\
                    .format(rows=i+1), end="\r", flush=True)
    print("")

    ldb.execute("COMMIT;")

    ldb_conn.close()
    cdb_conn.close()

    print("Done.\n")

