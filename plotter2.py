import apsw
from collections import OrderedDict
import datetime
import numpy as np
import numpy.random as rng
import plotly
import plotly.graph_objects as go

# Read-only connection to top channels database
tcdb_conn = apsw.Connection("db/top_channels.db",
                            flags=apsw.SQLITE_OPEN_READONLY)
tcdb = tcdb_conn.cursor()


HTML = \
"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <style>body { background-color: #222222; color: #E6E6E6;
                  font-family: 'Open Sans', Arial, sans-serif; }</style>
    <title>LBRY Channels Interactive Graphs</title>
    %%PLOTLYJS%%
</head>
<body>
    %%CONTENT%%
</body>
</html>
"""
f = open("plotlyjs.txt")
plotlyjs = "".join(f.readlines())
HTML = HTML.replace("%%PLOTLYJS%%", plotlyjs)
f.close()

def make_fig(channels, quantity="followers"):
    assert quantity in ["followers", "views", "reposts", "lbc"]

    if quantity == "followers":
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
                      font=dict(color="rgb(230, 230, 230)", size=14,
                                family="'Open Sans', Arial, sans-serif"),
                      xaxis=dict(title="Date", color="rgb(230, 230, 230)"),
                      yaxis=dict(title=yaxis_title,
                                 color="rgb(230, 230, 230)"))

    # Loop over channels
    for claim_hash in channels:
        datetimes = [datetime.datetime.fromtimestamp(t)\
                            for t in channels[claim_hash]["data"]["ts"]]
        #print(channels[claim_hash]["vanity_name"], datetimes[-1])
        visible = True
        if channels[claim_hash]["vanity_name"] in ["@lbry", "@lbrycast"]:
            visible = "legendonly"
        fig.add_trace(go.Scatter(x=datetimes,
                                 y=channels[claim_hash]["data"][quantity],
                                 showlegend=True,
                                 mode="lines+markers",
                                 name=channels[claim_hash]["vanity_name"],
                                 visible=visible))

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

    div = plotly.offline.plot(fig, output_type="div",
                              auto_open=False,
                              include_plotlyjs=False)

    # Give the div a sensible ID
    div = div.replace("<div>\n", f"<div id=\"{quantity}\">\n")

    return div

def html_plot(num_channels=20, mode="top"):
    assert mode in {"top", "random"}

    # Get current top channels
    channels = OrderedDict()
    for row in tcdb.execute("""SELECT claim_hash, vanity_name, rank
                             FROM channels c INNER JOIN measurements m
                                ON m.channel = c.claim_hash
                             WHERE epoch = (SELECT MAX(id) FROM epochs)
                             AND rank IS NOT NULL
                             ORDER BY rank ASC;"""):
        claim_hash, vanity_name, rank = row
        channels[claim_hash] = dict(vanity_name=vanity_name, rank=rank,
                                  data={"ts": [], "followers": [],
                                        "views": [], "reposts": [], "lbc": []})
        if mode == "top" and len(channels) >= num_channels:
            break

    if mode == "random":

        # Remove top 20
        _channels = OrderedDict()
        for ch in channels:
            if channels[ch]["rank"] > 20:
                _channels[ch] = channels[ch]
        channels = _channels

        # 20 random channels!
        which = set()
        while len(which) < num_channels:
            which.add(rng.randint(len(channels)))
        _channels = dict()
        i = 0
        for ch in channels:
            if i in which:
                _channels[ch] = channels[ch]
            i += 1

        channels = _channels

    # Question marks
    qms = "?, ".join(["" for i in range(num_channels+1)])
    qms = "(" + qms[0:-2] + ")"

    for row in tcdb.execute(f"""SELECT claim_hash, vanity_name,
                                    time, followers, views, reposts, lbc
                             FROM epochs e INNER JOIN measurements m
                                           INNER JOIN channels c
                                           ON e.id = m.epoch AND
                                           m.channel = c.claim_hash
                             WHERE claim_hash IN {qms};""", # No injection risk
                             channels.keys()):
        claim_hash, vanity_name, time, followers, views, reposts, lbc = row
        channels[claim_hash]["data"]["ts"].append(time)
        channels[claim_hash]["data"]["followers"].append(followers)
        channels[claim_hash]["data"]["views"].append(views)
        channels[claim_hash]["data"]["reposts"].append(reposts)
        channels[claim_hash]["data"]["lbc"].append(lbc)
#        print(time)

    div1 = make_fig(channels, "followers")
    div2 = make_fig(channels, "views")
    div3 = make_fig(channels, "reposts")
    div4 = make_fig(channels, "lbc")

    if mode=="top":
        filename = "plots/interactive.html"
    else:
        filename = "plots/interactive_random.html"
    f = open(filename, "w")
    html = HTML.replace("%%TOP%%", str(num_channels))
    html = html.replace("%%CONTENT%%", "\n".join([div1, div2, div3, div4]))
    f.write(html)
    f.close()

    # Version without HTML surrounding it
    if mode=="top":
        filename = "plots/interactive_parts.html"
    else:
        filename = "plots/interactive_random_parts.html"
    f = open(filename, "w")
    f.write("<!-- JavaScript for Plotly -->\n\n")
    f.write(plotlyjs + "\n")
    f.write("<!-- followers plot -->\n")
    f.write(div1 + "\n")
    f.write("<!-- views plot -->\n")
    f.write(div2 + "\n")
    f.write("<!-- reposts plot -->\n")
    f.write(div3 + "\n")
    f.write("<!-- lbc plot -->\n")
    f.write(div4 + "\n")
    f.close()



if __name__ == "__main__":
    html_plot(mode="top")
    html_plot(mode="random")


