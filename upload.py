import subprocess
import yaml

def upload():
    print("Uploading files.", flush=True)
    subprocess.run("cp plots/* upload", shell=True)
    subprocess.run("cp json/*.json upload", shell=True)
    subprocess.run("cp json/rss.xml upload", shell=True)

    subprocess.run("mv upload/num_streams.svg upload/claims.svg", shell=True)
    subprocess.run("mv upload/num_channels.svg upload/channels.svg", shell=True)

    f = open("secrets.yaml")
    secrets = yaml.load(f, Loader=yaml.SafeLoader)
    f.close()

    cmd = "sshpass -p \"{p}\" scp -P 21098 upload/* {user}@{dest}"\
            .format(p=secrets["password"], user=secrets["user"],
                    dest=secrets["destination"])
    subprocess.run(cmd, shell=True)
    print("Done.\n")

