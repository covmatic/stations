from .a import StationA
import json
import os


class StationAP1000(StationA):
    _protocol_description: str = "station A protocol for COPAN 330C samples."
    
    def __init__(
        self,
        air_gap_sample: float = 100,
        main_pipette: str = 'p1000_single_gen2',
        main_tiprack: str = 'opentrons_96_filtertiprack_1000ul',
        main_tiprack_label: str = '1000µl filter tiprack',
        source_headroom_height: float = 6,
        source_racks: str = 'copan_15_tuberack_14000ul',
        source_racks_definition_filepath: str = os.path.join(os.path.split(__file__)[0], "COPAN 15 Tube Rack 14000 µL.json"), 
        **kwargs
    ):
        super(StationAP1000, self).__init__(
            air_gap_sample=air_gap_sample,
            main_pipette=main_pipette,
            main_tiprack=main_tiprack,
            main_tiprack_label=main_tiprack_label,
            source_headroom_height=source_headroom_height,
            source_racks=source_racks,
            source_racks_definition_filepath=source_racks_definition_filepath,
            **kwargs
        )
    
    def _load_source_racks(self):
        if self.jupyter:
            # If it is executed in python, the definition must be loaded from JSON
            with open(self._source_racks_definition_filepath) as labware_file:
                labware_def = json.load(labware_file)
            self._source_racks = [
                self._ctx.load_labware_from_definition(
                    labware_def, slot,
                    'source tuberack ' + str(i + 1)
                ) for i, slot in enumerate(self._source_racks_slots)
            ]
        else:
            # If it is executed on the robot, the definition is loaded through the app
            super(StationAP1000, self)._load_source_racks()

    def transfer_sample(self, source, dest):
        self.logger.debug("transferring from {} to {}".format(source, dest))
        self.pick_up(self._p_main)
        self._p_main.mix(self._mix_repeats, self._mix_volume, source.bottom(self._source_headroom_height))
        self._p_main.transfer(
            self._sample_volume,
            source.bottom(self._source_headroom_height),
            dest.bottom(self._dest_headroom_height),
            air_gap=self._air_gap_sample,
            new_tip='never'
        )
        self._p_main.air_gap(self._air_gap_sample)
        #self._p_main.drop_tip()
        self.drop(self._p_main)


if __name__ == "__main__":
    StationAP1000(num_samples=48, metadata={'apiLevel': '2.3'}).simulate()


# Copyright (c) 2020 Covmatic.
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
