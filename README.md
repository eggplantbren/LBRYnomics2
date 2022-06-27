# LBRYnomics2

This is a program which runs on a LBRY wallet server (it has to be v0.92
which is old, and it has to have extra database indexes added, so 
this code is of historical interest only). Periodically,
it measures various quantities from both the wallet server's `claims.db`
database and LBRY Inc's APIs, saving the measurements to its own 
database. It also generates plots of the history of the quantities it 
measures, and JSON files containing numbers that can be presented on 
websites. These output files are then uploaded to a web server for hosting.

## Usage

This is a Python3 project.
In order to get all dependencies needed just type

```
pip3 install -r requirements.txt
```

Before running LBRYnomics, you'll need to edit `config.yaml` to point it 
to the wallet server's `claims.db` database on your system, and the
`lbrynet` binary as well (which should be running).
You'll need to create an 
additional file `secrets.yaml` with the following fields. All but one of 
these fields are used to transfer the output files to a web 
server that lets you use `scp` to copy files over. The `auth_token` is 
from your LBRY app and gives you access to view and follower counts.

If you do not want to upload the output files to any servers (e.g., if you are
just running it locally for testing purposes), comment out all calls
to `upload.upload` and `upload.backup` which occur in `main.py` and
`top_channels.py`.

```
---
destination: mywebserver.com:public_html/lbrynomics/
user: myusername
password: mypassword
port: 22
auth_token: xyz123abc456
```

To launch LBRYnomics2, run `main.py` with Python 3. The first time you 
do this, I recommand that you suspend your wallet server (make sure all 
`torba-server` processes are closed), launch LBRYnomics2, and then 
re-launch your wallet server. This is because LBRYnomics2 will add some 
new indexes to `claims.db` and it is risky to try doing this while the 
wallet server is running.

## Static databases
If you just want to experiment without having a wallet server running, you can
find a static snapshot of `claims.db` (and `lbrynomics.db`) at
https://brendonbrewer.com/lbrynomics.

## Testing of Plots
If you're working on `plotter.py` (which makes static Matplotlib plots) or 
`plotter2.py` (which makes interactive Plotly plots), you can run these 
independently and the output plots will be saved for your inspection in the
root LBRYnomics2 directory, rather than in the `plots` subdirectory where they
usually go. These plots won't be uploaded either. You can do this whether 
LBRYnomics2 is running or not. If it is running, it won't interfere 
with it.

## Outputs

If my instance is running (it usually is, and I intend to keep it that way),
the outputs at https://brendonbrewer.com/lbrynomics will be 
updated every five minutes, except around 12 noon UTC, when it performs the
top channels calculation which takes longer.
The output files at this location provide the raw information for 
presentation by other sites such as Electron's https://lbrynomics.com.

A full snapshot of the data is backed up to 
https://brendonbrewer.com/lbrynomics/lbrynomics.db.zst every few hours. 
It is an SQLite3 database which has been compressed with zstandard.
 
## License

GNU GPL version 3. See the LICENSE file for details.

(c) 2019, 2020 Brendon J. Brewer.


## Contributors

SK3LA, Electron
