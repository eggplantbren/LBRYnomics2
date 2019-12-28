import config
import matplotlib.pyplot as plt
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

def make_plot(mode):
    assert mode == "channels" or mode == "streams"

    string = mode
    fname = mode
    if mode == "streams":
        string = "publications"
        fname = "claims"

    # Connect to database file
    conn = sqlite3.connect("db/lbrynomics.db")
    c = conn.cursor()

    # Plot channel history
    ts, ys = [], []
    for row in c.execute("SELECT time, num_channels, num_streams FROM measurements;"):
        ts.append(row[0])
        if mode == "channels":
            ys.append(row[1])
        elif mode == "streams":
            ys.append(row[2])
    conn.close()

    # Convert to numpy arrays
    ts = np.array(ts)
    ys = np.array(ys)

    # Plotting stuff
    plt.rcParams["font.family"] = "Liberation Sans"
    plt.rcParams["font.size"] = 14
    plt.style.use("dark_background")
    plt.rcParams["axes.facecolor"] = "#3c3d3c"
    plt.rcParams["savefig.facecolor"] = "#3c3d3c"

    plt.figure(figsize=(15, 11))
    plt.subplot(2, 1, 1)
    times_in_days = (ts - 1483228800)/86400.0
    days = times_in_days.astype("int64")
    plt.plot(times_in_days, ys, "w-", linewidth=1.5)
    plt.ylabel("Number of {mode}".format(mode=string))
    plt.title("Total number of {mode} = {n}.".format(n=ys[-1], mode=string))
    plt.xlim([0.0, days.max() + 1])
    plt.ylim(bottom=0.0)
    plt.gca().tick_params(labelright=True)

    # Add vertical lines for new years (approximately)
    new_years = np.arange(0, 5)*365.2425
    for year in new_years:
        plt.axvline(year, color="r", alpha=0.8, linestyle="--")

    # Add text about years
    year_names = [2017, 2018, 2019]
    for i in range(len(year_names)):
        year = new_years[i]
        plt.text(year+5.0, 0.95*plt.gca().get_ylim()[1],
                    "{text} begins".format(text=year_names[i]),
                    fontsize=10)

    # Add line and text about MH's video
    plt.axvline(890.0, linestyle="dotted", linewidth=2, color="g")
    plt.text(890.0, 0.2*plt.gca().get_ylim()[1],
            "@MH video\n\'Why I Left YouTube\'\ngoes viral",
            fontsize=10)

    plt.subplot(2, 1, 2)

    # It's ts[1:] because if a claim appears at a certain measurement, it
    # was published BEFORE that.
    color = "#6b95ef"
    thin = int(86400.0/config.interval)
    t = times_in_days[0::thin][1:]
    y = derivative(t, ys[0::thin])

    plt.plot(t, y, alpha=0.9, color=color, label="Raw")
    plt.plot(t, moving_average(y), alpha=0.9, color="w", label="10-day moving average")

    plt.xlim([0.0, days.max() + 1])
    plt.ylim(bottom=0.0)
    plt.xlabel("Time (days since 2017-01-01)")
    plt.ylabel("New {mode} added each day".format(mode=string))
#    plt.title("Recent average rate (last 30 days) = {n} {mode} per day.".\
#                format(n=int(np.sum(ts >= ts[-1] - 30.0*86400.0)/30.0),
#                       mode=string))

    plt.gca().tick_params(labelright=True)

    # Year lines
    for year in new_years:
        plt.axvline(year, color="r", alpha=0.8, linestyle="--")

    # MH line
    plt.axvline(890.0, linestyle="dotted", linewidth=2, color="g")
    plt.legend()

    plt.savefig("plots/{mode}.svg".format(mode=fname), bbox_inches="tight")
    plt.savefig("plots/{mode}.png".format(mode=fname), bbox_inches="tight", dpi=70)
    print("    Figure saved to {mode}.svg and {mode}.png.".format(mode=fname))


def make_plots():
    print("Making plots.", flush=True)
    make_plot("channels")
    make_plot("streams")
    print("Done.\n")

