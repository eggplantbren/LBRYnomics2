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

