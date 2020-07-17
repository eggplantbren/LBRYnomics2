import json
import pandas

f = open("json/top_500.json")
x = json.load(f)
f.close()

df = pandas.DataFrame()
for key in x.keys():
    df[key] = x[key]

df.to_csv("top_500.csv", header=True, index=False)

