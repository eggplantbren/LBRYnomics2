import sqlite3

# Connect to database file
conn = sqlite3.connect("lbrynomics.db")
c = conn.cursor()

# Set pragmas
c.execute("""
PRAGMA journal_mode = WAL;
""")

# Create tables
c.execute("""
CREATE TABLE IF NOT EXISTS measurements
    (id INTEGER PRIMARY KEY,
     time REAL NOT NULL,
     num_channels INTEGER,
     num_streams INTEGER,
     num_supports INTEGER,
     lbc_supports REAL);
""")

conn.close()

