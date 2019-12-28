import config
import datetime
import json
import sqlite3
import time
import yaml


def subscriber_counts(preview=False):
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

    # Now get number of claims in each channel from chainquery
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
        include[i] = claim_ids[i] in claims_with_content

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

    # Put the top 100 into the dict
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

    grey_list = ["f24ab6f03d96aada87d4e14b2dac4aa1cee8d787",
                 "fd4b56c7216c2f96db4b751af68aa2789c327d48"]

    for i in range(100):
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
        if my_dict["claim_ids"][-1] in grey_list:
            my_dict["is_nsfw"][-1] = True
        else:         
            # Do SQL queries to see if there's a mature tag
            query = "SELECT tag.tag FROM claim INNER JOIN tag ON tag.claim_hash = claim.claim_hash WHERE claim_id = '"
            query += claim_ids[i] + "';"

            for row in c.execute(query):
                if row[0].lower() == "mature":
                    my_dict["is_nsfw"][-1] = True

    if preview:
        f = open("json/subscriber_counts_preview.txt", "w")
    else:
        f = open("subscriber_counts.json", "w")
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


    while True:
        gap = time.time() - t

        msg = "{d} days until next update.".format(d=(week - gap)/day)
        print(msg + "        ", end="\r", flush=True)
        time.sleep(1.0 - time.time()%1)

        if gap >= week:
            subscriber_counts()

            f = open("json/subscriber_counts.json")
            t = json.load(f)["unix_time"]
            f.close()


