# -*- coding: utf-8 -*-
import apsw
import dash
import dash_core_components as dcc
import dash_html_components as html
import datetime
import numpy as np
import time
from dash.dependencies import Input, Output

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

def get_start_of_today(now):
    """
    Returns unix epoch of the start of the day, based on input 'now'
    """
    start_of_today = datetime.datetime.fromtimestamp(now, datetime.timezone.utc)\
                        .replace(hour=0, minute=0, second=0, microsecond=0)
    start_of_today = start_of_today.timestamp()
    return start_of_today

# Create the app
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

# The graph to be given to the app
graph = dcc.Graph(id="num_streams")

app.layout = html.Div(style={"background-color": "#222222",
                             "color": "#EEEEEE"},
                      children=[html.H1(children="LBRYnomics Interactive"),
                                html.P(children="This is just a test!"),
                                graph, dcc.Interval(
                                   id='interval-component',
                                   interval=60*1000, # in milliseconds
                                   n_intervals=0
                                  )])


# Multiple components can update everytime interval gets fired.
@app.callback(Output('num_streams', 'figure'),
              [Input('interval-component', 'n_intervals')])
def update_data(n):
    # Get recent data from database
    conn = apsw.Connection("db/lbrynomics.db")
    db = conn.cursor()
    ts = []
    ys = []
    now = time.time()
    begin = get_start_of_today(now)
    for row in db.execute("SELECT time, num_streams FROM measurements\
                            WHERE time >= ?;", (begin, )):
        ts.append(row[0])
        ys.append(row[1])

    ts, ys = np.array(ts), np.array(ys)
    ts = (ts - begin)/3600.0
    data = {}
    if len(ts) <= 1:
        data = {"ts": [1, 2], "ys": [1, 2], "changes": [0]}

    ys = ys - ys[0]
    changes = np.diff(ys)
    conn.close()

    data["ts"] = ts
    data["ys"] = ys
    data["changes"] = changes

    print("Refreshed data.", flush=True)

    figure = {
              "layout": {
                            "title": "Publications on LBRY today",
                            "plot_bgcolor":  "#222222",
                            "paper_bgcolor": "#222222",
                            "xaxis": {"title": "Hours since UTC midnight"},
                            "yaxis": {"title": "Number of publications"},
                            "font": {"color": "#EEEEEE"}
                        },

              "data": [{"x": data["ts"], "y": data["ys"], "type": "line",
                        "mode": "lines+markers",
                        "name": "Cumulative"},
                      {"x": data["ts"][1:], "y": data["changes"],
                       "type": "bar",
                       "name": "5 minute change"}]
            }
    return figure


if __name__ == '__main__':
    app.run_server(host="0.0.0.0")

