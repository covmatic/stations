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


# Copyright (c) 2020 Covmatic.
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
