import sqlite3



def get_deltas(window):
    """
    Returns the change in the number of streams
    between the last measurement and one a certain time ago.
    """
    conn = sqlite3.connect("db/lbrynomics.db")
    c = conn.cursor()

    # Get most recent measurement
    value1 = c.execute("""SELECT * FROM measurements
                          ORDER BY num_streams DESC LIMIT 1;""").fetchone()
    time1 = value1[1]

    # Target time
    time2 = time1 - window
    value2 = c.execute("""SELECT * FROM measurements
                          WHERE time >= ?
                          ORDER BY time ASC LIMIT 1;""", (time2,)).fetchone()
    conn.close()

    print(value1)
    print(value2)





get_deltas(1000.0)
