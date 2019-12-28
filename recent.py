import config
import datetime
import json
import sqlite3


def count_recent_all(now):
    print("Counting recent activity.", flush=True)
    count_recent("channels", now)
    count_recent("streams",  now)  # Gets called claims for ease for Electron
    print("done.\n")



def count_recent(mode, now):
    """
    Count recent things. Output JSON.
    """

    # Claim type
    if mode == "streams":
        mode = "claims" # Backwards compatibility

    if mode == "claims":
        claim_type = 1
    elif mode == "channels":
        claim_type = 2
        
    # Time cutoffs
    cutoffs = [0.0, now - 30*86400.0, now-7*86400.0, now-86400.0, now-3600.0]
    names = [None, "30_days", "7_days", "24_hours", "1_hour"]

    # Result dictionary
    result_dict = {}
    result_dict["unix_time"] = now
    result_dict["human_time_utc"] = str(datetime.datetime.\
                                       utcfromtimestamp(int(now))) + " UTC"

    # Connect to the wallet server
    conn = sqlite3.connect(config.claims_db_file)
    c = conn.cursor()

    for i in range(len(cutoffs)):
        query = """
                SELECT COUNT(*) FROM claim
                WHERE creation_timestamp >= ? AND creation_timestamp <= ?
                            AND claim_type = ?;
                """
        row = c.execute(query, (cutoffs[i], now, claim_type)).fetchone()
        if i==0:
            result_dict["total_{mode}".format(mode=mode)] = row[0]
        else:
            result_dict["new_{mode}_{name}".format(mode=mode, name=names[i])]\
                             = row[0]

    # Save some stats to JSON for Electron
    filename = "json/{mode}_stats.json".format(mode=mode)
    f = open(filename.format(mode=mode), "w")
    f.write(json.dumps(result_dict, indent=4))
    f.close()
    conn.close()
    print("    Saved {filename}.".format(filename=filename), flush=True)

