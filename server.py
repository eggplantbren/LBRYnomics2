import apsw
from flask import Flask
import json
import time

app = Flask(__name__)
conn = apsw.Connection("db/top_channels.db", flags=apsw.SQLITE_OPEN_READONLY)
db = conn.cursor()

@app.route("/")
def hello_world():
   return "Hello World"

@app.route("/channel/<claim_id>")
def lookup_channel(claim_id):
    claim_hash = bytes.fromhex(claim_id)[::-1]

    result = {}
    for row in db.execute("SELECT time, rank, followers, views, reposts, lbc\
                           FROM measurements m INNER JOIN channels c\
                           INNER JOIN epochs e\
                           ON c.claim_hash = m.channel\
                           AND e.id = m.epoch\
                           WHERE c.claim_hash = ?\
                           ORDER BY epoch DESC LIMIT 1;", (claim_hash, )):
        t, rank, followers, views, reposts, lbc = row
        result = dict(last_checked="{:.3f} days ago"\
                                .format((time.time() - t)/86400.0)   ,                                  
                      rank=rank,
                      followers=followers,
                      views=views,
                      reposts=reposts,
                      lbc=lbc)
    return(json.dumps(result, indent=4))

if __name__ == "__main__":
    app.run(host="0.0.0.0")

