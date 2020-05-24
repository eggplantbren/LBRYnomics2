import apsw
from collections import OrderedDict
import databases
import datetime
import numpy as np
import plotly
import plotly.graph_objects as go

HTML = \
"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <style>body { background-color: #222222; color: #E6E6E6; }</style>
    <title>LBRY Top Channels Interactive Graphs</title>
    %%PLOTLYJS%%
</head>
<body>
    <h2>Growth of the Top %%TOP%% LBRY Channels</h2>
    %%CONTENT%%
</body>
</html>
"""
f = open("plotlyjs.txt")
s = "".join(f.readlines())
HTML = HTML.replace("%%PLOTLYJS%%", s)
f.close()

def make_fig(channels, quantity="num_followers"):
    assert quantity in ["num_followers", "views", "reposts", "lbc"]

    if quantity == "num_followers":
        yaxis_title = "Followers"
    elif quantity == "views":
        yaxis_title = "Views"
    elif quantity == "reposts":
        yaxis_title = "Reposts"
    elif quantity == "lbc":
        yaxis_title = "LBC"

    # Plotly figure
    fig = go.Figure()
    fig.update_layout(height=800, width=1500,
                      title=f"{yaxis_title}",
                      plot_bgcolor="rgb(32, 32, 32)",
                      paper_bgcolor="rgb(32, 32, 32)",
                      font=dict(color="rgb(230, 230, 230)", size=14),
                      xaxis=dict(title="Date", color="rgb(230, 230, 230)"),
                      yaxis=dict(title=yaxis_title,
                                 color="rgb(230, 230, 230)"))

    # Loop over channels
    for claim_id in channels:
        datetimes = [datetime.datetime.fromtimestamp(t)\
                            for t in channels[claim_id]["data"]["ts"]]
        #print(channels[claim_id]["vanity_name"], datetimes[-1])
        fig.add_trace(go.Scatter(x=datetimes,
                                 y=channels[claim_id]["data"][quantity],
                                 showlegend=True,
                                 mode="lines+markers",
                                 name=channels[claim_id]["vanity_name"]))

    # Add year lines
#    shapes = []
#    for year in range(2017, 2021):
#        shapes.append(dict(type="line",
#                           x0=datetime.datetime(year, 1, 1, 0, 0, 0),
#                           x1=datetime.datetime(year, 1, 1, 0, 0, 0),
#                           y0=ys.min(),
#                           y1=ys.max(),
#                           line=dict(dash="dash", width=2, color="red")))
#    fig.update_layout(shapes=shapes)

    div = plotly.offline.plot(fig, output_type="div", auto_open=False,                 
                              include_plotlyjs=False)
    return div

def html_plot(top=20):

    db = databases.dbs["lbrynomics"]
    # print(db.execute("SELECT MAX(id) FROM epochs;").fetchall())

    # Get current top channels
    channels = OrderedDict()
    for row in db.execute("""SELECT claim_id, vanity_name, rank
                             FROM channel_measurements
                             WHERE epoch = (SELECT MAX(id) FROM epochs)
                             AND rank <= ?
                             ORDER BY rank ASC;""", (top, )):
        claim_id, vanity_name, rank = row
        channels[claim_id] = dict(vanity_name=vanity_name, rank=rank,
                                  data={"ts": [], "num_followers": [],
                                        "views": [], "reposts": [], "lbc": []})

    # Question marks
    qms = "?, ".join(["" for i in range(top+1)])
    qms = "(" + qms[0:-2] + ")"

    for row in db.execute(f"""SELECT claim_id, vanity_name,
                                    time, num_followers, views, times_reposted, lbc
                             FROM epochs e INNER JOIN channel_measurements cm
                             ON e.id = cm.epoch
                             WHERE claim_id IN {qms};""", # No injection risk
                             channels.keys()):
        claim_id, vanity_name, time, num_followers, views, reposts, lbc = row
        channels[claim_id]["data"]["ts"].append(time)
        channels[claim_id]["data"]["num_followers"].append(num_followers)
        channels[claim_id]["data"]["views"].append(views)
        channels[claim_id]["data"]["reposts"].append(reposts)
        channels[claim_id]["data"]["lbc"].append(lbc)
#        print(time)

    div1 = make_fig(channels, "num_followers")
    div2 = make_fig(channels, "views")
    div3 = make_fig(channels, "reposts")
    div4 = make_fig(channels, "lbc")

    f = open("plots/interactive.html", "w")
    html = HTML.replace("%%TOP%%", str(top))
    html = html.replace("%%CONTENT%%", "\n".join([div1, div2, div3, div4]))
    f.write(html)
    f.close()



    db.close()

if __name__ == "__main__":
    html_plot()


