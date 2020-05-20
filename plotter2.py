import apsw
import datetime
import numpy as np
import plotly
import plotly.graph_objects as go

def html_plot():

    # Get data and put it in a nice dictionary
    conn = apsw.Connection("db/lbrynomics.db")
    db = conn.cursor()

    data = dict()
    for row in db.execute("""SELECT cm.claim_id, cm.vanity_name,
                                    e.time, cm.num_followers, views, lbc
                             FROM epochs e INNER JOIN channel_measurements cm
                             ON e.id = cm.epoch
                             WHERE cm.claim_id IN
                                    (SELECT claim_id FROM channel_measurements
                                     WHERE rank <= 10 ORDER BY epoch DESC,
                                     rank ASC LIMIT 10);"""):
        claim_id, vanity_name, time, num_followers, views, lbc = row
        if claim_id not in data:
            data[claim_id] = dict(vanity_name=vanity_name, ts=[], ys=[])
        data[claim_id]["ts"].append(time)
        data[claim_id]["ys"].append(num_followers)

    # Plotly figure
    fig = go.Figure()
    fig.update_layout(title="Growth of the Top 10 LBRY channels")

    # Loop over channels
    for claim_id in data:
        datetimes = [datetime.datetime.fromtimestamp(t)\
                            for t in data[claim_id]["ts"]]
        fig.add_trace(go.Scatter(x=datetimes,
                                 y=data[claim_id]["ys"],
                                 showlegend=True,
                                 mode="lines+markers",
                                 name=data[claim_id]["vanity_name"]))

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
    plotly.offline.plot(fig, filename="plots.html", auto_open=False)

    db.close()

if __name__ == "__main__":
    html_plot()


