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
* [Copan 48 rack](#copan-48-rack-correction)
* [Magnet settings](#magnet-settings)

## Installation
You can [install the Covmatic Stations package via `pip`](https://pypi.org/project/covmatic-stations/):
```
<python> -m pip install covmatic-stations
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

### Extend stations
If you want to customize your station further than what changing parameters allows, you can create your own station class.
First identify the base stations that you want to customize (e.g. `StationBTechnogenetics`).

You want to create a new class that extends that base class.
The method `body` implements the core of the protocol instructions.
Labware and instrument initialization is done before the body. Cleanup is done after.

To change the protocol procedure, override `body`.

If you want not to load a labware piece (or instrument), identify the corresponding loader method:
it should be tagged by a `@labware_loader` (or `@instrument_loader`) decorator.
> :warning: The method may be implemented by a parent class of the class you are looking at.
> If you don't find the method in the class you are extending, look in the parent classes. 

If you want to load a new labware piece (or instrument), define a corresponding loader method:
it should be decorated by a `@labware_loader` (or `@instrument_loader`) decorator.
The decorators take two arguments
- `index`: labware and instruments are loaded in the order defined by these indices (first all the labware, then all the instruments)
- `name`: the name of the labware or instrument (for debug purposes)

An example of protocol file made by extending a station class could be
```
import logging
from covmatic_stations.b.technogenetics import StationBTechnogenetics


class CustomStation(StationBTechnogenetics)
    # override loader: tempdeck will not be loaded
    def load_tempdeck(self):
        pass
    
    # load a custom labware piece
    @labware_loader(10, "_custom_labware")
        self._custom_labware = self._ctx.load_labware(...)
    
    # override body: redefine the procedure
    def body(self)
        ...

# debug level brings up more log messages, try this when extending a new class
logging.getLogger(CustomStation.__name__).setLevel(logging.DEBUG)
metadata = {'apiLevel': '2.3'}
station = CustomStation(num_samples=96)


def run(ctx):
    return station.run(ctx)
``` 

> :warning: If you are using the LocalWebServer GUI to upload the protocol file
> store this custom file in a different path than the one used for the automatically generated protocol

To upload this custom file using the LocalWebServer GUI:
- **Save** the automatically generated protocol to a file
- **Copy** the custom file to overwrite the automatically generated protocol
- **Upload** the file (press the upload button)
- **Verify** that the uploaded file is the correct one
  - Read the confirmation message: you should read that the expecte file has been uploaded

If the robot's Jupyter server is on, you can directly overwrite the protocol file on the robot via the Jupyter interface.

### Logging
You can adjust the logging level of your station (e.g. to `INFO`) like so

```
import logging
logging.getLogger(StationAP300.__name__).setLevel(logging.INFO)
```

By default, the level is set to `DEBUG`.

## Copan 48 Rack correction
The station A protocols use a custom tube rack.
The rack definition is generated by the corresponding class.
Some fine redefinition may be needed.
You can adjust the definition with a JSON file.
All values in the JSON file are considered multipliers. E.g.
```
{
  "stagger": 1.27,
  "distance_vert": 0.98
}
``` 
This file specifies a `stagger` value 27% bigger than the theoretical value
and a `distance_vert` value 2% smaller than the theoretical value.

If the default value is a tuple, use a list of multipliers. E.g.
```
{
  "global_dimensions": [1, 1.2, 0.9]
}
```

To override the default adjustments,
you can set the environment variable `OT_COPAN_48_CORRECT` to the file path of your
custom JSON.

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
