# Copyright 2022 iiPython

import json
try:
    with open("config.json", "r") as f:
        config = json.loads(f.read())

except Exception:
    config = {}
