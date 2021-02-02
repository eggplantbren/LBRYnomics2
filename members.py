import apsw
from config import claims_db_file
import requests
import time

conn = apsw.Connection("db/members.db")
db = conn.cursor()

def create_database():
    db.execute("pragma foreign_keys = on;")
    db.execute("pragma synchronous = 0;")
    db.execute("pragma journal_mode = wal;")

    db.execute("begin;")
    db.execute("create table if not exists channels\
      (claim_hash  bytes not null primary key,\
       vanity_name text not null)\
      without rowid;")
    db.execute("create table if not exists streams\
      (claim_hash bytes not null primary key,\
       channel    bytes not null,\
       vanity_name text not null,\
       foreign key (channel) references channels (claim_hash))\
     without rowid;")
    db.execute("create table if not exists stream_measurements\
      (stream bytes not null,\
       time   integer not null,\
       lbc    real not null,\
       views  integer not null default 0,\
       comments integer not null default 0,\
       primary key (stream, time),\
       foreign key (stream) references streams (claim_hash))\
      without rowid;")
    db.execute("commit;")


class Claim:
    def __init__(self, url):
        self.claim_id, self.claim_name, self.claim_type = resolve(url)

    @property
    def claim_hash(self):
        return bytes.fromhex(self.claim_id)[::-1]


def resolve(url):
    response = requests.post("http://localhost:5279",
                             json={"method": "resolve",
                                   "params": {"urls": [url]}})

    try:
        item = response.json()["result"][url]
        claim_name = item["name"]
        claim_id = item["claim_id"]
        claim_type = item["value_type"]
    except:
        return None

    return [claim_id, claim_name, claim_type]

def add_channel(channel):
    assert channel.claim_type == "channel"
    db.execute("begin;")
    db.execute("insert into channels values (?, ?)\
                on conflict (claim_hash) do nothing;",
               (channel.claim_hash, channel.claim_name))
    db.execute("commit;")


def update_streams_in_channel(channel):
    assert channel.claim_type == "channel"

    now = time.time()
    cconn = apsw.Connection(claims_db_file, flags=apsw.SQLITE_OPEN_READONLY)
    cdb = cconn.cursor()
    db.execute("begin;")
    for row in cdb.execute("select claim_hash, claim_name,\
                                   amount + support_amount\
                            from claim\
                            where channel_hash = ? and claim_type = 1;",
                           (channel.claim_hash, )):
        claim_hash, claim_name, deweys = row
        my_row = [claim_hash, now, deweys/1E8]
        db.execute("insert into streams values (?, ?, ?)\
                    on conflict (claim_hash) do nothing;",
                   (claim_hash, channel.claim_hash, claim_name))
        db.execute("insert into stream_measurements (stream, time, lbc)\
                    values (?, ?, ?);", my_row)
    db.execute("commit;")
    cconn.close()


create_database()
channel = Claim("@BrendonBrewer")
add_channel(channel)
update_streams_in_channel(channel)

