import apsw
from collections import OrderedDict
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
    <style>body { background-color: #222222; }</style>
    <title>LBRY Top Channels Interactive Graph</title>
</head>
<body>
    %%CONTENT%%
</body>
</html>
"""

def html_plot(top=10):

    # Get data and put it in a nice dictionary
    conn = apsw.Connection("db/lbrynomics.db")
    db = conn.cursor()

    # Get current top channels
    channels = OrderedDict()
    for row in db.execute("""SELECT claim_id, vanity_name, rank
                             FROM channel_measurements
                             WHERE epoch = (SELECT MAX(id) FROM epochs)
                             AND rank <= ?
                             ORDER BY rank ASC;""", (top, )):
        claim_id, vanity_name, rank = row
        channels[claim_id] = dict(vanity_name=vanity_name, rank=rank,
                                  data={"ts": [], "ys": []})

    # Question marks
    qms = "?, ".join(["" for i in range(top+1)])
    qms = "(" + qms[0:-2] + ")"

    for row in db.execute(f"""SELECT claim_id, vanity_name,
                                    time, num_followers, views, lbc
                             FROM epochs e INNER JOIN channel_measurements cm
                             ON e.id = cm.epoch
                             WHERE claim_id IN {qms};""", # No injection risk
                             channels.keys()):
        claim_id, vanity_name, time, num_followers, views, lbc = row
        channels[claim_id]["data"]["ts"].append(time)
        channels[claim_id]["data"]["ys"].append(num_followers)

    # Plotly figure
    fig = go.Figure()
    fig.update_layout(height=800, width=1500,
                      title="Growth of the Top 10 LBRY channels",
                      plot_bgcolor="rgb(20, 20, 20)",
                      paper_bgcolor="rgb(20, 20, 20)",
                      font=dict(color="rgb(230, 230, 230)", size=14),
                      xaxis=dict(title="Date", color="rgb(230, 230, 230)"),
                      yaxis=dict(title="Number of Followers",
                                 color="rgb(230, 230, 230)"))

    # Loop over channels
    for claim_id in channels:
        datetimes = [datetime.datetime.fromtimestamp(t)\
                            for t in channels[claim_id]["data"]["ts"]]
        fig.add_trace(go.Scatter(x=datetimes,
                                 y=channels[claim_id]["data"]["ys"],
                                 showlegend=True,
                                 mode="lines+markers",
                                 name=channels[claim_id]["vanity_name"],
                                 ))

    # Add year lines
    shapes = []
#    for year in range(2017, 2021):
#        shapes.append(dict(type="line",
#                           x0=datetime.datetime(year, 1, 1, 0, 0, 0),
#                           x1=datetime.datetime(year, 1, 1, 0, 0, 0),
#                           y0=ys.min(),
#                           y1=ys.max(),
#                           line=dict(dash="dash", width=2, color="red")))
    fig.update_layout(shapes=shapes)

    div = plotly.offline.plot(fig, output_type="div", auto_open=False,                 
                              include_plotlyjs=True)
    f = open("plots.html", "w")
    f.write(HTML.replace("%%CONTENT%%", div))
    f.close()

    db.close()

if __name__ == "__main__":
    html_plot()


