import apsw
import config
import datetime
import matplotlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from numba import njit
import numpy as np
import subprocess
import time

# Read-only connection to top channels database
tcdb_conn = apsw.Connection("db/top_channels.db",
                            flags=apsw.SQLITE_OPEN_READONLY)
tcdb = tcdb_conn.cursor()
ldb_conn = apsw.Connection("db/lbrynomics.db",
                           flags=apsw.SQLITE_OPEN_READONLY)
ldb = ldb_conn.cursor()

# Quantiles - actually the MEDIAN
class quantile:
    def __init__(self):
        self.xs = []

    def step(self, x):
        self.xs.append(x)

    def final(self):
        if len(self.xs) == 0:
            return 0.0
        return np.median(self.xs)

    # Under Python 2.3 remove the following line and add
    # factory=classmethod(factory) at the end
    @classmethod
    def factory(cls):
        return cls(), cls.step, cls.final

tcdb_conn.createaggregatefunction("QUANTILE", quantile.factory)


def thin(ts, ys, gap=86400.0):
    assert len(ts) == len(ys)
    thinned_ts, thinned_ys = [ts[0]], [ys[0]]
    for i in range(1, len(ts)):
        if (ts[i] - thinned_ts[-1] >= 0.5*gap) or (i == len(ts) - 1):
            thinned_ts.append(ts[i])
            thinned_ys.append(ys[i])
    return np.array(thinned_ts), np.array(thinned_ys)

def simple_diff(ts, ys):
    assert len(ts) == len(ys)
    midpoints = 0.5*(ts[0:-1] + ts[1:])
    widths = np.diff(ts)
    derivs = np.diff(ys)/widths
    return [midpoints, widths, derivs]



@njit
def moving_average(ys, length=10):
    result = np.empty(len(ys))
    for i in range(len(ys)):
        start = i - length
        if start < 0:
            start = 0
        result[i] = np.mean(ys[start:(i+1)])
    return result

# Load LBRY Social logo
#logo = plt.imread("assets/logo_and_url.svg")

# Configure Matplotlib
#matplotlib.rcParams["figure.dpi"] = 100
matplotlib.rcParams["font.family"] = "Roboto"
plt.rcParams["font.size"] = 16
plt.style.use("dark_background")
plt.rcParams["axes.facecolor"] = "#3c3d3c"
plt.rcParams["savefig.facecolor"] = "#3c3d3c"


#In [4]: import matplotlib.font_manager 
#   ...: flist = matplotlib.font_manager.get_fontconfig_fonts() 
#   ...: names = [matplotlib.font_manager.FontProperties(fname=fname).get_name() 
#   ...: for fname in flist] 
#   ...: print(names)


