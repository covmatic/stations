"""Labware definition for the custom Copan 48x rack.
This file can be
 - imported: e.g. `from copan_48 import StaggeredCopan48Specs`.
    Labware definition can be accessed with the method StaggeredCopan48Specs.labware_definition
 - executed with opentrons_simulate or opetrons_execute: e.g. `opentrons_simulate covmatic_stations/a/copan_48.py`
    This file acts as a test protocol for the custom labware.
 - executed with python:  e.g. `python -m covmatic_stations.a.copan_48`.
    This script generates the json file for the custom labware"""
from covmatic_stations.a.copan_24 import Copan24Specs, json_property
from opentrons.protocol_api import ProtocolContext
from typing import Tuple
import inspect
import copy
import os
import json

from .copan_48 import StaggeredCopan48Specs

_a1_offset = (27.5, 12)
_global_dimensions = (260, 177, 118)
_nrows = 8
_ncols = 6


class StaggeredCopan48SalivaSpecs(StaggeredCopan48Specs):
    def __init__(
        self,
        tube_diameter: float = 12,
        tube_volume: float = 5000,
        tube_depth: float = 79,
        tube_height: float = 10,
        stagger: float = 0.33,          # Needed for correction in StaggeredCopan48SalivaSpecsCorrected
        nrows: int = _nrows,            # Needed for correction in StaggeredCopan48SalivaSpecsCorrected
        ncols: int = _ncols,            # Needed for correction in StaggeredCopan48SalivaSpecsCorrected
        global_dimensions=_global_dimensions,           # Needed for correction in StaggeredCopan48SalivaSpecsCorrected
        distance_horz: float = (_global_dimensions[0] - 2 * _a1_offset[0]) / (_ncols - 1),      # Needed for correction
        distance_vert: float = (_global_dimensions[1] - 2 * _a1_offset[1]) / (_nrows - 1),      # Needed for correction
        displacement_horz: float = 6.07,
        **kwargs
    ):
        super(StaggeredCopan48SalivaSpecs, self).__init__(
            tube_diameter=tube_diameter,
            tube_volume=tube_volume,
            tube_depth=tube_depth,
            tube_height=tube_height,
            stagger=stagger,
            ncols=ncols,
            nrows=nrows,
            global_dimensions=global_dimensions,
            distance_horz=distance_horz,
            distance_vert=distance_vert,
            **kwargs
        )
        self._displacement_horz = displacement_horz
    
    @json_property
    def metadata(self) -> dict:
        d = super(StaggeredCopan48SalivaSpecs, self).metadata
        d["displayName"] = "Comedical SCS1380S {} Staggered Tube Rack 5000 uL".format(self.n)
        return d

    @json_property
    def parameters(self) -> dict:
        p = super(StaggeredCopan48SalivaSpecs, self).parameters
        p["loadName"] = "saliva_{}_tuberack_5000ul".format(self.n)
        return p

    def well(self, r: int, c: int) -> Tuple[str, dict]:
        w = super(StaggeredCopan48Specs, self).well(r, c)
        w[1]["x"] += (+1 if r % 2 else -1) * self._displacement_horz
        return w


class StaggeredCopan48SalivaSpecsCorrected(StaggeredCopan48SalivaSpecs):
    def __init__(self, **kwargs):
        remaining_kwargs = copy.deepcopy(kwargs)
        corrected_args = {}
        for k, v in inspect.signature(super(StaggeredCopan48SalivaSpecsCorrected, self).__init__).parameters.items():
            if k in remaining_kwargs:
                remaining_kwargs.pop(k)
                if hasattr(kwargs[k], "__iter__"):
                    corrected_args[k] = tuple(a * d for a, d in zip(kwargs[k], v.default))
                else:
                    corrected_args[k] = kwargs[k] * v.default
        super(StaggeredCopan48SalivaSpecsCorrected, self).__init__(**corrected_args, **remaining_kwargs)


copan_48_correction_env_key = "OT_COPAN_48_CORRECT"
copan_48_correction_file = os.path.join(os.path.dirname(__file__), "copan_48_correction.json")
copan_48_correction_file = os.environ.get(copan_48_correction_env_key, copan_48_correction_file)
with open(copan_48_correction_file, "r") as f:
    copan_48_correction = json.load(f)


copan_48_saliva_corrected_specs = StaggeredCopan48SalivaSpecsCorrected(**copan_48_correction)


def run(ctx: ProtocolContext):
    StaggeredCopan48SalivaSpecsCorrected().run_test(ctx)


metadata = {"apiLevel": "2.3"}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('file', metavar='F', type=str, help='The file path where to save the custom labware JSON')
    args = parser.parse_args()
    with open(args.file, "w") as f:
        f.write(str(copan_48_saliva_corrected_specs))


# Copyright (c) 2020 Covmatic.
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
