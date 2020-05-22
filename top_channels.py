import apsw
import config
from daemon_command import daemon_command
from databases import dbs
import datetime
import json
from lists import *
import numpy as np
import plotter2
import requests
import time
import upload
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
    result = [x for x in result if x not in black_list]

    print("done. {n} channels remain.".format(n=len(result)), flush=True)
    return result


def get_thumbnail_urls(claim_ids):
    """
    Get thumbnail URLs from claim IDs.
    """
    LBRY_RPC = "http://localhost:5279"
    response = requests.post(LBRY_RPC, json={"method": "claim_search",
                                             "params": {"claim_ids": claim_ids,
                                                        "page_size": 500}})
    result = []
    try:
        for item in response.json()["result"]["items"]:
            result.append(item["value"]["thumbnail"]["url"])
    except:
        result = None
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

    if start == end:
        print("Start equalled end!")

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
    for row in dbs["claims"].execute("SELECT claim_id FROM claim WHERE channel_hash = ? AND claim_type=1;",
                                     (channel_hash, )):
        claim_ids.append(row[0])

    counts = 0
    for i in range((len(claim_ids) - 1)//100 + 1):
        result = get_view_counts(claim_ids, 100*i, 100*(i+1))
        if sum([x is None for x in result]) != 0:
            raise ValueError("Error getting view counts.")
        counts += sum(result)
        #print(result, flush=True)
    return counts

def get_followers(channels, start, end):
    """
    Get follower numbers for channels[start:end]
    """
    result = []

    # Elegantly handle end
    if end > len(channels):
        end = len(channels)

    if start == end:
        print("Start equalled end!")

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
    attempts = 5
    while attempts > 0:
        try:
            response = requests.get(url).json()
            for value in response["data"]:
                result.append(value)
            break
        except:
            attempts -= 1

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
    for i in range((len(channels) - 1)//100 + 1):
        counts += get_followers(channels, 100*i, 100*(i+1))
        print("    Got follower counts for {a}/{b} channels."\
                .format(a=len(counts), b=len(channels)), end="\r", flush=True)
    print("")

    ii = np.argsort(counts)[::-1]
    channels = np.array(channels)[ii]
    counts = np.array(counts)[ii]
    passed = []

    # Vanity names and channel hashes from claim IDs
    vanity_names = []
    channel_hashes = []
    lbc = []
    views = []
    channels_truncated = []
    counts_truncated = []
    for i in range(len(channels)):
        result1 = dbs["claims"].execute("""
                SELECT claim_name, claim_hash, (amount + support_amount)/1E8
                FROM claim WHERE claim_id=?""", (channels[i], )).fetchone()

        # Add LBC amounts of claims to lbc
        result2 = dbs["claims"].execute("""SELECT SUM(amount)/1E8 + SUM(support_amount)/1E8
                FROM claim WHERE channel_hash = ?;""", (result1[1], )).fetchone()

        attempts = 5
        while attempts > 0:
            try:
                print("    Getting view counts for {name}. ".format(name=result1[0]),
                      end="", flush=True)
                v = view_counts_channel(result1[1])
                break
            except:
                attempts -= 1


        # Quality filter
        lbc_amount = result1[2] + result2[0]
        lbc_ratio = lbc_amount/counts[i]
        views_ratio = v/counts[i]
        passes = False

        if lbc_amount >= 20000.0:
            passes = True
        elif lbc_ratio >= 1.0:
            passes = views_ratio >= 0.25
        elif lbc_ratio >= 0.25:
            passes = views_ratio >= 1.0
        elif channels[i] in white_list:
            passes = True

        print(f"\n    (lbc_ratio, views_ratio) = {lbc_ratio, views_ratio}")

        if passes:
            print("    Passed quality filter.", flush=True)
            vanity_names.append(result1[0])
            channel_hashes.append(result1[1])
            lbc.append(lbc_amount)
            views.append(v)
            channels_truncated.append(channels[i])
            counts_truncated.append(counts[i])
        else:
            print("    Did not pass quality filter.", flush=True)
        print("")

        if len(vanity_names) >= n:
            break
    channels = channels_truncated
    counts = counts_truncated


    # Get repost counts for the channels
    query = """
    SELECT SUM(reposted) r
        FROM claim WHERE channel_hash = ?;
    """
    times_reposted = []
    for row in dbs["claims"].executemany(query,
                            [(ch, ) for ch in channel_hashes]):
        times_reposted.append(row[0])

    # Put into a dict
    result = {"unix_time": time.time(),
              "ranks": [],
              "claim_ids": [],
              "vanity_names": vanity_names,
              "num_followers": [],#              "revenue": [],
              "views": [],
              "times_reposted": times_reposted,
              "lbc": lbc}

    for i in range(n):
        result["ranks"].append(i+1)
        result["claim_ids"].append(str(channels[i]))
        result["num_followers"].append(int(counts[i]))
        result["views"].append(int(views[i]))
#        result["revenue"].append(estimate_revenue(channel_hash))
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
                 result["views"][i],
                 result["times_reposted"][i], result["lbc"][i])
        dbs["lbrynomics"].execute("""
                  INSERT INTO channel_measurements
                      (claim_id, vanity_name, epoch, num_followers, rank, views, times_reposted, lbc)
                  VALUES (?, ?, ?, ?, ?, ?, ?, ?);
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
    result["times_reposted_change"] = []

    result["is_nsfw"] = []
    result["lbryf"] = []
    result["inc"] = []
    result["grey"] = []
    result["lbrynomics"] = []

    for i in range(n):
        response = dbs["lbrynomics"].execute("""
                             SELECT num_followers, rank, views, times_reposted
                             FROM channel_measurements
                             WHERE claim_id = ? AND epoch = ?;
                             """, (result["claim_ids"][i], old_epoch)).fetchone()

        if response is None:
            response = [None, None, None, None]

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

        if response[3] is None:
            times_reposted_change = None
        else:
            times_reposted_change = result["times_reposted"][i] - response[3]

        result["change"].append(change)
        result["rank_change"].append(rank_change)
        result["views_change"].append(views_change)
        result["times_reposted_change"].append(times_reposted_change)

        result["is_nsfw"].append(result["claim_ids"][i] in manual_mature)
        result["grey"].append(result["claim_ids"][i] in grey_list)
        result["lbryf"].append(result["claim_ids"][i] in lbryf)
        result["inc"].append(result["claim_ids"][i] in inc)
        result["lbrynomics"].append(result["claim_ids"][i] in lbrynomics)

        # Check for mature tags on protocol level
        query = """SELECT tag.tag FROM claim
                        INNER JOIN tag
                        ON tag.claim_hash = claim.claim_hash
                        WHERE claim_id = ?;"""
        for row in dbs["claims"].execute(query, (result["claim_ids"][i], )):
            if row[0].lower() in set(["mature", "porn", "xxx", "nsfw"]):
                result["is_nsfw"][i] = True
                break

    # Create is_new field
    result["is_new"] = []
    for i in range(n):
        result["is_new"].append(result["change"][i] is None)

    # Truncate for publication, also replacing null values with 0
    for key in result.keys():
        try:
            if len(result[key]) == n:
                result[key] = result[key][0:publish]
                for i in range(len(result[key])):
                    if result[key][i] is None:
                        result[key][i] = 0
        except:
            pass

    # Get thumbnail URLs
    result["thumbnail_urls"] = get_thumbnail_urls(result["claim_ids"])

    # Save to file
    f = open("json/subscriber_counts.json", "w")
#    import update_rss
#    update_rss.update(result["human_time_utc"])
    f.write(json.dumps(result))
    f.close()

    print("Done.\n")

    print("Backing up DB file...", flush=True)
    upload.backup()
    print("done.\n", flush=True)

    print("Making and uploading daily interactive graph...", flush=True, end="")
    plotter2.html_plot()
    upload.upload(with_html_plot=True)
    print("done.", flush=True)

    return result


#if __name__ == "__main__":
#    channel_hash = dbs["claims"].execute("SELECT claim_hash FROM claim WHERE claim_id='760da3ba3dd85830a843beaaed543a89b7a367e7';").fetchone()[0]

#    start = time.time()
#    print(view_counts_channel(channel_hash))
#    print(time.time() - start)

