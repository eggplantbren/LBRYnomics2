import requests
import yaml

def get_view_counts(claim_ids):

    result = []

    # Get auth token
    f= open("secrets.yaml")
    auth_token = yaml.load(f, Loader=yaml.SafeLoader)["auth_token"]
    f.close()

    cids = ",".join(claim_ids)
    response = requests.post("https://api.lbry.com/file/view_count",
                             data={"auth_token": auth_token,
                                   "claim_id": cids}, timeout=20.0)
    if response.status_code == 200:
        for value in response.json()["data"]:
            result.append(value)        
    else:
        raise ValueError("HTTP request status code was not 200.")

    return result

