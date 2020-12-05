import apsw
import os
import subprocess
import yaml

def backup(secrets_file="secrets.yaml"):
    f = open(secrets_file)
    secrets = yaml.load(f, Loader=yaml.SafeLoader)
    f.close()

    ldb_conn = apsw.Connection("db/lbrynomics.db")
    ldb = ldb_conn.cursor()
    ldb.execute("PRAGMA main.wal_checkpoint(FULL);")
    ldb_conn.close()

    os.system("zstd -19 db/lbrynomics.db -o ./lbrynomics.db.zst")
    cmd = "sshpass -e scp -P {port} lbrynomics.db.zst {user}@{dest}"\
            .format(user=secrets["user"],
                    dest=secrets["destination"], port=secrets["port"])
    env = os.environ.copy()
    env["SSHPASS"] = secrets["password"]
    result = subprocess.run(cmd, env=env, shell=True)
    os.system("rm lbrynomics.db.zst")


def upload(secrets_file="secrets.yaml", html_plot=False):

    print("Uploading files...", end="", flush=True)

    if html_plot:
        os.system("cp plots/*.html upload")
    else:
        os.system("cp plots/*.svg upload")
        os.system("cp json/*.json upload")

    f = open(secrets_file)
    secrets = yaml.load(f, Loader=yaml.SafeLoader)
    f.close()

    wildcard = "*"
    if html_plot:
        wildcard += ".html"

    cmd = "sshpass -e scp -C -P {port} upload/{wildcard} {user}@{dest}"\
            .format(user=secrets["user"], wildcard=wildcard,
                    dest=secrets["destination"], port=secrets["port"])
    env = os.environ.copy()
    env["SSHPASS"] = secrets["password"]
    result = subprocess.run(cmd, env=env, shell=True)

    if html_plot:
        os.system("rm upload/*.html")

    print("done.\n", flush=True)

