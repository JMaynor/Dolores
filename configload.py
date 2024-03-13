import os

import yaml

if os.name == "nt":
    CONFIG_FILE = "config\\config.yml"
else:
    CONFIG_FILE = "/home/dolores/config/config.yml"
with open(CONFIG_FILE, "r", encoding="utf-8") as c:
    config = yaml.safe_load(c)
