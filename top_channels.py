import apsw
import config
from daemon_command import daemon_command
from databases import dbs
import datetime
import json
import numpy as np
import requests
import time
import yaml


def channels_with_content():
    """
    Return a list of all channels with content.
    """
    print("    Finding channels with content...", end="", flush=True)
    result = []

    for row in dbs["claims"].execute("""
    select c2.claim_id claim_ids, count(*) num_claims
        from claim c1 inner join claim c2 on c2.claim_hash = c1.channel_hash
        group by c2.claim_hash
        having num_claims > 0;
    """):
        result.append(row[0])

    print("done. Found {k} channels.".format(k=len(result)))

    # Remove blacklisted channels
    print("    Removing blacklisted channels...", flush=True, end="")
    black_list = dbs["lbrynomics"].execute("SELECT claim_id FROM special_channels WHERE black=1;")
    black_list = black_list.fetchall()
    black_list = set([x[0] for x in black_list])
    result = [x for x in result if x not in black_list]

    print("done. {n} channels remain.".format(n=len(result)))
    return result


def estimate_revenue(channel_hash):
    block = daemon_command("status")["wallet"]["blocks"] - 7*576

    query = """
    SELECT
        SUM(support.amount)/1E8 tot
    FROM
        claim post
            INNER JOIN
        claim channel
            ON post.channel_hash = channel.claim_hash AND
            post.channel_hash = ?
        INNER JOIN
        support ON
            support.claim_hash = post.claim_hash AND
        support.height >= ? AND
        support.amount <= 500000000;
    """

    result = dbs["claims"].execute(query, (channel_hash, block))
    result = result.fetchone()[0]
    if result is None:
        result = 0.0
    return result


def get_view_counts(claim_ids, start, end):
    result = []

    # Elegantly handle end
    if end > len(claim_ids):
        end = len(claim_ids)

    # Get auth token
    f= open("secrets.yaml")
    auth_token = yaml.load(f, Loader=yaml.SafeLoader)["auth_token"]
    f.close()

    # Prepare the request to the LBRY API
    url = "https://api.lbry.com/file/view_count?auth_token=" +\
                auth_token + "&claim_id="
    for i in range(start, end):
        url += claim_ids[i]
        if i != end-1:
            url += ","

    # JSON response from API
    try:
        response = requests.get(url).json()
        for value in response["data"]:
            result.append(value)
    except:
        result.append(None)

    return result

