from opentrons.types import Point

from ..utils import MoveWithSpeed, WellWithVolume, mix_bottom_top
from .a import StationA
import json
import os


class StationAP1000(StationA):
    _protocol_description: str = "station A protocol for COPAN 330C samples."
    
    def __init__(
        self,
        deepwell_after_dispense_touch_border: bool = False,
        air_gap_sample: float = 25,
        air_gap_sample_before: float = 25,
        air_gap_rate: float = 800,
        dest_above_liquid_height: float = 15,
        main_pipette: str = 'p1000_single_gen2',
        main_tiprack: str = 'opentrons_96_filtertiprack_1000ul',
        main_tiprack_label: str = '1000µl filter tiprack',
        sample_vertical_speed: float = 50,
        deepwell_vertical_speed: float = 50,
        sample_lateral_air_gap: float = 0,      # Use 0 to disable function
        sample_lateral_top_height: float = 3,
        sample_lateral_x_move: float = 0,
        sample_lateral_y_move: float = 0,
        source_headroom_height: float = 6,
        source_height_start_slow: float = 40,
        source_racks: str = 'copan_15_tuberack_14000ul',
        source_racks_definition_filepath: str = os.path.join(os.path.split(__file__)[0], "COPAN 15 Tube Rack 14000 µL.json"),
        **kwargs
    ):
        """
        @param sample_lateral_air_gap: Lateral air gap for viscuos samples to avoid contamination. Use 0 to disable function
        @param sample_lateral_top_height: height to raise above the top of the source for lateral air gap
        @param sample_lateral_x_move: lateral x movement respect to sample_lateral_top_height for lateral air gap; use None for auto calculation
        @param sample_lateral_y_move: lateral y movement respect to sample_lateral_top_height for lateral air gap; use None for auto calculation
        """
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
        self._deepwell_after_dispense_touch_border = deepwell_after_dispense_touch_border
        self._air_gap_rate = air_gap_rate
        self._air_gap_sample_before = air_gap_sample_before
        self._dest_above_liquid_height = dest_above_liquid_height
        self._sample_vertical_speed = sample_vertical_speed
        self._deepwell_vertical_speed = deepwell_vertical_speed
        self._sample_lateral_air_gap= sample_lateral_air_gap
        self._sample_lateral_top_height= sample_lateral_top_height
        self._sample_lateral_x_move= sample_lateral_x_move
        self._sample_lateral_y_move= sample_lateral_y_move
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
        self._p_main.flow_rate.aspirate = self._air_gap_rate
        self._p_main.flow_rate.dispense = self._air_gap_rate

        self.logger.debug("transferring from {} to {}".format(source, dest))
        self.pick_up(self._p_main)

        # Fake aspirate to avoid pipette going up the first time
        if self._p_main_fake_aspirate:
            self._p_main_fake_aspirate = False
            self._p_main.aspirate(self._air_gap_sample, source.top())
            self._p_main.dispense(self._air_gap_sample, source.top())


        # Aspirating sample
        if self._air_gap_sample_before:
            self._p_main.aspirate(self._air_gap_sample_before, source.top())

        self._p_main.flow_rate.aspirate = self._sample_aspirate
        self._p_main.flow_rate.dispense = self._sample_dispense

        with MoveWithSpeed(self._p_main,
                           from_point=source.bottom(self._source_height_start_slow),
                           to_point=source.bottom(self._source_headroom_height),
                           speed=self._sample_vertical_speed, move_close=False):
            if self._mix_repeats:
                self._p_main.mix(self._mix_repeats, self._mix_volume)
            self._p_main.aspirate(self._sample_volume)

        self._p_main.flow_rate.aspirate = self._air_gap_rate
        self._p_main.flow_rate.dispense = self._air_gap_rate
        self._p_main.air_gap(self._air_gap_sample)

        if self._sample_lateral_air_gap:
            default_side_move = source.diameter or source.length

            self._p_main.move_to(source.top(self._sample_lateral_top_height))
            self._p_main.move_to(source.top(self._sample_lateral_top_height).move(
                Point(x=self._sample_lateral_x_move if self._sample_lateral_x_move is not None else default_side_move,
                      y=self._sample_lateral_y_move if self._sample_lateral_y_move is not None else default_side_move)))
            self._p_main.aspirate(self._sample_lateral_air_gap)

        # Dispensing sample
        dest_with_volume = WellWithVolume(dest,
                                          initial_vol=self._sample_volume + self._lysis_volume if self._lysis_first else 0,
                                          headroom_height=0)
        # dispense_top_point = dest.bottom(dest_with_volume.height + self._dest_above_liquid_height)    # we must not go too high not to contaminate the well
        dispense_top_point = dest.bottom(dest_with_volume.height + self._dest_above_liquid_height)


        # if we will mix, just dispense sample as fast as mixing.
        self._p_main.flow_rate.dispense = self._lysis_rate_mix if self._lys_mix_repeats else self._sample_dispense

        self._p_main.dispense(self._sample_volume + self._air_gap_sample + self._sample_lateral_air_gap,
                              dest.bottom(dest_with_volume.height))

        self._p_main.flow_rate.aspirate = self._lysis_rate_mix
        self._p_main.flow_rate.dispense = self._lysis_rate_mix

        self.transfer_sample_mix(dest, height1=self._dest_headroom_height, height2=dest_with_volume.height)

        self._p_main.flow_rate.aspirate = self._air_gap_rate
        self._p_main.flow_rate.dispense = self._air_gap_rate

        if self._air_gap_sample_before:
            if self._deepwell_after_dispense_touch_border:
                self._p_main.dispense(self._air_gap_sample_before / 2, dest.bottom(dest_with_volume.height))
                self._p_main.move_to(dispense_top_point, speed=self._deepwell_vertical_speed)
                # Moving towards the side
                side_movement = ((dest.length or dest.diameter)/2) - 1.5    # subtracting the tip radius at that height
                self._p_main.move_to(dispense_top_point.move(Point(x=-side_movement)))
                self._p_main.dispense(self._air_gap_sample_before / 2)
            else:
                self._p_main.dispense(self._air_gap_sample_before, dest.bottom(dest_with_volume.height))
        else:
            self._p_main.blow_out(location=dispense_top_point)

        self._p_main.move_to(dispense_top_point, speed=self._deepwell_vertical_speed)
        self._p_main.air_gap(self._air_gap_sample, height=0)

        self.drop(self._p_main)

    def transfer_sample_mix(self, well, height1: float, height2: float):
        mix_bottom_top(
            pip=self._p_main,
            reps=self._lys_mix_repeats,
            vol=self._lys_mix_volume,
            pos=well.bottom,
            bottom=height1,
            top=height2,
            last_dispense_rate=self._lys_mix_last_rate,
            last_mix_volume=self._lys_mix_last_volume
        )


if __name__ == "__main__":
    StationAP1000(num_samples=48, metadata={'apiLevel': '2.3'}).simulate()


# Copyright (c) 2020 Covmatic.
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
