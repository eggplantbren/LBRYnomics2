"""
Little bar graph SVGs
"""

import apsw
import matplotlib.pyplot as plt
import numpy as np

conn = apsw.Connection("db/top_channels.db", flags=apsw.SQLITE_OPEN_READONLY)
db = conn.cursor()

def get_data(rank):
    """
    Get 8 days of view data for a channel of a given rank.
    """
    views = []
    for row in db.execute("SELECT views FROM measurements WHERE rank = ?\
                           ORDER BY epoch DESC LIMIT 8;",
                          (rank, )):
        if row[0] is None:
            row[0] = None
        views.append(row[0])

    # Reverse order to go forward in time again
    views = views[::-1]
    result = []
    for i in range(len(views)-1):
        if views[i] is None or views[i+1] is None:
            result.append(0)
        else:
            result.append(views[i+1]-views[i])

    return result

def make_svg(rank):
    plt.figure(figsize=(7, 2))
    plt.clf()
    data = get_data(rank)
#    data[2] = -100
    colors = ["g" if data[i] >= 0 else "r" for i in range(len(data))]
    plt.bar(np.arange(len(data)), data, width=1, color=colors)
    plt.axhline(0.0, color="k")
    plt.gca().axis("off")
    filename = f"plots/rank{rank}.svg"
    plt.savefig(filename)
    print(filename)

if __name__ == "__main__":
    for i in range(100):
        make_svg(i+1)

