import subprocess
import yaml

def backup():
    f = open("secrets.yaml")
    secrets = yaml.load(f, Loader=yaml.SafeLoader)
    f.close()

    subprocess.run("zstd db/lbrynomics.db -o ./lbrynomics.db.zst", shell=True)
    cmd = "sshpass -p \"{p}\" scp -P {port} lbrynomics.db.zst {user}@{dest}"\
            .format(p=secrets["password"], user=secrets["user"],
                    dest=secrets["destination"], port=secrets["port"])
    subprocess.run(cmd, shell=True)
#    print(cmd)
    subprocess.run("rm lbrynomics.db.zst", shell=True)


def upload():
    print("Uploading files.", flush=True)
    subprocess.run("cp plots/* upload", shell=True)
    subprocess.run("cp json/*.json upload", shell=True)
    subprocess.run("cp json/rss.xml upload", shell=True)

#    subprocess.run("mv upload/num_streams.svg upload/claims.svg", shell=True)
#    subprocess.run("mv upload/num_channels.svg upload/channels.svg", shell=True)

    f = open("secrets.yaml")
    secrets = yaml.load(f, Loader=yaml.SafeLoader)
    f.close()

    cmd = "sshpass -p \"{p}\" scp -P {port} upload/* {user}@{dest}"\
            .format(p=secrets["password"], user=secrets["user"],
                    dest=secrets["destination"], port=secrets["port"])
    subprocess.run(cmd, shell=True)
    print("Done.\n")

