import apsw
import config
import numpy as np
import numpy.random as rng
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
        streams[row[0]] = dict(views=None, likes=None, dislikes=None)
    print(f"done. There are {len(streams)} streams.", flush=True)

    # Get the view counts. Dicts are mutable.
    print(f"Getting view counts.", flush=True)
    get_views(streams)

    return streams



def get_views(streams, batch_size=MAX_BATCH_SIZE):

    # Find up to 1000 streams without a view count
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
    response = requests.post("https://api.lbry.com/file/view_count",
                             data={"auth_token": auth_token,
                                   "claim_id": cids}, timeout=30.0)
    if response.status_code == 200:
        for i in range(len(todo)):
            streams[todo[i]]["views"] = response.json()["data"][i]
        next_batch_size = MAX_BATCH_SIZE
        success = True
    else:
        next_batch_size = batch_size // 2
        success = False
    print(f"(batch_size={batch_size}, success={success}) ", end="", flush=True)

    if next_batch_size >= 1:
        get_views(streams, next_batch_size)


if __name__ == "__main__":
    streams = measure_channel(bytes.fromhex("aaeda15cc0cafe689793a00d5e6c5a231e3b6ee8")[::-1])

