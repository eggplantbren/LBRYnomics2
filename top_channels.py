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
        print(len(counts))

    ii = np.argsort(counts)[::-1]
    channels = np.array(channels)[ii]

    # Put into a dict
    result = {"ranks": [],
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
    return result

