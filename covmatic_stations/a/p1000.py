from ..utils import MoveWithSpeed, WellWithVolume
from .a import StationA
import json
import os


class StationAP1000(StationA):
    _protocol_description: str = "station A protocol for COPAN 330C samples."
    
    def __init__(
        self,
        air_gap_sample: float = 25,
        dest_above_liquid_height: float = 15,
        main_pipette: str = 'p1000_single_gen2',
        main_tiprack: str = 'opentrons_96_filtertiprack_1000ul',
        main_tiprack_label: str = '1000µl filter tiprack',
        sample_vertical_speed: float = 50,
        deepwell_vertical_speed: float = 50,
        source_headroom_height: float = 6,
        source_height_start_slow: float = 40,
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
        self._dest_above_liquid_height = dest_above_liquid_height
        self._sample_vertical_speed = sample_vertical_speed
        self._deepwell_vertical_speed = deepwell_vertical_speed
        self._source_height_start_slow = source_height_start_slow
        self._p_main_fake_aspirate = True
    
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

        # Fake aspirate to avoid pipette going up the first time
        if self._p_main_fake_aspirate:
            self._p_main_fake_aspirate = False
            self._p_main.aspirate(self._air_gap_sample, source.top())
            self._p_main.dispense(self._air_gap_sample, source.top())

        # Aspirating sample
        with MoveWithSpeed(self._p_main,
                           from_point=source.bottom(self._source_height_start_slow),
                           to_point=source.bottom(self._source_headroom_height),
                           speed=self._sample_vertical_speed, move_close=False):
            if self._mix_repeats:
                self._p_main.mix(self._mix_repeats, self._mix_volume)
            self._p_main.aspirate(self._sample_volume)
        self._p_main.air_gap(self._air_gap_sample)

        # Dispensing sample
        dest_with_volume = WellWithVolume(dest, initial_vol=self._sample_volume, headroom_height=0)
        dispense_top_point = dest.bottom(dest_with_volume.height + self._dest_above_liquid_height)    # we must not go too high not to contaminate the well

        with MoveWithSpeed(self._p_main,
                           from_point=dispense_top_point,
                           to_point= dest.bottom(dest_with_volume.height),
                           speed=self._deepwell_vertical_speed, move_close=False):
            self._p_main.dispense(self._sample_volume + self._air_gap_sample)
        self._ctx.delay(seconds=1)
        self._p_main.blow_out(location=dispense_top_point)
        self._p_main.air_gap(self._air_gap_sample, height=0)

        self.drop(self._p_main)


if __name__ == "__main__":
    StationAP1000(num_samples=48, metadata={'apiLevel': '2.3'}).simulate()


# Copyright (c) 2020 Covmatic.
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