def annotate_all(mode, subplot=1,):

    # Everyone gets year lines
    # Add vertical lines for new years (approximately)
    for year in range(2017, 2023):
        plt.axvline(mdates.date2num(datetime.date(year, 1, 1)),
                    color="w", alpha=0.5, linewidth=1.5, linestyle="--")

    ylims = plt.gca().get_ylim()
    text_pos = ylims[0] + 0.97*(ylims[1] - ylims[0])
    xlims = plt.gca().get_xlim()
    xwidth = xlims[1] - xlims[0]
    ywidth = ylims[1] - ylims[0]

    if subplot == 1:
        # Timestamp
        now = datetime.datetime.utcnow().replace(microsecond=0)
        stamp = "Produced at " + str(now) + " UTC"
        plt.text(xlims[0] + 0.0*xwidth, ylims[0] - 0.05*ywidth,
                 stamp, color="w", alpha=0.5)

        plt.text(xlims[0] + 0.01*xwidth, ylims[1] - 0.07*ywidth,
                 "(c) https://lbrynomics.com", color="#3490ff")

    # Nikooooo
    if "ytsync" in mode:
        loc = mdates.date2num(datetime.date(2020, 8, 15))
        plt.axvline(loc, color="limegreen", linestyle="--", linewidth=1.5)
        plt.text(loc - 0.020*xwidth,
                 text_pos,
                 "Niko makes a breakthrough",
                 fontsize=14, rotation=90,
                 rotation_mode="anchor", va="top", ha="right")

    # Altonomy
    if mode == "circulating_supply" and subplot == 1:
        loc = mdates.date2num(datetime.date(2020, 6, 22))
        plt.axvline(loc, color="limegreen", linestyle="--", linewidth=1.5)
        plt.text(loc - 0.020*xwidth,
                 text_pos,
                 "Altonomy market-making partnership",
                 fontsize=14, rotation=90,
                 rotation_mode="anchor", va="top", ha="right")

    # Odysee
    if mode in ["num_channels", "num_streams", "num_reposts", "followers",
                "views"]:
        loc = mdates.date2num(datetime.date(2020, 9, 18))
        plt.axvline(loc, color="#e50054", linestyle="--", linewidth=1.5)

        tp = text_pos
        plt.text(loc - 0.020*xwidth,
                 tp,
                 "Odysee.com launched", color="#e50054",
                 fontsize=14, rotation=90, rotation_mode="anchor", va="top", ha="right")
    # MH
    if mode == "num_channels" or mode == "num_streams":
        loc = mdates.date2num(datetime.date(2019, 6, 9))
        plt.axvline(loc, color="limegreen", linestyle="--", linewidth=1.5)

        tp = text_pos
        plt.text(loc - 0.037*xwidth,
                 tp,
                 "@MH video 'Why I Quit\nYouTube\' published",
                 fontsize=14, rotation=90, rotation_mode="anchor", va="top", ha="right")

    # Crypto purge
    if mode == "num_channels" or mode == "num_streams":
        loc = mdates.date2num(datetime.date(2019, 12, 25))
        plt.axvline(loc, color="limegreen", linestyle="--", linewidth=1.5)
        plt.text(loc - 0.037*xwidth,
                 text_pos,
                 "YouTube purges\ncrypto channels",
                 fontsize=14, rotation=90, rotation_mode="anchor", va="top", ha="right")

    # Onboarding
    if mode == "num_channels":
        loc = mdates.date2num(datetime.date(2019, 10, 15))
        plt.axvline(loc, color="limegreen", linestyle="--", linewidth=1.5)
        plt.text(loc - 0.037*xwidth,
                 text_pos,
                 "New users prompted\n to create a channel",
                 fontsize=14, rotation=90, rotation_mode="anchor", va="top", ha="right")

    # Zero lines on some lower panels
    if subplot == 2:
        if mode in ["num_supports", "followers", "views", "lbc_deposits",
                    "lbc_supports", "num_reposts", "ytsync_new_pending",
                    "ytsync_pending_update", "lbc_spread"]:
            plt.axhline(0.0, color="w", linestyle="--", alpha=0.3)

    # Log scales
    if mode == "circulating_supply" and subplot == 2:
        plt.gca().set_yscale("log")
        plt.ylim(bottom=5.0E4, top=2.0E8)


def title(mode, value):
    if type(value) == np.int64:
        value = int(value)
    elif type(value) == np.float64:
        value = float(value)

    num = round(value)

    string = ""
    if mode == "num_channels":
        string += f"Number of channels = {num}"
    if mode == "num_streams":
        string += f"Number of publications = {num}"
    if mode == "lbc_deposits":
        string += f"LBC staked in deposits = {num} LBC"
    if mode == "num_supports":
        string += f"Number of active supports+tips = {num}"
    if mode == "lbc_supports":
        string += f"LBC locked in active supports+tips = {num} LBC"
    if mode == "ytsync_new_pending":
        string += f"New channels in queue to sync = {num}"
    if mode == "ytsync_pending_update":
        string += f"Channels with new videos awaiting sync = {num}"
    if mode == "circulating_supply":
        string += f"Circulating supply = {num} LBC (max supply=1.083202 billion)"
    if mode == "followers":
        string += f"Median followers of top 200 channels = {num}"
    if mode == "views":
        string += f"Median views of top 200 channels = {num}"
    if mode == "num_reposts":
        string += f"Number of reposts = {num}"
    if mode == "lbc_spread":
        string += f"LBC spread = {num} claims."
    if mode == "total_views":
        string += f"Total views of all content = {num}."
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
        string += "New channels in queue to sync"
    if mode == "ytsync_pending_update":
        string += "Channels with new vids awaiting sync"
    if mode == "circulating_supply":
        string += "Circulating LBC supply"
    if mode == "followers":
        string += "Followers"
    if mode == "views":
        string += "Views"
    if mode == "num_reposts":
        string += "Number of reposts"
    if mode == "lbc_spread":
        string += "Number of claims"
    if mode == "total_views":
        string += "Views"
    return string

