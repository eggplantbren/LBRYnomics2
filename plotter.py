import apsw
import config
from databases import dbs
import datetime
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from numba import njit
import numpy as np
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

# Load LBRY Social logo
logo = plt.imread("assets/logo_and_url.png")
matplotlib.rcParams["figure.dpi"] = 500



def annotate_all(mode, subplot=1):

    # Everyone gets year lines
    # Add vertical lines for new years (approximately)
    for year in range(2017, 2021):
        plt.axvline(mdates.date2num(datetime.date(year, 1, 1)),
                    color="r", linewidth=1.5, linestyle="--")

    # Text vertical position depends on whether we're in the upper or
    # lower subplot.
    text_pos = 0.04*plt.gca().get_ylim()[1]
    if subplot == 2:
        text_pos = 0.55*plt.gca().get_ylim()[1]

    # MH
    if mode == "num_channels" or mode == "num_streams":
        loc = mdates.date2num(datetime.date(2019, 6, 9))
        plt.axvline(loc, color="limegreen", linestyle="--", linewidth=1.5)
        if mode == "num_streams":
            tp = 0.55*plt.gca().get_ylim()[1]
        else:
            tp = text_pos
        plt.text(loc - 40.0,
                 tp,
                 "@MH video 'Why I Quit\nYouTube\' published",
                 fontsize=12, rotation=90)

    # Crypto purge
    if mode == "num_channels" or mode == "num_streams":
        loc = mdates.date2num(datetime.date(2019, 12, 25))
        plt.axvline(loc, color="limegreen", linestyle="--", linewidth=1.5)
        plt.text(loc - 40.0,
                 text_pos,
                 "YouTube purges\ncrypto channels",
                 fontsize=12, rotation=90)

    # Onboarding
    if mode == "num_channels":
        loc = mdates.date2num(datetime.date(2019, 10, 15))
        plt.axvline(loc, color="limegreen", linestyle="--", linewidth=1.5)
        plt.text(loc - 40.0,
                 text_pos,
                 "New users prompted to\ncreate a channel",
                 fontsize=12, rotation=90)



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
        string += "New channels in queue to sync = {num}"\
                .format(num=value)
    if mode == "ytsync_pending_update":
        string += "Channels with new videos awaiting sync = {num}"\
                .format(num=value)
    if mode == "circulating_supply":
        string += "Circulating supply = {lbc:.2f} LBC".format(lbc=value)
    if mode == "followers":
        string += f"Average followers of top 200 channels = {value:.1f}"
    if mode == "num_reposts":
        string += "Total number of reposts = {num}"\
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
        string += "New channels in queue to sync"
    if mode == "ytsync_pending_update":
        string += "Channels with new videos awaiting sync"
    if mode == "circulating_supply":
        string += "Circulating LBC supply"
    if mode == "followers":
        string += "Avg. followers of top 200 channels"
    if mode == "num_reposts":
        string += "Total number of reposts"
    return string

def set_ylim(mode):
    if mode == "num_channels" or mode == "num_streams":
        plt.ylim(bottom=0)


def make_plot(mode, production=True, ts=None, ys=None):
    """
    Plot quantity history. ts and ys may be presupplied. If not, it will
    try to get them from the measurements table.
    """

    if ts is None:
        ts, ys = [], []

    if len(ts) == 0:
        for row in dbs["lbrynomics"].execute(f"SELECT time, {mode} FROM measurements;"):
            if row[1] is not None:
                ts.append(row[0])
                ys.append(row[1])

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
    xlim = [mdates.date2num(ticks[0]) - 1.0,
            mdates.date2num(ticks[-1]) + 1.0]

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

    # Add logo and tweak its position
    from mpl_toolkits.axes_grid1.inset_locator import inset_axes
    ax = plt.gca()
    ins = inset_axes(ax, width="100%", height="100%",
                       bbox_to_anchor=(0.01, 0.60, 0.16, 0.35),
                       bbox_transform=ax.transAxes,
                       borderpad=0)
    ins.imshow(logo)
    ins.axis("off")

    plt.subplot(2, 1, 2)

    # It's ts[1:] because if a claim appears at a certain measurement, it
    # was published BEFORE that.
    color = "#3490ff"
    thin = 1
    if len(ts) >= 2:
        interval = np.mean(np.diff(ts))
        thin = int(86400.0/interval)
        thin = max(thin, 1)
        print(interval, thin)

    t = mdates.epoch2num(ts[0::thin])
    y = derivative(t, ys[0::thin])

    plt.plot(t[1:], y, color=color, label="Raw")
    m = moving_average(y)
    if len(m) >= 2:
        plt.plot(t[1:], m, color="w",
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
    fname = "{mode}.svg"
    if production:
        fname = "plots/" + fname
    plt.savefig(fname.format(mode=mode), bbox_inches="tight")
    plt.close("all")
    print("    Figure saved to {mode}.svg.".format(mode=mode))


    # Make bokeh plot
#    if mode == "num_streams":
#        bokeh_plot(ts, ys)


def make_plots(production=True):
    print("Making plots.", flush=True)
    make_plot("num_channels", production)
    make_plot("num_streams", production)
    make_plot("lbc_deposits", production)
    make_plot("num_supports", production)
    make_plot("lbc_supports", production)
    make_plot("ytsync_new_pending", production)
    make_plot("ytsync_pending_update", production)
    make_plot("circulating_supply", production)


    # Followers data
    query = """
    SELECT time, AVG(num_followers) FROM channel_measurements INNER JOIN epochs
            ON epochs.id = channel_measurements.epoch
            WHERE rank <= 200
            GROUP BY channel_measurements.epoch;
    """
    ts, ys = [], []
    for row in dbs["lbrynomics"].execute(query):
        ts.append(row[0])
        ys.append(row[1])
    make_plot("followers", production, ts, ys)

    make_plot("num_reposts", production)

    print("Done.\n")


def bokeh_plot(ts, ys):
    """
    Very experimental.
    """
    from bokeh.plotting import figure, output_file, save

    output_file("streams.html")

    p = figure(plot_width=1200, plot_height=400, x_axis_type="datetime",
               x_axis_label="Time",
               y_axis_label="Number of publications")

    # Convert times to datetimes
    dts = [datetime.datetime.utcfromtimestamp(t) for t in ts]

    # Add a line renderer
    line = p.line(dts, ys, line_width=2)

    # Set background and line colors
    p.background_fill_color = "#3c3d3c"
    line.glyph.line_color = "#286dc1"

    # Make grid less intense
    p.xgrid.grid_line_alpha = 0.2
    p.ygrid.grid_line_alpha = 0.2
    p.xgrid.grid_line_dash = [6, 4]
    p.ygrid.grid_line_dash = [6, 4]


    save(p)

if __name__ == "__main__":
    make_plots(production=False)


