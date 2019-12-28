import matplotlib.pyplot as plt
import numpy as np
import sqlite3
import time

def make_plots():

    # Connect to database file
    conn = sqlite3.connect("db/lbrynomics.db")
    c = conn.cursor()

    # Plot channel history
    ts, ys = [], []
    for row in c.execute("SELECT time, num_channels FROM measurements;"):
        ts.append(row[0])
        ys.append(row[1])
    conn.close()

    # Convert to numpy arrays
    ts = np.array(ts)
    ys = np.array(ys)

    # Set mode # TODO work with streams as well
    mode = "channels"
    string = mode

    # Plotting stuff
    plt.rcParams["font.family"] = "Liberation Sans"
    plt.rcParams["font.size"] = 14
    plt.style.use("dark_background")
    plt.rcParams["axes.facecolor"] = "#3c3d3c"
    plt.rcParams["savefig.facecolor"] = "#3c3d3c"

    plt.figure(figsize=(15, 11))
#    plt.subplot(2, 1, 1)
    times_in_days = (ts - 1483228800)/86400.0
    days = times_in_days.astype("int64")
    plt.plot(times_in_days, ys, "w-", linewidth=1.5)
    plt.ylabel("Number of {mode}".format(mode=string))
    plt.title("Total number of {mode} = {n}.".format(n=ys[-1], mode=string))
    plt.xlim([0.0, days.max() + 1])
    plt.ylim(bottom=-100)
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

#    plt.subplot(2, 1, 2)
#    print("Here 1")


#    # It's ts[1:] because if a claim appears at a certain measurement, it
#    # was published BEFORE that.
#    color = "#6b95ef"
#    t, y = ts[1:], np.diff(ys)
#    plt.plot(t, y, alpha=0.9, color=color, label="Raw")
#    print("Here 2")


#    # Compute 10-day moving average
#    moving_average = np.zeros(len(y))
#    for i in range(len(moving_average)):
#        subset = y[0:(i+1)]
#        if len(subset) >= 10:
#            subset = y[-10:]
#        moving_average[i] = np.mean(subset)
#    plt.plot(t, moving_average, "w-",
#                label="10-day moving average", linewidth=1.5)
#    print("Here 3")


#    plt.xlim([0.0, days.max() + 1])
#    plt.xlabel("Time (days since 2017-01-01)")
#    plt.ylabel("New {mode} added each day".format(mode=string))
#    subset = y[-31:-1]
#    plt.title("Recent average rate (last 30 days) = {n} {mode} per day.".\
#                format(n=int(np.sum(ts >= ts[-1] - 30.0*86400.0)/30.0),
#                       mode=string))

#    plt.gca().tick_params(labelright=True)
#    # Year lines
#    for year in new_years:
#        plt.axvline(year, color="r", alpha=0.8, linestyle="--")

#    # MH line
#    plt.axvline(890.0, linestyle="dotted", linewidth=2, color="g")
#    plt.legend()

    plt.savefig("{mode}.svg".format(mode=mode), bbox_inches="tight")
    plt.savefig("{mode}.png".format(mode=mode), bbox_inches="tight", dpi=70)
    print("Figure saved to {mode}.svg and {mode}.png.".format(mode=mode))
    plt.show()

