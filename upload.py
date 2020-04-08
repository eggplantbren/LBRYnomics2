import os
import yaml

def backup(secrets_file="secrets.yaml"):
    f = open(secrets_file)
    secrets = yaml.load(f, Loader=yaml.SafeLoader)
    f.close()

    os.system("zstd db/lbrynomics.db -o ./lbrynomics.db.zst")
    cmd = "sshpass -p \"{p}\" scp -P {port} lbrynomics.db.zst {user}@{dest}"\
            .format(p=secrets["password"], user=secrets["user"],
                    dest=secrets["destination"], port=secrets["port"])
    os.system(cmd)
    os.system("rm lbrynomics.db.zst")


def upload(secrets_file="secrets.yaml"):
    print("Uploading files...", end=" ", flush=True)
    os.system("cp plots/* upload")
    os.system("cp json/*.json upload")

    f = open(secrets_file)
    secrets = yaml.load(f, Loader=yaml.SafeLoader)
    f.close()

    cmd = "sshpass -e scp -P {port} upload/* {user}@{dest}"\
            .format(user=secrets["user"],
                    dest=secrets["destination"], port=secrets["port"])
    env = os.environ.copy()
    env["SSHPASS"] = secrets["password"]
    import subprocess
    subprocess.Popen(cmd, env=env, shell=True)

#    print(cmd)
#    os.system(cmd)
    print("done.\n")

