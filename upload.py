from databases import dbs
import os
import subprocess
import yaml

def backup(secrets_file="secrets.yaml"):
    f = open(secrets_file)
    secrets = yaml.load(f, Loader=yaml.SafeLoader)
    f.close()

    dbs["lbrynomics"].execute("PRAGMA main.wal_checkpoint(FULL);")

    os.system("zstd -19 db/lbrynomics.db -o ./lbrynomics.db.zst")
    cmd = "sshpass -p \"{p}\" scp -P {port} lbrynomics.db.zst {user}@{dest}"\
            .format(p=secrets["password"], user=secrets["user"],
                    dest=secrets["destination"], port=secrets["port"])
    os.system(cmd)
    os.system("rm lbrynomics.db.zst")


def upload(secrets_file="secrets.yaml", with_html_plot=False):

    print("Uploading files...", end="", flush=True)
    os.system("rm upload/*")
    os.system("cp plots/*.svg upload")
    os.system("cp json/*.json upload")
    if with_html_plot:
        os.system("cp plots/*.html upload")

    f = open(secrets_file)
    secrets = yaml.load(f, Loader=yaml.SafeLoader)
    f.close()

    cmd = "sshpass -e scp -P {port} upload/* {user}@{dest}"\
            .format(user=secrets["user"],
                    dest=secrets["destination"], port=secrets["port"])
    env = os.environ.copy()
    env["SSHPASS"] = secrets["password"]
    result = subprocess.run(cmd, env=env, shell=True)

    print("done.\n", flush=True)

