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

    # 
    result["num_historical_estimates"] = db.execute("""
        SELECT COUNT(id) FROM measurements WHERE lbc_deposits IS NULL;
        """).fetchone()[0]
#    result["num_actual_measurements"] = 
#    result["num_daily_channel_measurements"] = 

    # Write to file
    f = open("json/lbrynomics.json", "w")
    f.write(json.dumps(result, indent=4))
    f.close()

    return result

