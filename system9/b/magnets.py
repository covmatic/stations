from functools import partial
import json
import os


def __getattr__(name: str):
    if name == "specs":
        fp = os.path.join(os.path.split(__file__)[0], "magnet_heights.json")
        with open(fp, "r") as f:
            j = json.load(f)
        return j


def height_by_query(key: str, value: str) -> float:
    specs = __getattr__("specs")
    return specs[[s[key] == value for s in specs].index(True)]['height']


height_by_serial = partial(height_by_query, "serial")
height_by_station = partial(height_by_query, "station")
