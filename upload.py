import os
import subprocess
import yaml

def backup(secrets_file="secrets.yaml"):
    f = open(secrets_file)
    secrets = yaml.load(f, Loader=yaml.SafeLoader)
    f.close()

    os.system("zstd -19 db/lbrynomics.db -o ./lbrynomics.db.zst")
    cmd = "sshpass -p \"{p}\" scp -P {port} lbrynomics.db.zst {user}@{dest}"\
            .format(p=secrets["password"], user=secrets["user"],
                    dest=secrets["destination"], port=secrets["port"])
    os.system(cmd)
    os.system("rm lbrynomics.db.zst")


def upload(secrets_file="secrets.yaml", with_html_plot=False):
    print("Uploading files...", end="", flush=True)
    os.system("cp plots/*.svg upload")
    os.system("cp json/*.json upload")
    if with_html_plot:
        subprocess.run("cp plots/interactive.html upload/", shell=True)
        #subprocess.run("ls upload/", shell=True)
    else:
        subprocess.run("rm plots/interactive.html upload/interactive.html", shell=True, capture_output=True)

    f = open(secrets_file)
    secrets = yaml.load(f, Loader=yaml.SafeLoader)
    f.close()

    cmd = "sshpass -e scp -P {port} upload/* {user}@{dest}"\
            .format(user=secrets["user"],
                    dest=secrets["destination"], port=secrets["port"])
    env = os.environ.copy()
    env["SSHPASS"] = secrets["password"]
    #import subprocess
    subprocess.Popen(cmd, env=env, shell=True)

#    print(cmd)
#    os.system(cmd)
    print("done.\n", flush=True)

