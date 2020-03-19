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
         FOREIGN KEY (epoch) REFERENCES epochs (id));

    -- Create epochs channel
    CREATE TABLE IF NOT EXISTS epochs
        (id       INTEGER PRIMARY KEY,
         time     REAL NOT NULL);

    -- Channel properties (e.g., manual mature, greylist)
    CREATE TABLE IF NOT EXISTS special_channels
        (claim_id STRING PRIMARY KEY,
         is_nsfw INTEGER NOT NULL DEFAULT 0,
         grey  INTEGER NOT NULL DEFAULT 0,
         lbryf INTEGER NOT NULL DEFAULT 0,
         inc   INTEGER NOT NULL DEFAULT 0,
         black INTEGER NOT NULL DEFAULT 0) WITHOUT ROWID;
    """)

    # Create indices
    dbs["lbrynomics"].execute("""
    CREATE INDEX IF NOT EXISTS time_idx ON measurements (time);
    CREATE INDEX IF NOT EXISTS channel_idx ON channel_measurements (claim_id, epoch);
    CREATE INDEX IF NOT EXISTS claim_id_idx ON special_channels (claim_id);
    CREATE INDEX IF NOT EXISTS epoch_idx ON channel_measurements (epoch);
    CREATE INDEX IF NOT EXISTS black_list_idx ON special_channels (black);
    """)


   #  Special treatment for some claims

   #  LBRY Inc channels
    inc = set(["f3da2196b5151570d980b34d311ee0973225a68e",
               "70b8a88fc6e5ce9e4d6e8721536688484ecd79f4",
               "3fda836a92faaceedfe398225fb9b2ee2ed1f01a",
               "e48d2b50501159034f68d53321f67b8aa5b1d771",
               "e8fed337dc4ee260f4bcfa6d24ae1e4dd75c2fb3",
               "4c29f8b013adea4d5cca1861fb2161d5089613ea"])

    # LBRY Foundation Channels
    lbryf = set(["5bd299a92e7b31865d2bb3e2313402edaca41a94",
              "f8d6eccd887c9cebd36b1d42aa349279b7f5c3ed",
              "e11e2fc3056137948d2cc83fb5ca2ce9b57025ec",
              "1ba5acff747615510cf3f6089f54d5de669ad94f",
              "4506db7fb52d3ec5d3a024c870bf86fc35f7b6a3",
              "0f3a709eac3c531a68c97c7a48b2e37a532edb03",
              "36b7bd81c1f975878da8cfe2960ed819a1c85bb5",
              "e5f33f22ef656cb1595140409850a04d60aa474b",
              "631ca9fce459f1116ae5317486c7f4af69554742",
              "4caa1f92fb477caed1ce07cb7762a2249050a59c",
              "56e86eb938c0b93beccde0fbaaead65755139a10",
              "60ea26a907f25bcbbc8215007eef2bf0fb846f5c",
              "d0174cf90b6ec4e26ee2fc013714b0803dec5dd1",
              "3849a35ae6122e0b7a035c2ba66e97b9e4ab9efa",
              "c62ee910262e0a126181dc454b0556a174bfb120" ])

    # Channels to be promoted
    # promo = set()
    # promo = set([""])
    
    # Given mature tag by us
    manual_mature = set(["f24ab6f03d96aada87d4e14b2dac4aa1cee8d787",
                     "fd4b56c7216c2f96db4b751af68aa2789c327d48",
                     "ebe983567c5b64970d5dff2fe78dd1573f0d7b61"])

    # Grey list (quietly disable link)
    grey_list = set(["ca8cfeb5b6660a0b8874593058178b7ce6af5fed",
                  "6c1119f18fd7a15fc7535fcb9eec3aa22af66b6b",
                  "3097b755d3b8731e6103cc8752cb1b6c79da3b85",
                  "11c2f6bb38f69a25dea3d0fbef67e2e3a83a1263",
                  "7acf8b2fcd212afa2877afe289309a20642880c4",
                  "b01a44af8b71c0c2001a78303f319ca960d341cf",
                  "bc89d67d9f4d0124c347fd2c4a04e1696e8ba8b1",
                  "14fcd92ad24c1f1bc50f6cbc1e972df79387d05c",
                  "977cd1c90eefe4c9831f5c93b2359202733a9c2e",
                  "b3c6591b2f64c843fa66edda91ceab91d452f94f",
                  "67c1ce0d5754490cfa573ca27f8473ba793d1842",
                  "1713b1a9d2fd4e68bf3ff179cba246d527f67d56"])

    # DMCA'd channels + rewards scammers (do not appear)
    # Also those who appear to be faking their following
    black_list = set([ "98c39de1c681139e43131e4b32c2a21272eef06e",
                    "9ced2a722e91f28e9d3aea9423d34e08fb11e3f4",
                    "d5557f4c61d6725f1a51141bbee43cdd2576e415",
                    "35100b76e32aeb2764d334186249fa1b90d6cd74",
                    "f2fe17fb1c62c22f8319c38d0018726928454112",
                    "17db8343914760ba509ed1f8c8e34dcc588614b7",
                    "06a31b83cd38723527861a1ca5349b0187f92193",
                    "9b7a749276c69f39a2d2d76ca4353c0d8f75217d",
                    "b1fa196661570de64ff92d031116a2985af6034c",
                    "4e5e34d0ab3cae6f379dad75afadb0c1f683d30f",
                    "86612188eea0bda3efc6d550a7ad9c96079facff",
                    "00aa9655c127cccb2602d069e1982e08e9f96636",
                    "4f2dba9827ae28a974fbc78f1b12e67b8e0a32c9",
                    "c133c44e9c6ee71177f571646d5b0000489e419f",
                    "eeb3c6452b240a9f6a17c06887547be54a90a4b9",
                    "f625ef83a3f34cac61b6b3bdef42be664fd827da",
                    "ed77d38da413377b8b3ee752675662369b7e0a49",
                    "481c95bd9865dc17770c277ae50f0cc306dfa8af",
                    "3c5aa133095f97bb44f13de7c85a2a4dd5b4fcbe",
                    "bd6abead1787fa94722bd7d064f847de76de5655",
                    "6114b2ce20b55c40506d4bd3f7d8f917b1c37a75",
                    "0c65674e28f2be555570c5a3be0c3ce2eda359d1",
                    "3395d03f379888ffa789f1fa45d6619c2037e3de",
                    "cd31c9ddea4ac4574df50a1f84ee86aa17910ea2",
                    "9d48c8ab0ad53c392d4d6052daf5f8a8e6b5a185",
                    "51fbdb73893c1b04a7d4c4465ffcd1138abc9e93",
                    "5183307ce562dad27367bdf94cdafde38756dca7",
                    "56dca125e775b2fe607d3d8d6c29e7ecfa3cbd96",
                    "a58926cb716c954bdab0187b455a63a2c592310e",
                    "aa83130864bf22c66934c1af36182c91219233aa",
                    "f3c1fda9bf1f54710b62ffe4b14be6990288d9ff",
                    "6291b3b53dde4160ce89067281300585bdf51905",
                    "eeef31480a14684a95898ecd3bcf3a5569e41a28",
                    "9530d1af1b9f9982149ecf5785f74695b96a1c32",
                    "8b8b3c8cd3e8364c37067b80bd5a20c09a0a0094",
                    "725189cd101ff372edbce1c05ef04346864d3254",
                    "35100b76e32aeb2764d334186249fa1b90d6cd74",
                    "47beabb163e02e10f99838ffc10ebc57f3f13938",
                    "e0bb55d4d6aec9886858df8f1289974e673309c7",
                    "242734793097302d33b6a316c9db8d17b4beb18e",
                    "71d3256c267ccc875df366258b9eff4766d6cb57",
                    "dee09cad16900936d6af97154a6510a09587ad42",
                    "357ce885e22f2a7bd426ac36224722d64fc90ce6",
                    "c3ab2407e295cd267ced06d1fad2ed09b8d5643e",
                    "37b96ce8ae7a5564174111573105ee7efe4cd2fc",
                    "2849e111e747ce5883d2409046fefa03029daaec",
                    "29531246ce976d00a41741555edae4028c668205" ])

    dbs["lbrynomics"].execute("BEGIN;")

    for claim_id in inc:
        dbs["lbrynomics"].execute("""INSERT INTO special_channels (claim_id, inc)
                    VALUES (?, 1)
                    ON CONFLICT (claim_id)
                    DO UPDATE SET inc=1;""", (claim_id, ))

    for claim_id in lbryf:
        dbs["lbrynomics"].execute("""INSERT INTO special_channels (claim_id, lbryf)
                    VALUES (?, 1)
                    ON CONFLICT (claim_id)
                    DO UPDATE SET lbryf=1;""", (claim_id, ))

    for claim_id in manual_mature:
        dbs["lbrynomics"].execute("""INSERT INTO special_channels (claim_id, is_nsfw)
                    VALUES (?, 1)
                    ON CONFLICT (claim_id)
                    DO UPDATE SET is_nsfw=1;""", (claim_id, ))

    for claim_id in grey_list:
        dbs["lbrynomics"].execute("""INSERT INTO special_channels (claim_id, grey)
                    VALUES (?, 1)
                    ON CONFLICT (claim_id)
                    DO UPDATE SET grey=1;""", (claim_id, ))


    for claim_id in black_list:
        dbs["lbrynomics"].execute("""INSERT INTO special_channels (claim_id, black)
                    VALUES (?, 1)
                    ON CONFLICT (claim_id)
                    DO UPDATE SET black=1;""", (claim_id, ))

    dbs["lbrynomics"].execute("COMMIT;")


    
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