def set_ylim(mode, subplot=1):
    if mode in ["num_streams", "num_channels", "num_reposts", "total_views"]:
        plt.ylim(bottom=-0.5)
#    if mode == "followers":
#        plt.ylim(bottom=-0.5)
#    if mode == "views":
#        plt.ylim(bottom=-0.5)
    if mode in ["ytsync_new_pending", "ytsync_pending_update"] and\
            subplot==1:
        plt.ylim(bottom=-0.5)
    if mode == "circulating_supply" and subplot==2:
        plt.ylim(bottom=-0.5)


def make_plot(mode, ts=None, ys=None, **kwargs):
    """
    Plot quantity history. ts and ys may be presupplied. If not, it will
    try to get them from the measurements table.
    """

    if ts is None:
        ts, ys = [], []

    if len(ts) == 0:
        for row in ldb.execute(f"SELECT time, {mode} FROM measurements;"):
            if row[1] is not None:
                ts.append(row[0])
                ys.append(row[1])

    # Numpy arrays
    ts = np.array(ts)
    ys = np.array(ys)

    # Truncate
    if "truncate" in kwargs and kwargs["truncate"]:
        now = time.time()
        keep = ts >= now - 90*86400
        ts = ts[keep]
        ys = ys[keep]

    # Thin to daily
    ts, ys = thin(ts, ys)
    mpl_times = mdates.epoch2num(ts)

    # Convert ts to datetimes to facilitate good tick positions
    datetimes = []
    for i in range(len(ts)):
        datetimes.append(datetime.datetime.utcfromtimestamp(ts[i]))

    # Gap in ticks, in months
    tick_gap_months = 3

    # Shorter datasets, use one month
    if (ts[-1] - ts[0]) < 250*86400.0:
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
    elif (ts[-1] - ts[0]) < 50*86400.0:
        ticks = [dt.date() for dt in datetimes]
        ticks = np.unique(ticks[0::3] + [ticks[-1]])
    elif (ts[-1] - ts[0]) < 100*86400.0:
        ticks = [dt.date() for dt in datetimes]
        ticks = np.unique(ticks[0::5] + [ticks[-1]])


    # Compute xlim
    xlim = [mdates.epoch2num(ts[0])  - 1.0,
            mdates.epoch2num(ts[-1]) + 1.0]
    xlim[1] += 0.07*(xlim[1] - xlim[0])

    plt.figure(figsize=(15, 12))
    plt.subplot(2, 1, 1)

    style = "-"
    if "truncate" in kwargs and kwargs["truncate"]:
        style = "o-"

    plt.plot(mpl_times, ys, style, color="w", linewidth=1.5)
    plt.xticks([])
    plt.xlim(xlim)

    plt.ylabel(ylabel(mode), fontsize=16)
    plt.title(title(mode, ys[-1]))
    if "truncate" not in kwargs or not kwargs["truncate"]:
        set_ylim(mode)
    plt.gca().tick_params(labelright=True)

    # Add annotations
    annotate_all(mode)

    # Add logo and tweak its position
    #ax = plt.gca()
    #axins = ax.inset_axes([0.01, 0.80, 0.20, 0.18])
    #axins.imshow(logo)
    #axins.axis("off")

    plt.subplot(2, 1, 2)
    color = "#3490ff"

    midpoints, widths, derivs = simple_diff(ts, ys)
    derivs *= 86400.0
    midpoints = mdates.epoch2num(midpoints)

    plt.plot(midpoints, derivs, style, color=color, label="Raw")
    m = moving_average(derivs)
    if len(m) >= 2:
        plt.plot(midpoints, m, style, color="w",
                    label="10-day moving average")

    # Find 30-day gap if possible
    dist = np.abs(ts - (ts[-1] - 30.0*86400.0))
    index = np.nonzero(dist == min(dist))[0]
    rise = ys[-1] - ys[index]
    run =  ts[-1] - ts[index]
    if run == 0.0:
        run = 1.0
    plt.title("Recent average daily change (last 30 days) = {value}"\
                .format(value=round(float(rise/(run/86400.0)))))

    plt.xticks(mdates.date2num(ticks), ticks, rotation=70)
    plt.xlim(xlim)
    set_ylim(mode, 2)
    plt.ylabel(ylabel(mode) + " daily change", fontsize=16)
    plt.gca().tick_params(labelright=True)
    plt.gcf().align_ylabels()

    # Add annotations
    annotate_all(mode, 2)

    plt.legend()
    fname = f"{mode}"
    if "production" in kwargs and kwargs["production"]:
        fname = "plots/" + fname
    if "truncate" in kwargs and kwargs["truncate"]:
        fname += "_90d"
    fname += ".png"
    plt.savefig(fname.format(mode=mode),
                bbox_inches=matplotlib.transforms.Bbox\
                    (np.array([[0.5, -0.0], [14.5, 11.0]])), dpi=100)
    plt.close("all")
    command = f"convert -strip -resize 1200x943 -colors 256 -depth 8 +dither {fname} png8:{fname}"
    subprocess.run(command, shell=True)
    print(f"    Figure saved to {fname}.")


