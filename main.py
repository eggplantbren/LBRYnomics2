import config
import create_db
import measurement
import plotter
import recent
import subprocess
import time
import upload

# Create the database
create_db.create_db()

# Test for history and estimate it if it's not there
create_db.test_history()

# Enter main loop
k = 0
while True:

    # Make the measurement
    result = measurement.make_measurement()

    # Count recent activity and write to JSON
    recent.count_recent_all(result["time"])

    # Make plots
    plotter.make_plots()

    # Upload
    upload.upload()

    # Backup db periodically
    print("Backing up DB file and top channels JSON.")
    if k % 250 == 0:
        subprocess.run("zstd db/lbrynomics.db "\
                            + "-o ./lbrynomics.db.zst", shell=True)
        subprocess.run("zstd json/subscriber_counts.json"\
                            + "-o ./subscriber_counts.json.zst", shell=True)
        subprocess.run("mv lbrynomics.db.zst " + config.backup_dir, shell=True)
        subprocess.run("mv subscriber_counts.json.zst " + config.backup_dir, shell=True)
    print("\nDone.")

    # Get the time and make another measurement in 5 minutes
    wait = config.interval - (time.time() - result["time"])
    if wait < 0.0:
        wait = 0.0
    print("Sleeping for {wait} seconds.".format(wait=wait), end="", flush=True)
    time.sleep(wait)
    print("\nDone.\n")

    k += 1

