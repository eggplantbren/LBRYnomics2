from databases import dbs
import json

def lbrynomics_meta():
    """
    Measure some things about LBRYnomics itself.
    """

    # The dictionary that will be populated
    result = {}

    # Alias
    db = dbs["lbrynomics"]

    # Make the measurements!
    result["num_historical_estimates"] = db.execute("""
        SELECT COUNT(id) FROM measurements WHERE lbc_deposits IS NULL;
        """).fetchone()[0]
    result["num_actual_measurements"] = db.execute("""
        SELECT count(id) FROM measurements WHERE lbc_deposits IS NOT NULL;
        """).fetchone()[0]
    result["num_daily_channel_measurements"] = db.execute("""
        SELECT count(id) FROM epochs;
        """).fetchone()[0]
    result["days_actively_measuring"] = db.execute("""
        select count(*) from (select cast(time/86400.0 as INTEGER) t, COUNT(lbc_deposits)
        c from measurements GROUP BY t HAVING c > 0);""").fetchone()[0]

    # Write to file
    f = open("json/lbrynomics.json", "w")
    f.write(json.dumps(result, indent=4))
    f.close()

    return result

