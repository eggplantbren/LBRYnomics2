import apsw
import config
import datetime
from daemon_command import daemon_command
import json
import math
import requests

def count_recent_all(now):
    print("Counting recent activity.", flush=True)
    count_recent("channels", now)
    count_recent("streams",  now)
    count_recent("reposts",  now)
    count_boosts(now)
    print("done.\n", flush=True)


def count_recent(mode, now):
    """
    Count recent things. Output JSON.
    """

    if mode == "streams":
        claim_type = 1
    elif mode == "channels":
        claim_type = 2
    elif mode == "reposts":
        claim_type = 3

    # Time cutoffs
    cutoffs = [0.0, now - 30*86400.0, now-7*86400.0, now-86400.0, now-3600.0]
    names = [None, "30_days", "7_days", "24_hours", "1_hour"]

    # Result dictionary
    result_dict = {}
    result_dict["unix_time"] = now
    result_dict["human_time_utc"] = str(datetime.datetime.\
                                       utcfromtimestamp(int(now)))

    cdb_conn = apsw.Connection(config.claims_db_file,
                                flags=apsw.SQLITE_OPEN_READONLY)
    cdb = cdb_conn.cursor()

    for i in range(len(cutoffs)):
        query = """
                SELECT COUNT(*) FROM claim
                WHERE creation_timestamp >= ? AND creation_timestamp <= ?
                            AND claim_type = ?;
                """
        row = cdb.execute(query, (cutoffs[i], now, claim_type)).fetchone()
        if i==0:
            result_dict["total_{mode}".format(mode=mode)] = row[0]
        else:
            result_dict["new_{mode}_{name}".format(mode=mode, name=names[i])]\
                             = row[0]

    # When did today start?
    start_of_today = get_start_of_today(now)
    query = """
            SELECT COUNT(*) FROM claim
            WHERE creation_timestamp >= ?
            AND claim_type = ?;
            """
    new_today = cdb.execute(query, (start_of_today, claim_type)).fetchone()[0]
    result_dict[f"new_{mode}_today_utc"] = new_today

    # Save some stats to JSON for Electron
    filename = f"json/{mode}_stats.json"
    f = open(filename.format(mode=mode), "w")
    f.write(json.dumps(result_dict, indent=4))
    f.close()

    print("    Saved {filename}. {new} so far this UTC day."\
		.format(new=new_today, filename=filename), flush=True)

    cdb_conn.close()


def get_start_of_today(now):
    """
    Returns unix epoch of the start of the day, based on input 'now'
    """
    start_of_today = datetime.datetime.fromtimestamp(now, datetime.timezone.utc)\
                        .replace(hour=0, minute=0, second=0, microsecond=0)
    start_of_today = start_of_today.timestamp()
    return start_of_today


def count_boosts(now):
    """
    Calculate tips and supports over past X amount of time and write JSON output
    """
    labels = ["all_time", "30_days", "7_days", "24_hours", "1_hour"]
    windows = [None, 30*86400.0, 7*86400.0, 1*86400.0, 3600.0]
    result = {}
    result["unix_time"] = now
    result["human_time_utc"] =\
                    str(datetime.datetime.utcfromtimestamp(int(now)))
    block = daemon_command("status")["wallet"]["blocks"]

    # Save next trending block
    """
    blocks = {}
    blocks["current"] = block
    blocks["next_trending_cycle"] = (int(block / 134) + 1)*134
    filename = "json/blocks.json"
    f = open(filename, "w")
    f.write(json.dumps(blocks, indent=4))
    f.close()
    print("    Saved {filename}.".format(filename=filename), flush=True)
    """

    cdb_conn = apsw.Connection(config.claims_db_file,
                                    flags=apsw.SQLITE_OPEN_READONLY)
    cdb = cdb_conn.cursor()

    for i in range(len(labels)):
        if i==0:
            cutoff = 0.0
        else:
            cutoff = block - windows[i]/(2.5*60)

        # Count and aggregate tips and supports for the time window
        query = """
                SELECT
                    COUNT(amount) num,
                    MAX(amount) max
                FROM
                    support
                """
        data = ()

        if i > 0:
            query += "WHERE height >= ?"
            data += (cutoff, )



        for row in cdb.execute(query, data):
            biggest = row[1]
            if biggest is None:
                biggest = 0.0
            result["num_{label}".format(label=labels[i])] = row[0]
            result["biggest_{label}".format(label=labels[i])] = biggest/1E8
            break


        # Count and aggregate tips and supports for the time window
        query = """
                SELECT amount, COUNT(*) AS num
                FROM support
                """
        data = ()
        if i > 0:
            query += "WHERE height >= ?\n"
            data += (cutoff, )

        query += """
                 GROUP BY amount
                 HAVING amount > 200000000
                 ORDER BY num DESC
                 LIMIT 1;
                 """
        for row in cdb.execute(query, data):
            val = None
            try:
                val = row[0]/1.0E8
            except:
                pass
            result["most_common_value_{label}".format(label=labels[i])] = val

        # Get claim name and ID for max
        query = """
                SELECT
                    claim_name, claim_id
                FROM
                    claim INNER JOIN support
                            ON claim.claim_hash = support.claim_hash
                WHERE
                    support.amount = ?
                """
        data = (biggest, )

        if i > 0:
            query += "AND support.height >= ?"
            data += (cutoff, )

        claim_name, claim_id = None, None
        for row in cdb.execute(query, data):
            claim_name, claim_id = row[0:2]
#        print(query, data, claim_name, claim_id)

        tv_url = None
        if claim_name is not None:
            tv_url = "https://odysee.com/" + claim_name + ":" + claim_id
        result["tv_url_{label}".format(label=labels[i])] = tv_url
#        print(tv_url)


        # Get title of max boosted claim and its channel
        title, channel_title = None, None
        try:
            payload = {"method": "claim_search",
                       "params": {"claim_ids": [claim_id]}}
            response = requests.post("http://localhost:5279", json=payload)
            r = response.json()["result"]
            title = r["items"][0]["value"]["title"]
            channel_title = r["items"][0]["signing_channel"]["value"]["title"]
        except:
            pass
        result[f"title_{labels[i]}"] = title
        result[f"channel_title_{labels[i]}"] = channel_title

        # Get NSFW status of max boosted claim
        query = """
                SELECT
                    COUNT(claim_id)
                FROM
                    claim INNER JOIN tag ON claim.claim_hash = tag.claim_hash
                    INNER JOIN support ON support.claim_hash = claim.claim_hash
                WHERE ((tag.tag = "mature" OR tag.tag = "nsfw" OR
                       tag.tag = "porn" OR tag.tag = "xxx")
                      AND support.amount = ?)
                """
        data = (biggest, )

        if i > 0:
            query += "AND support.height >= ?"
            data += (cutoff, )

        for row in cdb.execute(query, data):
            result["is_nsfw_{label}".format(label=labels[i])] = row[0] != 0
            break

    """
    # Use chainquery to get number of boosts today
    url = "https://chainquery.lbry.com/api/sql?query="
    url += "SELECT COUNT(id) FROM support WHERE UNIX_TIMESTAMP(created_at) >= "
    url += str(int(get_start_of_today(now))) + ";"
    response = requests.get(url)
    """

    filename = "json/supports_and_tips.json"
    f = open(filename, "w")
    f.write(json.dumps(result, indent=4))
    f.close()

    print(f"    Saved {filename}.", flush=True)

    cdb_conn.close()


