import os
import yaml

def backup():
    f = open("secrets.yaml")
    secrets = yaml.load(f, Loader=yaml.SafeLoader)
    f.close()

    os.system("zstd db/lbrynomics.db -o ./lbrynomics.db.zst")
    cmd = "sshpass -p \"{p}\" scp -P {port} lbrynomics.db.zst {user}@{dest}"\
            .format(p=secrets["password"], user=secrets["user"],
                    dest=secrets["destination"], port=secrets["port"])
    os.system(cmd)
    os.system("rm lbrynomics.db.zst")


def upload():
    print("Uploading files.", flush=True)
    os.system("cp plots/* upload")
    os.system("cp json/*.json upload")

    f = open("secrets.yaml")
    secrets = yaml.load(f, Loader=yaml.SafeLoader)
    f.close()

    cmd = "sshpass -p \"{p}\" scp -P {port} upload/* {user}@{dest}"\
            .format(p=secrets["password"], user=secrets["user"],
                    dest=secrets["destination"], port=secrets["port"])
    os.system(cmd)
    print("Done.\n")

