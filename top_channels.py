import apsw
import config
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
    print("Finding channels with content...", end="", flush=True)
    result = []

    # Open claims.db
    conn = apsw.Connection(config.claims_db_file)
    c = conn.cursor()
    for row in c.execute("""
    select c2.claim_id claim_ids, count(*) num_claims
        from claim c1 inner join claim c2 on c2.claim_hash = c1.channel_hash
        group by c2.claim_hash
        having num_claims > 0;
    """):
        result.append(row[0])

    conn.close()
    print("done. Found {k} channels.".format(k=len(result)))

    # Remove blacklisted channels
    print("Removing blacklisted channels...", flush=True, end="")
    conn = apsw.Connection("db/lbrynomics.db")
    c = conn.cursor()
    black_list = c.execute("SELECT claim_id FROM special_channels WHERE black=1;")
    black_list = black_list.fetchall()
    black_list = set([x[0] for x in black_list])
    conn.close()
    result = [x for x in result if x not in black_list]

    print("done. {n} channels remain.".format(n=len(result)))
    return result


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
    response = requests.get(url).json()
    for value in response["data"]:
        result.append(value)

    return result


def time_since_last_epoch():
    """
    Get the number of seconds since the last epoch
    """
    conn = apsw.Connection("db/lbrynomics.db")
    c = conn.cursor()

    last = c.execute("""
                     SELECT time FROM epochs
                     WHERE id = (SELECT MAX(id) FROM epochs);""").fetchone()[0]
    conn.close()
    return time.time() - last

def get_top(n=200):
    """
    Compute the top n=200
    """
    channels = channels_with_content()
    counts = []
    for i in range(len(channels)//100 + 1):
        counts += get_followers(channels, 100*i, 100*(i+1))
        if i > 0:
            print("                                               ", end="\r")
        print("Processed {a}/{b} channels."\
                .format(a=len(counts), b=len(channels)), end="")

    ii = np.argsort(counts)[::-1]
    channels = np.array(channels)[ii]
    counts = np.array(counts)[ii]

    # Put into a dict
    result = {"unix_time": time.time(),
              "ranks": [],
              "claim_ids": [],
              "vanity_names": [],
              "num_followers": []}

    conn = apsw.Connection(config.claims_db_file)
    c = conn.cursor()
    for i in range(n):
        result["ranks"].append(i+1)
        result["claim_ids"].append(str(channels[i]))
        name = c.execute("SELECT claim_name FROM claim WHERE claim_id=?",
                         (str(channels[i]),)).fetchone()[0]
        result["vanity_names"].append(name)
        result["num_followers"].append(int(counts[i]))

    conn.close()

    # Open lbrynomics.db for writing
    conn = apsw.Connection("db/lbrynomics.db")
    c = conn.cursor()

    # Epoch number
    epoch = 1 + c.execute("SELECT COUNT(id) c FROM epochs").fetchone()[0]
    c.execute("INSERT INTO epochs VALUES (?, ?)", (epoch, time.time()))

    c.execute("BEGIN;")
    for i in range(n):
        values = (result["claim_ids"][i],\
                 result["vanity_names"][i],\
                 epoch,
                 result["num_followers"][i],\
                 result["ranks"][i])
        c.execute("""
                  INSERT INTO channel_measurements
                      (claim_id, vanity_name, epoch, num_followers, rank)
                  VALUES (?, ?, ?, ?, ?);
                  """, values)

    c.execute("COMMIT;")
    conn.close()

    return result

