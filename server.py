#!/usr/bin/env python
import apsw
from flask import Flask
import json
import subprocess
import time

app = Flask(__name__)
conn = apsw.Connection("db/top_channels.db", flags=apsw.SQLITE_OPEN_READONLY)
db = conn.cursor()

conn2 = apsw.Connection("db/view_crawler.db", flags=apsw.SQLITE_OPEN_READONLY)
db2 = conn2.cursor()

# Generous timeouts
conn.setbusytimeout(60000)
conn2.setbusytimeout(60000)

@app.route("/")
def hello_world():
   return "Hello World"

@app.route("/status/")
def status():
    x = subprocess.run("ps -e | grep run_lbrynomics | wc -l",
                       shell=True, capture_output=True)
    count = int(x.stdout.decode("utf-8"))
    return json.dumps({"running": count == 1}, indent=4)

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


@app.route("/views/<claim_id>")
def views(claim_id):
    claim_hash = bytes.fromhex(claim_id)[::-1]

    # Current views
    current = db2.execute("SELECT MAX(views) FROM stream_measurements\
                            WHERE stream = ?;",
                          (claim_hash, )).fetchone()[0]

    # Number of streams
    num_streams = db2.execute("SELECT COUNT(*) FROM streams;").fetchone()[0]

    rank = db2.execute("""SELECT COUNT(stream) FROM
                       (SELECT stream, MAX(views) v FROM stream_measurements
                        GROUP BY stream) AS temp WHERE temp.v >= ?;""",
                        (current, )).fetchone()[0]

    result = { "rank": rank, "out_of": num_streams }
    return(json.dumps(result, indent=4))



if __name__ == "__main__":
    app.run(host="0.0.0.0")

