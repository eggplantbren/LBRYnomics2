import collections
import config
import sqlite3
import time




def make_measurement():

    print("Making measurement...", end="", flush=True)

    # Get current timestamp
    now = time.time()

    # Connect to the wallet server DB and the output DB
    claims_db = sqlite3.connect(config.claims_db_file)

    # Measurement measurement
    measurement = collections.OrderedDict()
    measurement["time"] = now

    # Query claims.db to get some measurement info
    query = """
            SELECT COUNT(*), claim_type FROM claim
            GROUP BY claim_type
            HAVING claim_type = 1 OR claim_type = 2
            ORDER BY claim_type DESC; 
            """
    output = claims_db.cursor().execute(query)
    measurement["num_channels"] = output.fetchone()[0]
    measurement["num_streams"]  = output.fetchone()[0]

    # Query claims.db to get some measurement info
    query = """
            SELECT SUM(amount)/1E8 FROM claim;
            """
    output = claims_db.cursor().execute(query)
    measurement["lbc_deposits"] = output.fetchone()[0]


    # Query claims.db to get some measurement info
    query = """
            SELECT COUNT(*), SUM(amount)/1E8 FROM support;
            """
    output = claims_db.cursor().execute(query)
    row = output.fetchone()
    measurement["num_supports"], measurement["lbc_supports"] = row

    # Close claims.db
    claims_db.close()


    # Open output DB and write to it
    lbrynomics_db = sqlite3.connect("./lbrynomics.db")
    query = """
            INSERT INTO measurements (time, num_channels, num_streams,
                                      lbc_deposits, num_supports, lbc_supports)
            VALUES (?, ?, ?, ?, ?, ?);
            """
    lbrynomics_db.cursor().execute(query, tuple(measurement.values()))
    lbrynomics_db.cursor().execute("COMMIT;")
    lbrynomics_db.close()

    print("done.")
    return measurement


if __name__ == "__main__":
    measurement = make_measurement()
    print(measurement)

