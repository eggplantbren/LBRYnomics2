#!/usr/bin/env python

import config
import create_db
import lbrynomics_meta
import measurement
import plotter
import recent
import subprocess
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

    # Data about LBRYnomics itself
    lbrynomics_meta.lbrynomics_meta(result["time"], d)

    # Make plots
    if k%2 == 0:
        plotter.make_plots(production=True, truncate=False)
        plotter.make_plots(production=True, truncate=True)
        upload.upload(include_pngs=True)
    else:
        upload.upload(include_pngs=False)
#    upload.upload("secrets2.yaml")

    # Backup db periodically
#    if k % 36 == 0:
#        print("Backing up DB files...", flush=True)
#        upload.backup()
#        print("done.\n", flush=True)

    # Get the time and make another measurement in 5 minutes
    print("Sleeping for {wait} seconds.".format(wait=config.interval), end=" ", flush=True)
    time.sleep(config.interval)
    print("done.\n", flush=True)

    k += 1


databases.close()

