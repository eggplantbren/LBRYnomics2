import apsw
from config import *
import datetime
import json
import requests
import time

def run():
    print("Finding trending tags...", flush=True, end="")

    try:
        # Get readers
        cdb_conn = apsw.Connection(config["claims_db_file"],
                                   flags=apsw.SQLITE_OPEN_READONLY)
        cdb_conn.setbusytimeout(60000)
        cdb = cdb_conn.cursor()

        response = requests.post("http://localhost:5279",
                                 json=dict(method="status", params={})).json()
        height = response["result"]["wallet"]["blocks"]

        bin_size = 1000
        result = {}
        result["human_time_utc"] = str(datetime.datetime.utcfromtimestamp(time.time()))
        result["rank"] = []
        result["tag"] = []
        result["count"] = []

        rank = 1
        for row in cdb.execute("SELECT tag, COUNT(*) AS number FROM tag\
                                    WHERE height >= ?\
                                    GROUP BY tag.tag\
                                    ORDER BY number DESC\
                                    LIMIT 200;", (height - bin_size, )):
            result["rank"].append(rank)
            result["tag"].append(row[0])
            result["count"].append(row[1])
            rank += 1

        f = open("json/popular_tags_last_1000_blocks.json", "w")
        json.dump(result, f)
        f.close()
        print("done.")
    except:
        print("something went wrong.")

if __name__ == "__main__":
    run()

