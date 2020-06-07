import config
from databases import dbs
import numpy as np
import apsw
import time


def create_db():

    # Set pragmas
    dbs["lbrynomics"].execute("""
    PRAGMA synchronous = 1;
    PRAGMA journal_mode = WAL;
    """)

    # Add indices to claims.db
    dbs["claims"].execute("""create index if not exists lbrynomics_cti_idx
                on claim (claim_type, creation_timestamp);""")

    # Add indices to claims.db
    dbs["claims"].execute("""create index if not exists lbrynomics_sh_idx
                on support (height);""")
    dbs["claims"].execute("""create index if not exists lbrynomics_test
                on claim (claim_type, channel_hash, claim_id)""")
    dbs["claims"].execute("""create index if not exists lbrynomics_height_amount_idx
                on support (height, amount);""")

    # Create tables for measurements etc.
    dbs["lbrynomics"].execute("""
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
         num_reposts INTEGER);

    -- Create channel measurements table
    CREATE TABLE IF NOT EXISTS channel_measurements
        (id INTEGER PRIMARY KEY,
         claim_id STRING NOT NULL,
         vanity_name STRING NOT NULL,
         epoch INTEGER NOT NULL,
         num_followers INTEGER NOT NULL,
         rank INTEGER NOT NULL,
--         revenue REAL,
         views INTEGER,
         times_reposted INTEGER,
         lbc REAL,
         FOREIGN KEY (epoch) REFERENCES epochs (id));

    -- Create epochs channel
    CREATE TABLE IF NOT EXISTS epochs
        (id       INTEGER PRIMARY KEY,
         time     REAL NOT NULL);
    """)

    # Create indices
    dbs["lbrynomics"].execute("""
    CREATE INDEX IF NOT EXISTS time_idx ON measurements (time);
    CREATE INDEX IF NOT EXISTS channel_idx ON channel_measurements (claim_id, epoch);
    CREATE INDEX IF NOT EXISTS epoch_idx ON channel_measurements (epoch);
    """)


    
def test_history():
    """
    See whether the history table is populated. If not, populate it.
    Not the fastest ever method but this shouldn't really be needed very
    much.
    """

    print("Generating approximate historical data.", flush=True)

    # Count rows of history in table
    rows = dbs["lbrynomics"].execute("""SELECT COUNT(*) FROM measurements
                        WHERE lbc_deposits IS NULL;""").fetchone()[0]
    if rows > 0:
        # No need to do anything if history exists
        print("Done.\n")
        return

    # Obtain creation times from claims.db
    ts_channels = []
    ts_streams  = []
    for row in dbs["claims"].execute("SELECT creation_timestamp, claim_type FROM claim;"):
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

    dbs["lbrynomics"].execute("BEGIN;")

    for i in range(counts.shape[1]):
        t = start + i*config.interval
        dbs["lbrynomics"].execute("""INSERT INTO measurements (time, num_channels, num_streams)
                     VALUES (?, ?, ?);""", (t, counts[0, i], counts[1, i]))
        print("    Inserted {rows} rows into database."\
                    .format(rows=i+1), end="\r", flush=True)
    print("")

    dbs["lbrynomics"].execute("COMMIT;")
    print("Done.\n")

