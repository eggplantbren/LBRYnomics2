import requests
import time
import yaml

BATCH_SIZE = 500

def get_counts(claim_ids, mode="views", batch_size=BATCH_SIZE):
    """
    Only used for follower mode now. For other quantities, use
    channel_measurement.py
    """

    assert mode in ["followers"]

    result = []

    # Get auth token
    f= open("secrets.yaml")
    auth_token = yaml.load(f, Loader=yaml.SafeLoader)["auth_token"]
    f.close()

    url = "https://api.odysee.com/"
    if mode == "views":
        url += "file/view_count"
    elif mode == "followers":
        url += "subscription/sub_count"
    elif mode == "likes_dislikes":
        url += "reaction/list"

    # Batch into groups of 1000
    cids = []
    num_batches = 1 + (len(claim_ids)-1) // batch_size
    batch_sizes = []
    for i in range(num_batches):
        start = i*batch_size
        end = (i+1)*batch_size
        if end > len(claim_ids):
            end = len(claim_ids)
        cids.append(",".join(claim_ids[start:end]))
        batch_sizes.append(end - start)

    # Run each batch
    if mode == "likes_dislikes":
        result = [[], []]
    else:
        result = []

    for i in range(num_batches):
        data = {"auth_token": auth_token}
        if mode == "likes_dislikes":
            data["claim_ids"] = cids[i]
        else:
            data["claim_id"] = cids[i]

        attempts_remaining = 5
        while attempts_remaining > 0:
            response = requests.post(url, data=data, timeout=30.0)
            if response.status_code == 200:
                print("Y", end="", flush=True)
                if mode == "likes_dislikes":
                    likes, dislikes = [], []
                    mine = response.json()["data"]["my_reactions"]
                    others = response.json()["data"]["others_reactions"]
                    for claim_id in cids[i].split(","):
                        likes += [mine[claim_id]["like"] + others[claim_id]["like"]]
                        dislikes += [mine[claim_id]["dislike"] + others[claim_id]["dislike"]]
                    result[0] += likes
                    result[1] += dislikes
                else:
                    for value in response.json()["data"]:
                        result.append(value)
                attempts_remaining = 0
            else:
                print("N", end="", flush=True)
                attempts_remaining -= 1
                if attempts_remaining == 4 and batch_size > 1:
                    time.sleep(10.0)
                elif attempts_remaining > 1:
                    time.sleep(0.1)
                else:
                    if batch_size > 1:
                        return get_counts(claim_ids, mode, batch_size=1)
                    else:
                        temp = None
                        if mode == "likes_dislikes":
                            temp = (None, None)
                        result.append([temp for _ in range(batch_sizes[i])])

    return result

