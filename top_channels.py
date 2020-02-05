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

    # Put into a dict
    result = {"unix_time": time.time(),
              "ranks": [],
              "claim_ids": [],
              "vanity_names": []}

    conn = apsw.Connection(config.claims_db_file)
    c = conn.cursor()
    for i in range(n):
        result["ranks"].append(i+1)
        result["claim_ids"].append(channels[i])
        name = c.execute("SELECT claim_name FROM claim WHERE claim_id=?",
                         (channels[i],)).fetchone()
        result["vanity_names"].append(name)

    conn.close()


#    -- Create channel measurements table
#    CREATE TABLE IF NOT EXISTS channel_measurements
#        (id INTEGER PRIMARY KEY,
#         claim_id STRING NOT NULL,
#         vanity_name STRING NOT NULL,
#         epoch INTEGER NOT NULL,
#         num_followers INTEGER NOT NULL,
#         rank INTEGER NOT NULL);

    # Open lbrynomics.db for writing
    conn = apsw.Connection("db/lbrynomics.db")
    c = conn.cursor()
    c.execute("BEGIN;")
    for i in range(n):
        a, b, c, d = result["claim_ids"][i],\
                     result["vanity_names"][i],\
                     result["num_followers"][i],\
                     result["ranks"][i]
                     
        c.execute("""
                  INSERT INTO channel_measurements
                      (claim_id, vanity_name, epoch, num_followers, rank)
                  VALUES (?, ?, ?, ?, ?)
                  SET 
                  """, (a, b, 1, c, d))

    c.execute("COMMIT;")
    conn.close()

    return result

