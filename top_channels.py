import config
import datetime
import json
import numpy as np
import pandas as pd
import requests
import sqlite3
import time
import yaml


# Special treatment for some claims

# LBRY Inc channels
inc = set(["f3da2196b5151570d980b34d311ee0973225a68e",
           "70b8a88fc6e5ce9e4d6e8721536688484ecd79f4",
           "3fda836a92faaceedfe398225fb9b2ee2ed1f01a",
           "e48d2b50501159034f68d53321f67b8aa5b1d771"])

# LBRY Social channels
ls = set(["5bd299a92e7b31865d2bb3e2313402edaca41a94",
          "f8d6eccd887c9cebd36b1d42aa349279b7f5c3ed",
          "e11e2fc3056137948d2cc83fb5ca2ce9b57025ec",
          "1ba5acff747615510cf3f6089f54d5de669ad94f",
          "4506db7fb52d3ec5d3a024c870bf86fc35f7b6a3",
          "f5cd68fc0d2edcde180bee2f6de48fc9cc5ee1f3",
          "4394924aa67c93d1f39b068bcfa044509cf19ec1",
          "36b7bd81c1f975878da8cfe2960ed819a1c85bb5",
          "ec0e86fc8fe55bd59f45ebe35f99515ef0949a38",
          "0956afbfbf7be2232dccf1dc01c4d89dae060220",
          "e5f33f22ef656cb1595140409850a04d60aa474b",
          "631ca9fce459f1116ae5317486c7f4af69554742",
          "c4dd78bcff002a2ae99e28c883a655f58e106423",
          "4caa1f92fb477caed1ce07cb7762a2249050a59c",
          "56e86eb938c0b93beccde0fbaaead65755139a10",
          "60ea26a907f25bcbbc8215007eef2bf0fb846f5c",
          "d0174cf90b6ec4e26ee2fc013714b0803dec5dd1",
          "3849a35ae6122e0b7a035c2ba66e97b9e4ab9efa" ])


# Given mature tag by us
manual_mature = set(["f24ab6f03d96aada87d4e14b2dac4aa1cee8d787",
                 "fd4b56c7216c2f96db4b751af68aa2789c327d48"])

# Grey list (quietly disable link)
grey_list = set(["ca8cfeb5b6660a0b8874593058178b7ce6af5fed",
              "6c1119f18fd7a15fc7535fcb9eec3aa22af66b6b",
              "3097b755d3b8731e6103cc8752cb1b6c79da3b85",
              "11c2f6bb38f69a25dea3d0fbef67e2e3a83a1263",
              "7acf8b2fcd212afa2877afe289309a20642880c4",
              "b01a44af8b71c0c2001a78303f319ca960d341cf",
              "bc89d67d9f4d0124c347fd2c4a04e1696e8ba8b1",
              "14fcd92ad24c1f1bc50f6cbc1e972df79387d05c" ])


# DMCA'd channels + rewards scammers (do not appear)
black_list = set([ "98c39de1c681139e43131e4b32c2a21272eef06e",
                "9ced2a722e91f28e9d3aea9423d34e08fb11e3f4",
                "d5557f4c61d6725f1a51141bbee43cdd2576e415",
                "35100b76e32aeb2764d334186249fa1b90d6cd74",
                "f2fe17fb1c62c22f8319c38d0018726928454112",
                "17db8343914760ba509ed1f8c8e34dcc588614b7",
                "06a31b83cd38723527861a1ca5349b0187f92193",
                "9b7a749276c69f39a2d2d76ca4353c0d8f75217d",
                "b1fa196661570de64ff92d031116a2985af6034c",
                "4e5e34d0ab3cae6f379dad75afadb0c1f683d30f",
                "86612188eea0bda3efc6d550a7ad9c96079facff",
                "00aa9655c127cccb2602d069e1982e08e9f96636",
                "4f2dba9827ae28a974fbc78f1b12e67b8e0a32c9",
                "c133c44e9c6ee71177f571646d5b0000489e419f",
                "eeb3c6452b240a9f6a17c06887547be54a90a4b9",
                "f625ef83a3f34cac61b6b3bdef42be664fd827da",
                "ed77d38da413377b8b3ee752675662369b7e0a49",
                "481c95bd9865dc17770c277ae50f0cc306dfa8af",
                "3c5aa133095f97bb44f13de7c85a2a4dd5b4fcbe",
                "bd6abead1787fa94722bd7d064f847de76de5655",
                "6114b2ce20b55c40506d4bd3f7d8f917b1c37a75",
                "0c65674e28f2be555570c5a3be0c3ce2eda359d1",
                "3395d03f379888ffa789f1fa45d6619c2037e3de",
                "cd31c9ddea4ac4574df50a1f84ee86aa17910ea2",
                "9d48c8ab0ad53c392d4d6052daf5f8a8e6b5a185",
                "51fbdb73893c1b04a7d4c4465ffcd1138abc9e93",
                "5183307ce562dad27367bdf94cdafde38756dca7",
                "56dca125e775b2fe607d3d8d6c29e7ecfa3cbd96",
                "a58926cb716c954bdab0187b455a63a2c592310e",
                "aa83130864bf22c66934c1af36182c91219233aa",
                "f3c1fda9bf1f54710b62ffe4b14be6990288d9ff",
                "6291b3b53dde4160ce89067281300585bdf51905",
                "eeef31480a14684a95898ecd3bcf3a5569e41a28",
                "8b8b3c8cd3e8364c37067b80bd5a20c09a0a0094",
                "725189cd101ff372edbce1c05ef04346864d3254",
                "35100b76e32aeb2764d334186249fa1b90d6cd74",
                "47beabb163e02e10f99838ffc10ebc57f3f13938",
                "e0bb55d4d6aec9886858df8f1289974e673309c7",
                "242734793097302d33b6a316c9db8d17b4beb18e",
                "71d3256c267ccc875df366258b9eff4766d6cb57",
                "dee09cad16900936d6af97154a6510a09587ad42",
                "357ce885e22f2a7bd426ac36224722d64fc90ce6",
                "c3ab2407e295cd267ced06d1fad2ed09b8d5643e" ])



