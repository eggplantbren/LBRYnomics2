import apsw
import config
import requests
import yaml



MAX_BATCH_SIZE = 1024
assert MAX_BATCH_SIZE % 2 == 0


def measure_channel(claim_hash):
    """
    Measure views, likes, and dislikes of a channel.
    """
    streams = dict()

    # Get reader for claims.db
    cdb_conn = apsw.Connection(config.claims_db_file,
                                flags=apsw.SQLITE_OPEN_READONLY)
    cdb_conn.setbusytimeout(60000)
    cdb = cdb_conn.cursor()

    # Streams in the channel
    print("Finding all streams in the channel...", end="", flush=True)
    for row in cdb.execute("SELECT claim_id FROM claim\
                            WHERE channel_hash = ?\
                            AND claim_type = 1;",
                           (claim_hash, )):
        streams[row[0]] = dict(views=None, likes=None, dislikes=None, solo_attempts=0)
    print(f"done. There are {len(streams)} streams.", flush=True)

    # Get the view counts. Dicts are mutable.
    print(f"Getting view counts.", flush=True)
    get_views(streams)
    print("done.")

    print(f"Getting likes.", flush=True)
    get_likes(streams)
    print("done.")

    total_views = sum(streams[cid]["views"] for cid in streams)
    total_likes = sum(streams[cid]["likes"] for cid in streams)
    total_dislikes = sum(streams[cid]["dislikes"] for cid in streams)

    return dict(total_views=total_views, total_likes=total_likes,
                total_dislikes=total_dislikes)



def get_views(streams, batch_size=MAX_BATCH_SIZE):

    # Find up to batch_size streams without a view count
    todo = []
    for claim_id in streams:
        if streams[claim_id]["views"] is None:
            todo.append(claim_id)
        if len(todo) >= batch_size:
            break

    # Terminate if nothing left to do
    if len(todo) == 0:
        return

    # Get auth token
    f= open("secrets.yaml")
    auth_token = yaml.load(f, Loader=yaml.SafeLoader)["auth_token"]
    f.close()

    # Create query
    cids = ",".join(todo)
    try:
        response = requests.post("https://api.lbry.com/file/view_count",
                                 data={"auth_token": auth_token,
                                       "claim_id": cids}, timeout=30.0)
        query_returned = True
    except:
        query_returned = False

    if query_returned and response.status_code == 200:
        for i in range(len(todo)):
            streams[todo[i]]["views"] = response.json()["data"][i]
        next_batch_size = MAX_BATCH_SIZE
        success = True
    else:
        next_batch_size = len(todo) // 2
        if next_batch_size == 0:
            next_batch_size = 1
        success = False
    print(f"(batch_size={len(todo)}, success={success}) ", end="", flush=True)

    if next_batch_size >= 1:
        get_views(streams, next_batch_size)


def get_likes(streams, batch_size=MAX_BATCH_SIZE):

    total_failures = 0

    while True:

        # Find up to batch_size streams without a view count
        todo = []
        for claim_id in streams:
            if streams[claim_id]["likes"] is None or streams[claim_id]["dislikes"] is None:
                todo.append(claim_id)
            if len(todo) >= batch_size:
                break

        # Terminate if nothing left to do
        if len(todo) == 0:
            return

        # Get auth token
        f= open("secrets.yaml")
        auth_token = yaml.load(f, Loader=yaml.SafeLoader)["auth_token"]
        f.close()

        # Increment solo attempts
        if len(todo) == 1:
            for cid in todo:
                streams[cid]["solo_attempts"] += 1

        # Create query
        cids = ",".join(todo)
        try:
            response = requests.post("https://api.lbry.com/reaction/list",
                                 data={"auth_token": auth_token,
                                       "claim_ids": cids}, timeout=30.0)
            data = response.json()["data"]
            for i in range(len(todo)):
                streams[todo[i]]["likes"] = data["my_reactions"][todo[i]]["like"]
                streams[todo[i]]["likes"] += data["others_reactions"][todo[i]]["like"]
                streams[todo[i]]["dislikes"] = data["my_reactions"][todo[i]]["dislike"]
                streams[todo[i]]["dislikes"] += data["others_reactions"][todo[i]]["dislike"]
            next_batch_size = MAX_BATCH_SIZE
            success = True

        except:
            next_batch_size = len(todo) // 2
            if next_batch_size == 0:
                next_batch_size = 1
            success = False

            # After three failed solo attempts, just give up and set result to zero
            for cid in todo:
                if streams[cid]["solo_attempts"] >= 3:
                    streams[cid]["likes"] = 0
                    streams[cid]["dislikes"] = 0
                    next_batch_size = MAX_BATCH_SIZE
                    total_failures += 1
                    success = "ABORTED, IMPUTING ZERO"

        print(f"(batch_size={len(todo)}, success={success}) ", end="", flush=True)
        batch_size = next_batch_size

        if total_failures >= 20:
            for cid in todo:
                streams[cid]["likes"] = 0
                streams[cid]["dislikes"] = 0
            print("Giving up on channel. Too many failures.", flush=True)




if __name__ == "__main__":
    result = measure_channel(bytes.fromhex("aaeda15cc0cafe689793a00d5e6c5a231e3b6ee8")[::-1])
    print(result)


