# LBRYnomics2
New cleaner backend for LBRYnomics

## Usage

This is a Python3 project.

In order to get all dependencies needed just type
```
pip3 install -r requirements.txt
```

This code is intended to be run on a wallet server. You'll need to edit `config.yaml` to point it to the wallet server's `claims.db` database, and change other directories there to something sensible.

The `secrets.yaml` config file should have the following fields. All but one of these fields are used to transfer the files to a web server that lets you use `scp` to copy files over. The `auth_token` is from your LBRY app.

```
destination: mywebserver.com:public_html/lbrynomics/
user: myusername
password: mypassword
port: 22
auth_token: xyz123abc456
```

To launch LBRYnomics2, run `main.py` with Python 3.

## Data Snapshots

These are published a few times a day to https://keybase.pub/brendonbrewer/lbrynomics.db.zst
That's a zstandard-compressed SQLite3 database file.
 
## License

GNU GPL version 3. See the LICENSE file for details.


(c) 2019, 2020 Brendon J. Brewer.


## Contributors

SK3LA, Electron
