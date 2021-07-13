import apsw
from config import *
import datetime
import json
import requests
import time

def run(mode):
    assert mode in set(["day", "week", "month", "year", "all_time"])

    print(f"    Finding hot tags (mode = {mode})...", flush=True, end="")

    try:
        # Get readers
        cdb_conn = apsw.Connection(config["claims_db_file"],
                                   flags=apsw.SQLITE_OPEN_READONLY)
        cdb_conn.setbusytimeout(60000)
        cdb = cdb_conn.cursor()

        response = requests.post("http://localhost:5279",
                                 json=dict(method="status", params={})).json()
        height = response["result"]["wallet"]["blocks"]

        limit = 0
        if mode == "day":
            limit = height - 576
        elif mode == "week":
            limit = height - 7*576
        elif mode == "month":
            limit = height - 30*576
        elif mode == "year":
            limit = height - 365*576

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
                                    LIMIT 50;", (limit, )):
            result["rank"].append(rank)
            result["tag"].append(row[0])
            result["count"].append(row[1])
            rank += 1

        f = open(f"json/hot_tags_{mode}.json", "w")
        json.dump(result, f)
        f.close()
        print("done.")
    except:
        print("something went wrong.")

if __name__ == "__main__":
    for mode in set(["day", "week", "month", "year", "all_time"]):
        run(mode)

