import apsw
import config

db1 = apsw.Connection(config.claims_db_file, flags=apsw.SQLITE_OPEN_READONLY)
db2 = apsw.Connection("db/lbrynomics.db")

# Cursors
dbs = {"claims": db1.cursor(), "lbrynomics": db2.cursor()}

def close():
    db1.close()
    db2.close()

