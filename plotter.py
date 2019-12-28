import config
import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from numba import njit
import numpy as np
import sqlite3
import time

@njit
def derivative(ts, ys):
    result = np.empty(len(ys) - 1)
    for i in range(len(result)):
        result[i] = (ys[i+1] - ys[i])/(ts[i+1] - ts[i])
    return result

@njit
def moving_average(ys, length=10):
    result = np.empty(len(ys))
    for i in range(len(ys)):
        start = i - length
        if start < 0:
            start = 0
        result[i] = np.mean(ys[start:(i+1)])
    return result


def annotate_mh(mode):
    if mode == "num_channels" or mode == "num_streams":
        loc = mdates.date2num(datetime.date(2019, 6, 9))
        plt.axvline(loc, color="g", linestyle="--", alpha=0.7)
        plt.text(loc,
                 0.8*plt.gca().get_ylim()[1],
                 "@MH video\n\'Why I Quit YouTube\'\npublished",
                 fontsize=10)



def make_plot(mode):

    # Connect to database file
    conn = sqlite3.connect("db/lbrynomics.db")
    c = conn.cursor()

    # Plot channel history
    ts, ys = [], []
    for row in c.execute("SELECT time, {y} FROM measurements;".format(y=mode)):
        if row[1] is not None:
            ts.append(row[0])
            ys.append(row[1])
    conn.close()

    # Numpy arrays
    ts = np.array(ts)
    ys = np.array(ys)

    # Convert ts to datetimes so as to calculate good tick positions
    datetimes = []
    for i in range(len(ts)):
        datetimes.append(datetime.datetime.utcfromtimestamp(ts[i]))

    # Generate ticks as dates on the first of each quarter
    ticks = [datetimes[0].replace(day=1).date()]
    while True:
        tick = ticks[-1] + datetime.timedelta(1)
        while tick.day != 1 or (tick.month - 1) % 3 != 0:
            tick += datetime.timedelta(1)
        ticks.append(tick)
        if tick > datetimes[-1].date():
            break

    # Compute xlim
    xlim = [mdates.date2num(ticks[0]) - 0.5,
            mdates.date2num(ticks[1]) + 0.5]
    if mdates.epoch2num(ts[0]) < xlim[0]:
        xlim[0] = mdates.epoch2num(ts[0]) - 0.5
    if mdates.epoch2num(ts[-1]) > xlim[1]:
        xlim[1] = mdates.epoch2num(ts[-1]) + 0.5


    # Plotting stuff
    plt.rcParams["font.family"] = "Liberation Sans"
    plt.rcParams["font.size"] = 14
    plt.style.use("dark_background")
    plt.rcParams["axes.facecolor"] = "#3c3d3c"
    plt.rcParams["savefig.facecolor"] = "#3c3d3c"

    plt.figure(figsize=(15, 12))
    plt.subplot(2, 1, 1)

    plt.plot(mdates.epoch2num(ts), ys, "w-", linewidth=1.5)
    plt.xticks([])
    plt.xlim(xlim)

    plt.ylabel("{mode}".format(mode=mode))
    plt.title("Total {mode} = {n}.".format(n=ys[-1], mode=mode))
    plt.ylim(bottom=0.0)
    plt.gca().tick_params(labelright=True)

    # Add vertical lines for new years (approximately)
    for year in range(2017, 2021):
        plt.axvline(mdates.date2num(datetime.date(year, 1, 1)),
                    color="r", alpha=0.8, linestyle="--")

    # Add text about MH's video
    annotate_mh(mode)

    plt.subplot(2, 1, 2)

    # It's ts[1:] because if a claim appears at a certain measurement, it
    # was published BEFORE that.
    color = "#6b95ef"
    thin = int(86400.0/config.interval)
    t = mdates.epoch2num(ts)[0::thin][1:]
    y = derivative(t, ys[0::thin])

    plt.plot(t, y, alpha=0.9, color=color, label="Raw")
    m = moving_average(y)
    if len(m) >= 2:
        plt.plot(t, moving_average(y), alpha=0.9, color="w",
                    label="10-day moving average")

    plt.xticks(mdates.date2num(ticks), ticks, rotation=70)
    plt.xlim(xlim)
    plt.ylim(bottom=0.0)
    plt.ylabel("{mode} daily change".format(mode=mode))
    plt.gca().tick_params(labelright=True)

    annotate_mh(mode)

    plt.legend()
    plt.savefig("plots/{mode}.svg".format(mode=mode), bbox_inches="tight")
    plt.savefig("plots/{mode}.png".format(mode=mode), bbox_inches="tight")
    plt.close("all")
    print("    Figure saved to {mode}.svg and {mode}.png.".format(mode=mode))


def make_plots():
    print("Making plots.", flush=True)
    make_plot("num_channels")
    make_plot("num_streams")
    make_plot("lbc_deposits")
    make_plot("num_supports")
    make_plot("lbc_supports")
    print("Done.\n")

