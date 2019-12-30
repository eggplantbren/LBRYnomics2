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


def annotate_all(mode, subplot=1):

    # Everyone gets year lines
    # Add vertical lines for new years (approximately)
    for year in range(2017, 2021):
        plt.axvline(mdates.date2num(datetime.date(year, 1, 1)),
                    color="r", alpha=0.8, linestyle="--")

    # Text vertical position depends on whether we're in the upper or
    # lower subplot.
    text_pos = 0.05*plt.gca().get_ylim()[1]
    if subplot == 2:
        text_pos = 0.65*plt.gca().get_ylim()[1]

    # MH
    if mode == "num_channels" or mode == "num_streams":
        loc = mdates.date2num(datetime.date(2019, 6, 9))
        plt.axvline(loc, color="g", linestyle="--", alpha=0.7)
        plt.text(loc - 28.0,
                 text_pos,
                 "@MH video 'Why I Quit\nYouTube\' published",
                 fontsize=10, rotation=90)

    # Crypto purge
    if mode == "num_channels" or mode == "num_streams":
        loc = mdates.date2num(datetime.date(2019, 12, 25))
        plt.axvline(loc, color="g", linestyle="--", alpha=0.7)
        plt.text(loc - 28.0,
                 text_pos,
                 "YouTube purges\ncrypto channels",
                 fontsize=10, rotation=90)

    # Onboarding
    if mode == "num_channels":
        loc = mdates.date2num(datetime.date(2019, 10, 15))
        plt.axvline(loc, color="g", linestyle="--", alpha=0.7)
        plt.text(loc - 28.0,
                 text_pos,
                 "New users prompted to\ncreate a channel",
                 fontsize=10, rotation=90)



def title(mode, value):
    string = ""
    if mode == "num_channels":
        string += "Total number of channels = {num}".format(num=value)
    if mode == "num_streams":
        string += "Total number of publications = {num}".format(num=value)
    if mode == "lbc_deposits":
        string += "Total staked in deposits = {lbc:.2f} LBC"\
                .format(lbc=value)
    if mode == "num_supports":
        string += "Total number of active supports+tips = {num}"\
                .format(num=value)
    if mode == "lbc_supports":
        string += "Total locked in active supports+tips = {lbc:.2f} LBC"\
                .format(lbc=value)
    if mode == "ytsync_new_pending":
        string += "Total number of channels in sync queue = {num}"\
                .format(num=value)
    if mode == "ytsync_pending_update":
        string += "Total number of channels pending an update = {num}"\
                .format(num=value)
    return string


def ylabel(mode):
    string = ""
    if mode == "num_channels":
        string += "Number of channels"
    if mode == "num_streams":
        string += "Number of publications"
    if mode == "lbc_deposits":
        string += "LBC staked in deposits"
    if mode == "num_supports":
        string += "Number of active supports+tips"
    if mode == "lbc_supports":
        string += "LBC in active supports+tips"
    if mode == "ytsync_new_pending":
        string += "Number of channels in sync queue"
    if mode == "ytsync_pending_update":
        string += "Number of pending an update"
    return string

def set_ylim(mode):
    if mode == "num_channels" or mode == "num_streams":
        plt.ylim(bottom=0)


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

    # Convert ts to datetimes to facilitate good tick positions
    datetimes = []
    for i in range(len(ts)):
        datetimes.append(datetime.datetime.utcfromtimestamp(ts[i]))

    # Gap in ticks, in months
    tick_gap_months = 3

    # Shorter datasets, use one month
    if (ts[-1] - ts[0]) < 90*86400.0:
        tick_gap_months = 1

    # Generate ticks as dates on the first of each quarter
    # Go back in time
    ticks = [datetimes[0].date()]
    while (ticks[0].month - 1)% tick_gap_months != 0 or ticks[0].day != 1:
        ticks[0] -= datetime.timedelta(1)

    # Go forward in time
    while True:
        tick = ticks[-1] + datetime.timedelta(1)
        while tick.day != 1 or (tick.month - 1) % tick_gap_months != 0:
            tick += datetime.timedelta(1)
        ticks.append(tick)
        if tick > datetimes[-1].date():
            break

    # Handle very short datasets differently
    if (ts[-1] - ts[0]) < 20*86400.0:
        ticks = np.unique([dt.date() for dt in datetimes])

    # Compute xlim
    xlim = [mdates.date2num(ticks[0]) - 0.5,
            mdates.date2num(ticks[-1]) + 0.5]

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

    plt.ylabel(ylabel(mode))
    plt.title(title(mode, ys[-1]))
    set_ylim(mode)
    plt.gca().tick_params(labelright=True)

    # Add annotations
    annotate_all(mode)

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

    # Find 30-day gap if possible
    dist = np.abs(ts - (ts[-1] - 30.0*86400.0))
    index = np.nonzero(dist == min(dist))[0]
    rise = ys[-1] - ys[index]
    run =  ts[-1] - ts[index]
    if run == 0.0:
        run = 1.0
    plt.title("Recent average daily change (last 30 days) = {value}."\
                .format(value=int(rise/(run/86400.0))))

    plt.xticks(mdates.date2num(ticks), ticks, rotation=70)
    plt.xlim(xlim)
    set_ylim(mode)
    plt.ylabel(ylabel(mode) + " daily change")
    plt.gca().tick_params(labelright=True)

    # Add annotations
    annotate_all(mode, 2)

    plt.legend()
    plt.savefig("plots/{mode}.svg".format(mode=mode), bbox_inches="tight")
    plt.close("all")
    print("    Figure saved to {mode}.svg.".format(mode=mode))


def make_plots():
    print("Making plots.", flush=True)
    make_plot("num_channels")
    make_plot("num_streams")
    make_plot("lbc_deposits")
    make_plot("num_supports")
    make_plot("lbc_supports")
    make_plot("ytsync_new_pending")
    make_plot("ytsync_pending_update")
    print("Done.\n")

