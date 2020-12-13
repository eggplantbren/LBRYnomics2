import apsw
import config
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import requests
import yaml

f = open("config.yaml")
x = yaml.load(f, Loader=yaml.SafeLoader)
f.close()


# Get current block
response = requests.post("http://localhost:5279", json={"method": "status", "params": {}}).json()
block = response["result"]["wallet"]["blocks"]

#back = input(f"How many blocks back do you want to go?: ")
#print("")
start_block = 0 #block - int(back)

conn = apsw.Connection(x["claims_db_file"])
db = conn.cursor()

channels = ["@drsambailey", "@paulvanderklay", "@alaslewisandbarnes", "@emmyhucker"]

#channels = ["@emmyhucker", "@justinmurphy", "@paulvanderklay", "@mikenayna",
#            "@theworthyhouse", "@AlasLewisAndBarnes", "@veritasium",
#            "@skepticlawyer", "@benjaminaboyce", "@sensemakesmath", "@mru"]

response = requests.post("http://localhost:5279",
                         json={"method": "resolve",
                               "params": {"urls": channels}}).json()["result"]
for channel in channels:

    #print(f"Channel = {channel}.", flush=True)
    claim_id = response[channel]["claim_id"]
    claim_hash = db.execute("""SELECT claim_hash FROM claim
                               WHERE claim_id = ?;""",
                            (claim_id, )).fetchone()[0]

    all_claim_hashes = []
    for row in db.execute("""SELECT claim_hash FROM claim WHERE
                           claim_hash = ? OR channel_hash = ?;""",
                        (claim_hash, claim_hash)):
        all_claim_hashes.append(row[0])

    # Get supports
    ts = []
    ys = []
    for ch in all_claim_hashes:
        for row in db.execute("""
                              SELECT height, amount/1E8 lbc FROM support
                              WHERE claim_hash = ? AND lbc <= 10.0
                              AND height >= ?
;
                              """, (ch, start_block)):
            ts.append(row[0])
            ys.append(row[1])
#            print(f"\rGot supports for claim {len(ts)}.", end="", flush=True)
#    print("")

    ts = np.array(ts)
    ys = np.array(ys)
    ii = np.argsort(ts)
    ts = ts[ii]
    ys = ys[ii]

    print(channel, ys, np.round(np.sum(ys), 2))
    print("")

#    # Truncate to the most recent fortnight
    ys = ys[ts >= block - 4032*2 - 10]
    ts = ts[ts >= block - 4032*2 - 10]
    ys = np.cumsum(ys)

    plt.plot(ts, ys, "-", label=channel)

plt.legend()
plt.axvline(block, linestyle="--", color="r", alpha=0.3)
#plt.xlim([block - 576, block + 10])
#plt.xlim([block - 4032 - 10, block + 10])
plt.ylim(bottom=0.0)
print("Saving supported.png")
plt.savefig("supported.png", dpi=450)
#plt.show()
conn.close()

