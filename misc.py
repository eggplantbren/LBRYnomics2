import requests
import yaml

def get_view_counts(claim_ids, start, end):
    result = []

    # Elegantly handle end
    if end > len(claim_ids):
        end = len(claim_ids)

    if start == end:
        print("Start equalled end!")

    # Get auth token
    f= open("secrets.yaml")
    auth_token = yaml.load(f, Loader=yaml.SafeLoader)["auth_token"]
    f.close()

    # Prepare the request to the LBRY API
    url = "https://api.lbry.com/file/view_count?auth_token=" +\
                auth_token + "&claim_id="
    for i in range(start, end):
        url += claim_ids[i]
        if i != end-1:
            url += ","

    # JSON response from API
    try:
        response = requests.get(url).json()
        for value in response["data"]:
            result.append(value)
        print(".", end="", flush=True)
    except:
        result.append(None)

    return result

