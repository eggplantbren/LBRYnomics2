import config
import create_db
import measurement
import time

# Create the database
create_db.create_db()

# Enter main loop
while True:

    # Make the measurement
    result = measurement.make_measurement()
    print(result)

    # Get the time and make another measurement in 5 minutes
    wait = config.interval - (time.time() - result["time"])
    if wait < 0.0:
        wait = 0.0
    time.sleep(wait)