def subscriber_counts(num=200, preview=False):
    """
    Get subscriber counts for all channels.
    """
    now = time.time()

    # Open previous JSON
    f = open("json/subscriber_counts.json")
    old = json.load(f)
    f.close()

    # Get auth token
    f= open("secrets.yaml")
    auth_token = yaml.load(f, Loader=yaml.SafeLoader)["auth_token"]
    f.close()

    # Create a dict from the old JSON, where the claim_id can return
    # the subscribers and the rank
    old_dict = {}
    for i in range(len(old["ranks"])):
        old_dict[old["claim_ids"][i]] = (old["subscribers"][i], old["ranks"][i])

    # Open claims.db
    conn = sqlite3.connect(config.claims_db_file)
    c = conn.cursor()
    query = "select claim_name, claim_id, claim_hash from claim where claim_type = 2;"
    vanity_names = []
    claim_ids = []
    subscribers = []

    # Iterate over query results
    i = 0
    for row in c.execute(query):
        vanity_names.append(row[0])
        claim_ids.append(row[1])
        i = i + 1

    vanity_names = np.array(vanity_names)
    claim_ids = np.array(claim_ids)

    # Now get number of claims in each channel
    query = \
"""
select c2.claim_id claim_ids, count(*) num_claims
    from claim c1 inner join claim c2 on c2.claim_hash = c1.channel_hash
    group by c2.claim_hash
    having num_claims > 0;
"""

    claims_with_content = {}
    k = 0
    for row in c.execute(query):
        claims_with_content[row[0]] = None
        k += 1
        print("Getting channels with content...found {k} so far.".format(k=k))

    start = time.time()


    include = np.zeros(len(claim_ids), dtype=bool)
    for i in range(len(claim_ids)):
        include[i] = (claim_ids[i] in claims_with_content) and \
                            claim_ids[i] not in black_list

    vanity_names = vanity_names[include]
    claim_ids = claim_ids[include]

    k = 0
    while True:
        """
        Go in batches of 100 with a pause in between
        """
        time.sleep(3.0)

        # Cover a certain range of channels
        start = 100*k
        end = 100*(k+1)
        final = end >= len(claim_ids)
        if final:
            end = len(claim_ids)

        
        # Attempt the request until it succeeds
        while True:

            # Prepare the request to the LBRY API
            url = "https://api.lbry.com/subscription/sub_count?auth_token=" +\
                        auth_token + "&claim_id="
            for i in range(start, end):
                url += claim_ids[i] + ","
            url = url[0:-1] # No final comma

            f = open("url.txt", "w")
            f.write(url)
            f.close()

            try:
                # Do the request
                result = requests.get(url)
                result = result.json()
                break
            except:
                time.sleep(3.0)
                pass

        # Get sub counts from the result and put them in the subscribers list
        for x in result["data"]:
            subscribers.append(x)
            i = len(subscribers)-1

        print("Processed {end} channels.".format(end=end))
        if final:
            break
        k += 1

    # Sort by number of subscribers then by vanity name.
    # Zip subs with name
    s_n = []
    indices = []
    for i in range(len(vanity_names)):
        s_n.append((subscribers[i], vanity_names[i]))
        indices.append(i)
    indices = sorted(indices, key=lambda x: (s_n[x][0], s_n[x][1]))[::-1]

    vanity_names = np.array(vanity_names)[indices]
    claim_ids = np.array(claim_ids)[indices]
    subscribers = np.array(subscribers)[indices]

    # Put the top 200 into the dict
    my_dict = {}
    my_dict["unix_time"] = now
    my_dict["human_time_utc"] = str(datetime.datetime.utcfromtimestamp(int(now))) + " UTC"
    my_dict["old_unix_time"] = old["unix_time"]
    my_dict["old_human_time_utc"] = old["human_time_utc"]
    my_dict["interval_days"] = np.round((my_dict["unix_time"]\
                                        - my_dict["old_unix_time"])/86400.0, 2)
    my_dict["ranks"] = []
    my_dict["vanity_names"] = []
    my_dict["claim_ids"] = []
    my_dict["subscribers"] = []
    my_dict["change"] = []
    my_dict["rank_change"] = []
    my_dict["is_nsfw"] = []
    my_dict["grey"] = []
    my_dict["ls"] = []
    my_dict["inc"] = []


    for i in range(num):
        my_dict["ranks"].append(i+1)
        my_dict["vanity_names"].append(vanity_names[i])
        my_dict["claim_ids"].append(claim_ids[i])
        my_dict["subscribers"].append(int(subscribers[i]))
        my_dict["is_nsfw"].append(False)

        # Compute subscribers change
        my_dict["change"].append(None)
        my_dict["rank_change"].append(None)
        try:
            my_dict["change"][-1] = int(subscribers[i]) - \
                                        old_dict[claim_ids[i]][0]
            my_dict["rank_change"][-1] = old_dict[claim_ids[i]][1] - \
                                            int(my_dict["ranks"][-1])
        except:
            pass

        # Mark some channels NSFW manually
        if my_dict["claim_ids"][-1] in manual_mature:
            my_dict["is_nsfw"][-1] = True
        else:         
            # Do SQL queries to see if there's a mature tag
            query = "SELECT tag.tag FROM claim INNER JOIN tag ON tag.claim_hash = claim.claim_hash WHERE claim_id = '"
            query += claim_ids[i] + "';"

            for row in c.execute(query):
                if row[0].lower() == "mature":
                    my_dict["is_nsfw"][-1] = True

        # Grey list
        my_dict["grey"].append(my_dict["claim_ids"][-1] in grey_list)

        # LS list
        my_dict["ls"].append(my_dict["claim_ids"][-1] in ls)
        my_dict["inc"].append(my_dict["claim_ids"][-1] in inc)

    if preview:
        f = open("json/subscriber_counts_preview.csv", "w")
        # Create data frame and make CSV
        df = pd.DataFrame()
        df["ranks"] = my_dict["ranks"]
        df["vanity_names"] = my_dict["vanity_names"]
        df["claim_ids"] = my_dict["claim_ids"]
        df["is_nsfw"] = my_dict["is_nsfw"]
        df["grey"] = my_dict["grey"]
        df["ls"] = my_dict["ls"]
        df["inc"] = my_dict["inc"]
        df["followers"] = my_dict["subscribers"]
        df["change"] = my_dict["change"]
        df["rank_change"] = my_dict["rank_change"]
        df.to_csv("json/subscriber_counts_preview.csv", index=False)


    else:
        f = open("json/subscriber_counts.json", "w")
        import update_rss
        update_rss.update(my_dict["human_time_utc"])
        f.write(json.dumps(my_dict, indent=4))
        f.close()

    conn.close()

# Main loop
if __name__ == "__main__":

    # Needs an initial JSON file to bootstrap from
    hour = 3600.0
    day = 24*hour
    week = 7*day


    f = open("json/subscriber_counts.json")
    t = json.load(f)["unix_time"]
    f.close()


    # Update frequency
    interval = 0.5*week


    while True:
        gap = time.time() - t

        msg = "{d} days until next update.".format(d=(interval - gap)/day)
        print(msg + "        ", end="\r", flush=True)
        time.sleep(1.0 - time.time()%1)

        if gap >= interval:
            subscriber_counts()

            f = open("json/subscriber_counts.json")
            t = json.load(f)["unix_time"]
            f.close()


