"""Labware definition for the custom Copan 24x rack.
This file can be
 - imported: e.g. `from copan_24 import Copan24Specs`.
    Labware definition can be accessed with the method Copan24Specs.labware_definition
 - executed with opentrons_simulate or opetrons_execute: e.g. `opentrons_simulate covmatic_stations/a/copan_24.py`
    This file acts as a test protocol for the custom labware.
 - executed with python:  e.g. `python -m covmatic_stations.a.copan_24`.
    This script generates the json file for the custom labware"""
import json
from collections import OrderedDict
from itertools import product, chain
from typing import List, Tuple
from opentrons_shared_data.labware.dev_types import LabwareDefinition
from opentrons.protocol_api import ProtocolContext


class JsonProperty(property):
    _count = 0
    
    def __init__(self, fget=None, fset=None, fdel=None, doc=None, ord=0):
        super(JsonProperty, self).__init__(fget=fget, fset=fset, fdel=fdel, doc=doc)
        self._idx = type(self)._count
        type(self)._count += 1
    
    def __int__(self) -> int:
        return self._idx


json_property = JsonProperty


class Copan24Specs:
    def __init__(self,
                 nrows: int = 4,
                 ncols: int = 6,
                 brand: str = "COPAN",
                 brandId: List[str] = ["330C"],
                 diameter: float = 16.8,
                 distance_vert: float = 17.75,
                 distance_horz: float = 18.75,
                 tube_diameter: float = 16,
                 tube_volume: float = 14000,
                 tube_depth: float = 93,
                 tube_height: float = 10,
                 global_dimensions: Tuple[float, float, float] = (121.35, 79.1, 108),
                 a1_offset: Tuple[float, float] = (11.63, 14),
                 ):
        self.nrows = nrows
        self.ncols = ncols
        self._brand = brand
        self._brandId = brandId
        self._dims = global_dimensions
        self._a1_off = a1_offset
        self._d = diameter
        self._dv = distance_vert
        self._dh = distance_horz
        self._tw = tube_diameter
        self._td = tube_depth
        self._tv = tube_volume
        self._th = tube_height
    
    @property
    def n(self) -> int:
        return self.ncols * self.nrows

    @json_property
    def ordering(self) -> List[List[str]]:
        return [[chr(r + ord("A")) + str(c + 1) for r in range(self.nrows)] for c in range(self.ncols)]

    @json_property
    def brand(self) -> dict:
        return {"brand": self._brand, "brandId": self._brandId}

    @json_property
    def metadata(self) -> dict:
        return {
            "displayName": "COPAN {} Tube Rack 14000 µL".format(self.n),
            "displayCategory": "tubeRack",
            "displayVolumeUnits": "µL",
            "tags": []
        }

    @json_property
    def dimensions(self) -> dict:
        return {
            "xDimension": self._dims[0],
            "yDimension": self._dims[1],
            "zDimension": self._dims[2]
        }
    
    def well(self, r: int, c: int) -> Tuple[str, dict]:
        return chr(ord("A") + r) + str(1 + c), {
            "depth": self._td,
            "totalLiquidVolume": self._tv,
            "shape": "circular",
            "diameter": self._tw,
            "x": self._a1_off[0] + c * self._dh,
            "y": self._dims[1] - self._a1_off[1] - r * self._dv,
            "z": self._th
        }
        
    @json_property
    def wells(self) -> dict:
        return dict(self.well(r, c) for c, r in product(range(self.ncols), range(self.nrows)))
    
    @json_property
    def groups(self) -> List[dict]:
        d = {k: self.metadata[k] for k in ("displayName", "displayCategory")}
        d["wellBottomShape"] = "v"
        return [{
            "metadata": d,
            "brand": self.brand,
            "wells": list(chain.from_iterable(self.ordering)),
        }]

    @json_property
    def parameters(self) -> dict:
        return {
            "format": "irregular",
            "quirks": [],
            "isTiprack": False,
            "isMagneticModuleCompatible": False,
            "loadName": "copan_{}_tuberack_14000ul".format(self.n)
        }

    @json_property
    def namespace(self) -> str:
        return "custom_beta"

    @json_property
    def version(self) -> int:
        return 1

    @json_property
    def schemaVersion(self) -> int:
        return 2

    @json_property
    def cornerOffsetFromSlot(self) -> dict:
        return {
            "x": 0,
            "y": 0,
            "z": 0
        }
    
    def toJSON(self) -> dict:
        return OrderedDict((k, getattr(self, k)) for k in sorted(
            filter(lambda a: isinstance(getattr(type(self), a, None), json_property), dir(self)),
            key=lambda a: int(getattr(type(self), a, 0))
        ))
    
    def labware_definition(self) -> LabwareDefinition:
        return LabwareDefinition(self.toJSON())
    
    def __str__(self) -> str:
        return json.dumps(self.toJSON(), indent=4).replace(r"\u00b5", "\u00b5")
    
    def run_test(self, ctx: ProtocolContext):
        """Test protocol"""
        ctx.comment("Test the custom '{}' rack".format(self.metadata["displayName"]))
        
        rack = ctx.load_labware_from_definition(self.labware_definition(), '2', 'custom tuberack')
        tipracks1000 = [ctx.load_labware('opentrons_96_filtertiprack_1000ul', '1', '1000µl filter tiprack')]
        p1000 = ctx.load_instrument('p1000_single_gen2', 'right', tip_racks=tipracks1000)
        
        p1000.pick_up_tip()
        for w in rack.wells():
            ctx.pause("moving to top of {}".format(w))
            p1000.move_to(w.top())
            ctx.pause("moving to bottom of {} (1 mm high)".format(w))
            p1000.move_to(w.bottom(1))
            p1000.aspirate(5)
            p1000.dispense(5)
        p1000.drop_tip()
        

def run(ctx: ProtocolContext):
    Copan24Specs().run_test(ctx)


metadata = {"apiLevel": "2.3"}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('file', metavar='F', type=str, help='The file path where to save the custom labware JSON')
    args = parser.parse_args()
    with open(args.file, "w") as f:
        f.write(str(Copan24Specs()))


# Copyright (c) 2020 Covmatic.
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
