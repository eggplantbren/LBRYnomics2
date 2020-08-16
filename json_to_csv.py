import json
import pandas

f = open("json/top_500.json")
x = json.load(f)
f.close()

df = pandas.DataFrame()
df["rank"] = x["ranks"]
df["vanity_name"] = x["vanity_names"]
df["claim_id"] = x["claim_ids"]
df["lbc"] = x["lbc"]
df["followers"] = x["subscribers"]
df["views"] = x["views"]
df["reposts"] = x["times_reposted"]
df["nsfw"] = x["is_nsfw"]

df.to_csv("top_500.csv", header=True, index=False)

