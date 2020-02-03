import apsw
import config
import datetime
import json
import numpy as np
import pandas as pd
import requests
import time
import yaml


def channels_with_content():
    """
    Return a list of all channels with content.
    """
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