def view_counts_channel(channel_hash):
    claim_ids = []
    for row in dbs["claims"].execute("SELECT claim_id FROM claim WHERE channel_hash = ?;",
                                     (channel_hash, )):
        claim_ids.append(row[0])

    counts = 0
    for i in range(len(claim_ids)//100 + 1):
        result = get_view_counts(claim_ids, 100*i, 100*(i+1))
        for x in result:
            if x is not None:
                counts += x
    return counts

def get_followers(channels, start, end):
    """
    Get follower numbers for channels[start:end]
    """
    result = []

    # Elegantly handle end
    if end > len(channels):
        end = len(channels)

    # Get auth token
    f= open("secrets.yaml")
    auth_token = yaml.load(f, Loader=yaml.SafeLoader)["auth_token"]
    f.close()

    # Prepare the request to the LBRY API
    url = "https://api.lbry.com/subscription/sub_count?auth_token=" +\
                auth_token + "&claim_id="
    for i in range(start, end):
        url += channels[i]
        if i != end-1:
            url += ","

    # JSON response from API
    try:
        response = requests.get(url).json()
        for value in response["data"]:
            result.append(value)
    except:
        result.append(None)

    return result


def time_since_last_epoch():
    """
    Get the number of seconds since the last epoch
    """
    last = dbs["lbrynomics"].execute("""
                     SELECT time FROM epochs
                     WHERE id = (SELECT MAX(id) FROM epochs);""").fetchone()[0]
    return time.time() - last


def check_and_run():
    """
    Check whether it's time to do the top channels table. If so, do it.
    """
    rows = dbs["lbrynomics"].execute("SELECT COUNT(*) AS rows FROM epochs;").fetchone()[0]

    if rows == 0:
        get_top()
    elif time_since_last_epoch() >= 12*3600.0 and datetime.datetime.utcnow().hour == 0:
        get_top()
    elif time_since_last_epoch() >= 25*3600:
        get_top()

    return


def get_top(n=250, publish=200):
    """
    Compute the top n channels
    """
    assert n >= publish

    print("Making top channels list.", flush=True)
    channels = channels_with_content()
    counts = []
    for i in range(len(channels)//100 + 1):
        counts += get_followers(channels, 100*i, 100*(i+1))
        print("    Got follower counts for {a}/{b} channels."\
                .format(a=len(counts), b=len(channels)), end="\r")
    print("")

    ii = np.argsort(counts)[::-1]
    channels = np.array(channels)[ii]
    counts = np.array(counts)[ii]

    # Put into a dict
    result = {"unix_time": time.time(),
              "ranks": [],
              "claim_ids": [],
              "vanity_names": [],
              "num_followers": [],#              "revenue": [],
              "views": []}

    for i in range(n):
        result["ranks"].append(i+1)
        result["claim_ids"].append(str(channels[i]))
        row = dbs["claims"].execute("SELECT claim_name, claim_hash FROM claim WHERE claim_id=?",
                         (str(channels[i]),)).fetchone()
        name, channel_hash = row
        result["vanity_names"].append(name)
        result["num_followers"].append(int(counts[i]))
        print(f"    Getting view counts for {name}.", end="", flush=True)
#        result["revenue"].append(estimate_revenue(channel_hash))
        result["views"].append(view_counts_channel(channel_hash))
        print("")
    print("done.")

    # Epoch number
    epoch = 1 + dbs["lbrynomics"].execute("SELECT COUNT(id) c FROM epochs").fetchone()[0]
    now = time.time()
    dbs["lbrynomics"].execute("INSERT INTO epochs VALUES (?, ?)", (epoch, now))

    dbs["lbrynomics"].execute("BEGIN;")
    for i in range(n):
        values = (result["claim_ids"][i],
                 result["vanity_names"][i],
                 epoch,
                 result["num_followers"][i],
                 result["ranks"][i], #                 result["revenue"][i],\
                 result["views"][i])
        dbs["lbrynomics"].execute("""
                  INSERT INTO channel_measurements
                      (claim_id, vanity_name, epoch, num_followers, rank, views)
                  VALUES (?, ?, ?, ?, ?, ?);
                  """, values)

    dbs["lbrynomics"].execute("COMMIT;")


    # Now create the JSON in the old format
    result["human_time_utc"] = str(datetime.datetime.utcfromtimestamp(int(now))) + " UTC"
    result["subscribers"] = result["num_followers"]
    del result["num_followers"]

    # Get change from 7 epochs ago
    old_epoch = dbs["lbrynomics"].execute("""
                          SELECT id, abs(id-(?-7)) difference FROM epochs
                          ORDER BY difference ASC LIMIT 1;
                          """, (epoch, )).fetchone()[0]
    result["change"] = []
    result["rank_change"] = []
    result["views_change"] = []
    result["is_nsfw"] = []
    result["lbryf"] = []
    result["inc"] = []
    result["grey"] = []

    for i in range(n):
        response = dbs["lbrynomics"].execute("""
                             SELECT num_followers, rank, views
                             FROM channel_measurements
                             WHERE claim_id = ? AND epoch = ?;
                             """, (result["claim_ids"][i], old_epoch)).fetchone()

        if response is None:
            response = [None, None, None]

        if response[0] is None:
            change = None
        else:
            change = result["subscribers"][i] - response[0]

        if response[1] is None:
            rank_change = None
        else:
            rank_change = response[1] - result["ranks"][i]

        if response[2] is None:
            views_change = None
        else:
            views_change = result["views"][i] - response[2]

        result["change"].append(change)
        result["rank_change"].append(rank_change)
        result["views_change"].append(views_change)

        result["is_nsfw"].append(False)
        result["grey"].append(False)
        result["lbryf"].append(False)
        result["inc"].append(False)

        # Check for NSFW and other flags
        response = dbs["lbrynomics"].execute("SELECT * FROM special_channels WHERE claim_id=?;",
                              (result["claim_ids"][i], ))
        for row in response:
            result["is_nsfw"][-1] = bool(row[1])
            result["grey"][-1] = bool(row[2])
            result["lbryf"][-1] = bool(row[3])
            result["inc"][-1] = bool(row[4])

        # Check for mature tags on protocol level
        query = """SELECT tag.tag FROM claim
                        INNER JOIN tag
                        ON tag.claim_hash = claim.claim_hash
                        WHERE claim_id = ?;"""
        for row in dbs["claims"].execute(query, (result["claim_ids"][i], )):
            if row[0].lower() in set(["mature", "porn", "xxx", "nsfw"]):
                result["is_nsfw"][i] = True
                break

    # Truncate dict to publish
    for key in result.keys():
        try:
            if len(result[key]) == n:
                result[key] = result[key][0:publish]
        except:
            pass

    # Save to file
    f = open("json/subscriber_counts.json", "w")
    import update_rss
    update_rss.update(result["human_time_utc"])
    f.write(json.dumps(result, indent=4))
    f.close()

    print("Done.\n")

    return result


#if __name__ == "__main__":
#    channel_hash = dbs["claims"].execute("SELECT claim_hash FROM claim WHERE claim_id='760da3ba3dd85830a843beaaed543a89b7a367e7';").fetchone()[0]

#    start = time.time()
#    print(view_counts_channel(channel_hash))
#    print(time.time() - start)