def make_plots(**kwargs):
    print("Making plots.", flush=True)
    make_plot("num_channels", **kwargs)
    make_plot("num_streams", **kwargs)
    make_plot("lbc_deposits", **kwargs)
    make_plot("num_supports", **kwargs)
    make_plot("lbc_supports", **kwargs)
    make_plot("ytsync_new_pending", **kwargs)
    make_plot("ytsync_pending_update", **kwargs)
    make_plot("circulating_supply", **kwargs)
    make_plot("lbc_spread", **kwargs)

    # Followers data
    query = """
        SELECT time, QUANTILE(followers) f
        FROM measurements m INNER JOIN epochs e ON m.epoch = e.id
        WHERE rank <= 200 AND followers IS NOT NULL
        GROUP BY e.id
        HAVING f NOT NULL
        ORDER BY time ASC;
    """
    ts, ys = [], []
    for row in tcdb.execute(query):
        ts.append(row[0])
        ys.append(row[1])
    make_plot("followers", ts, ys, **kwargs)

    # Views data
    query = """
        SELECT time, QUANTILE(views) v
        FROM measurements m INNER JOIN epochs e ON m.epoch = e.id
        WHERE rank <= 200 AND views IS NOT NULL
        GROUP BY e.id
        HAVING v NOT NULL
        ORDER BY time ASC;
    """
    ts, ys = [], []
    for row in tcdb.execute(query):
        ts.append(row[0])
        ys.append(row[1])
    make_plot("views", ts, ys, **kwargs)

    make_plot("num_reposts", **kwargs)

    # Total views
    tvconn = apsw.Connection("db/total_views.db",
                             flags=apsw.SQLITE_OPEN_READONLY)
    tvdb = tvconn.cursor()
    ts, ys = [], []
    for row in tvdb.execute("SELECT time, total_views FROM measurements;"):
        ts.append(row[0])
        ys.append(row[1])
    make_plot("total_views", ts, ys, **kwargs)
    tvconn.close()


    print("Done.\n")


if __name__ == "__main__":
    make_plots(production=False, truncate=False)
    make_plots(production=False, truncate=True)


