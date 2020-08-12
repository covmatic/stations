import json
import os
from collections import namedtuple


_env_key = "OT_MAGNET_JSON"
_keys = ["serial", "station", "height"]
_getter_c = namedtuple("getter", list(map("by_{}".format, _keys)))


def __getattr__(name: str):
    if name == "specs":
        fp = os.environ.get(_env_key, os.path.join(os.path.split(__file__)[0], "magnet_heights.json"))
        with open(fp, "r") as f:
            j = json.load(f)
        return j
    
    if name in _keys:
        specs = __getattr__("specs")
        return _getter_c(**{"by_{}".format(k): {s[k]: s[name] for s in specs} for k in _keys})
