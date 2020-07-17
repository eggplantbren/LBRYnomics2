import apsw
from databases import dbs
import datetime
import json

# Read-only connection to top channels database
tcdb_conn = apsw.Connection("db/top_channels.db",
                            flags=apsw.SQLITE_OPEN_READONLY)
tcdb = tcdb_conn.cursor()

def lbrynomics_meta(now, uptime):
    """
    Measure some things about LBRYnomics itself.
    """

    # The dictionary that will be populated
    result = {}

    # Alias
    db = dbs["lbrynomics"]

    result["unix_time_last_measurement"] = now
    result["human_time_last_measurement"] = str(datetime.datetime.\
                                       utcfromtimestamp(int(now))) + " UTC"
    result["uptime_days_at_last_measurement"] = round(uptime, 4)
    result["active_measurements_in_db"] = db.execute("""
        SELECT count(id) FROM measurements WHERE lbc_deposits IS NOT NULL;
        """).fetchone()[0]
    result["days_with_active_measurements"] = db.execute("""
        select count(*) from (select cast(time/86400.0 as INTEGER) t, COUNT(lbc_deposits)
        c from measurements GROUP BY t HAVING c > 0);""").fetchone()[0]
    result["historical_estimates_in_db"] = db.execute("""
        SELECT COUNT(id) FROM measurements WHERE lbc_deposits IS NULL;
        """).fetchone()[0]
    result["top_channel_days_in_db"] = tcdb.execute("""
        SELECT count(id) FROM epochs;
        """).fetchone()[0]

    # Write to file
    f = open("json/lbrynomics.json", "w")
    f.write(json.dumps(result, indent=4))
    f.close()

    return result

