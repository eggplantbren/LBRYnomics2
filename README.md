# LBRYnomics2

This is a program which runs on a LBRY wallet server. It measures various quantities from both the wallet server's claim database and LBRY Inc's APIs, saving the measurements to its own database. It also generates plots of the history of the quantities it measures, and JSON files containing numbers that can be presented on websites.

## Usage

This is a Python3 project.

In order to get all dependencies needed just type
```
pip3 install -r requirements.txt
```

This code is intended to be run on a wallet server. You'll need to edit `config.yaml` to point it to the wallet server's `claims.db` database, and change other directories there to something sensible.

You'll need to create an additional file `secrets.yaml` with the following fields. All but one of these fields are used to transfer the files to a web server that lets you use `scp` to copy files over. The `auth_token` is from your LBRY app.

```
---
destination: mywebserver.com:public_html/lbrynomics/
user: myusername
password: mypassword
port: 22
auth_token: xyz123abc456
```

To launch LBRYnomics2, run `main.py` with Python 3.

## Outputs

If my instance is running (it usually is, and I intend to keep it running), the outputs at
https://brendonbrewer.com/lbrynomics will be updated every five minutes. These provide the raw information for presentation by other sites such as Electron's https://lbrynomics.com.

A full snapshot of the data is
backed up to https://keybase.pub/brendonbrewer/lbrynomics.db.zst approximately every 6 hours. It is an SQLite3 database which has been compressed with zstandard.
 
## License

GNU GPL version 3. See the LICENSE file for details.


(c) 2019, 2020 Brendon J. Brewer.


## Contributors

SK3LA, Electron
