import yaml

# Load config from config.yaml
f = open("config.yaml")
config = yaml.load(f, Loader=yaml.SafeLoader)
f.close()

claims_db_file = config["claims_db_file"]
interval = config["interval"]
lbrynet_bin = config["lbrynet_bin"]
#backup_dir = config["backup_dir"]

