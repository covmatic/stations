# Introduction

Indexed on [Test PyPi](https://test.pypi.org/project/covid19-system9)

This is the protocol repository for Opentrons COVID-19 System 9 ([site name]).

The protocol files that you can upload to your OT-2s will be kept here.

In order to avoid errors running local protocol simulations add the ./custom_defaults/*.json files to your ~/.opentrons folder.

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
