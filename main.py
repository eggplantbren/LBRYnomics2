import config
import create_db
import measurement
import plotter
import time

# Create the database
create_db.create_db()

# Test for history and estimate it if it's not there
create_db.test_history()

# Enter main loop
while True:

    # Make the measurement
    result = measurement.make_measurement()

    # Make plots
    plotter.make_plots()

    # Get the time and make another measurement in 5 minutes
    wait = config.interval - (time.time() - result["time"])
    if wait < 0.0:
        wait = 0.0
    print("Waiting for {wait} seconds.".format(wait=wait), end="", flush=True)
    time.sleep(wait)
    print("\nDone.\n")

