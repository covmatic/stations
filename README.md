[![Build status](https://github.com/OpenSourceCovidTesting/covid19-system-9_PRIVATE/workflows/package/badge.svg?branch=master)](https://github.com/OpenSourceCovidTesting/covid19-system-9_PRIVATE/actions?query=workflow%3Apackage)

# Introduction

Indexed on [Test PyPi](https://test.pypi.org/project/covid19-system9)

This is the protocol repository for Opentrons COVID-19 System 9 ([site name]).

The protocol files that you can upload to your OT-2s will be kept here.

In order to avoid errors running local protocol simulations add the ./custom_defaults/*.json files to your ~/.opentrons folder.

# Utilities

In the `utilities` directory you can find helpful protocols for the setup of the robots.

 - `update.py` update (or install) the `covid19-system9` package on the robot

## Config

In the `utilities/config` directory you can find python scripts for generating setup protocols.

 - `hostame_ip.py` set the robot name, the hostname, the DNS, the NTP server and a static ip for the robot

# Usage

In the `protocols` directory you can find examples for using the `covid19-system9` protocols.

First, you have to import the station you want to use. In this example (`protocols/station_a_p300.py`) we will use the Station A loaded with 300uL tips, that can be used for BPGenomics samples.

```
from system9.a.p300 import StationAP300
```

Then, you have to instantiate your own station. All our classes come with a full set of default parameters, that you can change to suit your needs. E.g. let's assume you want to change the number of samples to 48.

```
station = StationAP300(num_samples=48)
```

You also have to define the metadata (at least the API level) as usual

```
metadata = {'apiLevel': '2.3'}
```

Finally, the definition of the `run` function becomes trivial

```
def run(ctx):
    return station.run(ctx)
```

## Logging
You can adjust the logging level of your station (e.g. to `INFO`) like so

```
import logging
logging.getLogger(StationAP300.__name__).setLevel(logging.INFO)
```

By default, the level is set to `DEBUG`.

## Magnet Settings
Magnet settings are read from a JSON file in the package. To override the file path, you can set the environment variable `OT_MAGNET_JSON` to your custom path (a path on the OT's Raspberry). If the file is `/home/altern_magnet.json`, you would write
```
export OT_MAGNET_JSON=/home/altern_magnet.json
```
To delete the variable you would write
```
unset OT_MAGNET_JSON
```
The JSON file should be an array of objects, each of which has the fields `serial`, `station` and `height`. E.g.
```
[
  {
	"serial": "X",
	"station": "B1",
	"height": 6.20
  },
  {
	"serial": "Y",
	"station": "B2",
	"height": 6.20
  }
]
```

To inspect a field of a magnet, use the following pattern `magnets.<field>.by_<key>["keyvalue"]`. E.g. to get the height of the magnet whose serial is `X` you would write
```
from system9.b import magnets
h = magnets.height.by_serial["X"]
```


<!---
Copyright (c) 2020 Covmatic.
Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
-->
