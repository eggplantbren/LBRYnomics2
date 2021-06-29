import apsw
from config import *
import json
import requests



# Get readers
cdb_conn = apsw.Connection(config["claims_db_file"],
                           flags=apsw.SQLITE_OPEN_READONLY)
cdb_conn.setbusytimeout(60000)
cdb = cdb_conn.cursor()

response = requests.post("http://localhost:5279",
                         json=dict(method="status", params={})).json()
height = response["result"]["wallet"]["blocks"]


bin_size = 1000
result = []
rank = 1
for row in cdb.execute("SELECT tag, COUNT(*) AS number FROM tag\
                            WHERE height >= ?\
                            GROUP BY tag.tag\
                            ORDER BY number DESC\
                            LIMIT 100;", (height - bin_size, )):
    result.append((rank, ) + row)

f = open("json/popular_tags_last_1000_blocks.json", "w")
json.dump(result, f)
f.close()

