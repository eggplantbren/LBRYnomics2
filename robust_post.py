import requests
import time
import yaml

BATCH_SIZE = 1000

def get_counts(claim_ids, mode="views"):

    assert mode in ["views", "followers", "likes_dislikes"]

    result = []

    # Get auth token
    f= open("secrets.yaml")
    auth_token = yaml.load(f, Loader=yaml.SafeLoader)["auth_token"]
    f.close()

    url = "https://api.lbry.com/"
    if mode == "views":
        url += "file/view_count"
    elif mode == "followers":
        url += "subscription/sub_count"
    elif mode == "likes_dislikes":
        url += "reaction/list"

    # Batch into groups of 1000
    cids = []
    num_batches = 1 + (len(claim_ids)-1) // BATCH_SIZE
    batch_sizes = []
    for i in range(num_batches):
        start = i*BATCH_SIZE
        end = (i+1)*BATCH_SIZE
        if end > len(claim_ids):
            end = len(claim_ids)
        cids.append(",".join(claim_ids[start:end]))
        batch_sizes.append(end - start)

    # Run each batch
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
                for value in response.json()["data"]:
                    result.append(value)
                attempts_remaining = 0
            else:
                attempts_remaining -= 1
                if attempts_remaining > 0:
                    time.sleep(10.0)
                else:
                    result.append([None for _ in range(batch_sizes[i])])

    return result

