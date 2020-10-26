# Stations
This software is part of the *Covmatic* project.  
Visit the website https://covmatic.org/ for more documentation and information.

> :warning: **This package is meant to be directly used only by an informed developer audience**  
>  [Non-devs can more easily access the protocols implemented in this package via the Covmatic LocalWebServer GUI](https://github.com/covmatic/localwebserver)  

## Table of Contents
* [Installation](#installation)
* [Robot network configuration](#robot-network-configuration)
* [Usage](#usage)
* [Logging](#logging)
* [Magnet settings](#magnet-settings)

## Installation
> :warning: **This software is still in its beta phase**  
> Every feature may be subject to change without notice

You can [install the Covmatic Stations package via `pip`](https://test.pypi.org/project/covmatic-stations/):
```
<python> -m pip install -i https://test.pypi.org/simple/ covmatic-stations
```
Where `<python>` should be changed for the Python instance you wish to install the LocalWebServer onto. We will be following this convention for all the next instructions. 

## Robot network configuration
See the [`config`](config) folder for robot network configuration protocols. 

## Usage
In the `protocols` directory you can find usage examples.

First, you have to import the station you want to use.
In this example ([`protocols/station_a_technogenetics.py`](protocols/station_a_technogenetics.py)),
we will use the Station A class for the Technogenetics kit that uses custom 4x6 COPAN tube racks.

```
from covmatic_stations.a.technogenetics import StationATechnogenetics24
```

Then, you have to instantiate your own station.
All classes come with a full set of default parameters,
that you can change to suit your needs.
E.g. let's assume you want to change the number of samples to 96.

```
station = StationATechnogenetics24(num_samples=96)
```

You can also specify your language: `'ENG'` (default) or `'ITA'`.
This choice will affect the messages that the internal protocol server sends to the LocalWebServer.
E.g.

```
station = StationATechnogenetics24(
    num_samples=96,
    language="ITA"
)
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
Magnet settings are read from a JSON file in the package.
To override the file path, you can set the environment variable `OT_MAGNET_JSON`
to your custom path (a path on the OT's Raspberry).
If the file was `/home/altern_magnet.json`, you would have to write
```
export OT_MAGNET_JSON=/home/altern_magnet.json
```
To delete the variable you can run
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
from covmatic_stations.b import magnets
h = magnets.height.by_serial["X"]
```


<!---
Copyright (c) 2020 Covmatic.
Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
-->
