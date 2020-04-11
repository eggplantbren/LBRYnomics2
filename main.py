import config
import create_db
import databases
import lbrynomics_meta
import measurement
import plotter
import recent
import subprocess
import top_channels
import time
import upload

# Measure the time
started_at = time.time()

# Create the database
create_db.create_db()

# Test for history and estimate it if it's not there
create_db.test_history()

# Enter main loop
k = 0
while True:

    d = (time.time() - started_at)/86400.0
    print(f"This process has been running for {d:.3f} days.", flush=True)

    # Make the measurement
    result = measurement.make_measurement(k)

    # Count recent activity and write to JSON
    recent.count_recent_all(result["time"])

    # Top channels
    top_channels.check_and_run()

    # Data about LBRYnomics itself
    lbrynomics_meta.lbrynomics_meta(result["time"], d)

    # Make plots
    plotter.make_plots()

    # Upload
    upload.upload()
#    upload.upload("secrets2.yaml")

    # Backup db periodically
    if k % 72 == 0:
        print("Backing up DB file...", flush=True)
        upload.backup()
        print("done.\n", flush=True)

    # Get the time and make another measurement in 5 minutes
    wait = config.interval - (time.time() - result["time"])
    if wait < 0.0:
        wait = 0.0
    print("Sleeping for {wait} seconds.".format(wait=wait), end=" ", flush=True)
    time.sleep(wait)
    print("done.\n", flush=True)

    k += 1


databases.close()

