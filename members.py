import apsw
from config import claims_db_file
import requests


conn = apsw.Connection("db/members.db")
db = conn.cursor()

def create_database():
    db.execute("pragma synchronous = 0;")
    db.execute("pragma journal_mode = wal;")

    db.execute("begin;")
    db.execute("create table if not exists channels\
      (claim_hash  bytes not null primary key,\
       vanity_name text not null)\
      without rowid;");
    db.execute("commit;")


def resolve(url):
    response = requests.post("http://localhost:5279",
                             json={"method": "resolve",
                                   "params": {"urls": [url]}})

    try:
        item = response.json()["result"][url]
        claim_name = item["name"]
        claim_id = item["claim_id"]
    except:
        return None

    return [claim_name, claim_id]

def add_channel(url):
    claim_name, claim_id = resolve(url)
    claim_hash = bytes.fromhex(claim_id)[::-1]
    db.execute("begin;")
    db.execute("insert into channels values (?, ?);", (claim_hash, claim_name))
    db.execute("commit;")

#    cconn = apsw.Connection(claims_db_file, flags=apsw.SQLITE_OPEN_READONLY)
#    cdb = cconn.cursor()
#    for row in cdb.execute("select claim_name from claim\
#                            where channel_hash = ?;", (claim_hash, )):
#        claim_name = row
#        print(claim_name)
#    cconn.close()


create_database()
add_channel("@BrendonBrewer")

