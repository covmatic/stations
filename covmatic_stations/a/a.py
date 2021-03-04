from ..station import Station, labware_loader, instrument_loader
from ..geometry import LysisTube
from ..utils import mix_bottom_top
from itertools import chain, islice, repeat
import math
import logging
from typing import Optional, Tuple


class StationA(Station):
    def __init__(
            self,
            air_gap_dest_multi: float = 5,
            air_gap_sample: float = 20,
            air_gap_lys: float = 10,
            dest_headroom_height: float = 2,
            dest_top_height: float = 5,
            dest_multi_headroom_height: float = 2,
            drop_loc_l: float = -10,
            drop_loc_r: float = 30,
            drop_threshold: int = 296,
            hover_height: float = -2,
            ic_capacity: float = 180,
            ic_lys_headroom: float = 1.1,
            ic_headroom_bottom: float = 2,
            ic_mix_repeats: int = 5,
            ic_mix_volume: float = 20,
            iec_volume: float = 19,
            internal_control_idx_th: int = 48,
            jupyter: bool = True,
            logger: Optional[logging.getLoggerClass()] = None,
            lysis_cone_height: float = 16,
            lysis_first: bool = False,
            lysis_headroom_height: float = 4,
            lysis_rate_aspirate: float = 100,
            lysis_rate_dispense: float = 100,
            lysis_volume: float = 160,
            lys_mix_repeats: int = 10,
            lys_mix_volume: float = 100,
            main_pipette: str = 'p300_single_gen2',
            main_tiprack: str = 'opentrons_96_tiprack_300ul',
            main_tiprack_label: str = '200ul filter tiprack',
            max_speeds_a: float = 20,
            metadata: dict = None,
            mix_repeats: int = 3,
            mix_volume: float = 150,
            num_samples: int = 96,
            positive_control_well: str = 'A10',
            sample_aspirate: float = 30,
            sample_blow_out: float = 300,
            sample_dispense: float = 30,
            samples_per_col: int = 8,
            sample_volume: float = 200,
            source_headroom_height: float = 8,
            source_position_top: float = -10,
            source_top_height: float = 10,
            source_racks: str = 'opentrons_24_tuberack_nest_1.5ml_screwcap',
            source_racks_definition_filepath: str = "",
            source_racks_slots: Tuple[str, ...] = ('2', '3', '5', '6'),
            tempdeck_temp: float = 4,
            tempdeck_bool: bool = True,
            tipracks_slots: Tuple[str, ...] = ('8', '9', '11'),
            tipracks_slots_20: Tuple[str, ...] = ('7',),
            **kwargs
    ):
        """ Build a :py:class:`.StationA`.
        :param air_gap_dest_multi: air gap for destination tube (multi) in uL
        :param air_gap_sample: air gap for sample transfer in uL
        :param dest_headroom_height: headroom always to keep from the bottom of the destination tube in mm
        :param dest_top_height: top height from the bottom of the destination tube in mm when mixing
        :param dest_multi_headroom_height: headroom always to keep from the bottom of the destination tube (multi) in mm
        :param drop_loc_l: offset for dropping to the left side (should be positive) in mm
        :param drop_loc_r: offset for dropping to the right side (should be negative) in mm
        :param drop_threshold: the amount of dropped tips after which the run is paused for emptying the trash
        :param hover_height: height from the top at which to hover (should be negative) in mm
        :param ic_capacity: capacity of the internal control tube
        :param ic_lys_headroom: headroom for the internal control and lysis tube (multiplier)
        :param ic_headroom_bottom: headroom always to keep from the bottom of the internal control tube in mm
        :param ic_mix_repeats: number of repetitions during mixing the internal control
        :param ic_mix_volume: volume aspirated for mixing the internal control in uL
        :param iec_volume: The volume of lysis buffer to use per sample in uL
        :param internal_control_idx_th: internal control index threshold for choosing the strip
        :param logger: logger object. If not specified, the default logger is used that logs through the ProtocolContext comment method
        :param lysis_cone_height: height of he conic bottom of the lysis buffer tube in mm
        :param lysis_first: whether to transfer the lysis buffer first or else the sample first
        :param lysis_headroom_height: headroom always to keep from the bottom of the lysis buffer tube in mm
        :param lysis_rate_aspirate: P300 aspiration flow rate when aspirating lysis buffer in uL/s
        :param lysis_rate_dispense: P300 dispensation flow rate when dispensing lysis buffer in uL/s
        :param lysis_volume: The volume of lysis buffer to use per sample in uL
        :param lys_mix_repeats: number of repetitions during mixing the lysis buffer
        :param lys_mix_volume: volume aspirated for mixing the lysis buffer in uL
        :param main_pipette: type of the main pipette
        :param main_tiprack: type of the main tiprack
        :param main_tiprack_label: label of the main tiprack
        :param mix_repeats: number of repetitions during mixing
        :param mix_volume: volume aspirated for mixing in uL
        :param max_speeds_a: max speed for sample transfer
        :param metadata: protocol metadata
        :param num_samples: The number of samples that will be loaded on the station A
        :param positive_control_well: Position of the positive control well
        :param sample_aspirate: P300 samples aspiration flow rate in uL/s
        :param sample_blow_out: P300 samples blow out flow rate in uL/s
        :param sample_dispense: P300 samples dispensation flow rate in uL/s
        :param samples_per_col: The number of samples in a column of the destination plate
        :param sample_volume: The volume of a sample in uL
        :param source_headroom_height: headroom always to keep from the bottom of the source tube in mm
        :param source_position_top: height from the top of the source tube in mm (should be negative)
        :param source_top_height: top height from the bottom of the source tube in mm when mixing
        :param source_racks: source racks to load
        :param source_racks_definition_filepath: filepath for source racks definitions
        :param source_racks_slots: slots where source racks are installed
        :param tempdeck_temp: tempdeck temperature in Celsius degrees
        :param tipracks_slots: Slots where the tipracks are positioned
        :param tipracks_slots_20: Slots where the tipracks (20 uL) are positioned
        :param jupyter: Specify whether the protocol is run on Jupyter (or Python) instead of the robot
        """
        super(StationA, self).__init__(
            drop_loc_l=drop_loc_l,
            drop_loc_r=drop_loc_r,
            drop_threshold=drop_threshold,
            jupyter=jupyter,
            logger=logger,
            metadata=metadata,
            num_samples=num_samples,
            samples_per_col=samples_per_col,
            **kwargs
        )
        self._air_gap_dest_multi = air_gap_dest_multi
        self._air_gap_sample = air_gap_sample
        self._air_gap_lys = air_gap_lys
        self._dest_headroom_height = dest_headroom_height
        self._dest_multi_headroom_height = dest_multi_headroom_height
        self._dest_top_height = dest_top_height
        self._hover_height = hover_height
        self._ic_capacity = ic_capacity
        self._ic_headroom_bottom = ic_headroom_bottom
        self._ic_lys_headroom = ic_lys_headroom
        self._ic_mix_repeats = ic_mix_repeats
        self._ic_mix_volume = ic_mix_volume
        self._iec_volume = iec_volume
        self._internal_control_idx_th = internal_control_idx_th
        self._lysis_cone_height = lysis_cone_height
        self._lysis_first = lysis_first
        self._lysis_headroom_height = lysis_headroom_height
        self._lysis_rate_aspirate = lysis_rate_aspirate
        self._lysis_rate_dispense = lysis_rate_dispense
        self._lysis_volume = lysis_volume
        self._lys_mix_repeats = lys_mix_repeats
        self._lys_mix_volume = lys_mix_volume
        self._main_pipette = main_pipette
        self._main_tiprack = main_tiprack
        self._main_tiprack_label = main_tiprack_label
        self._max_speeds_a = max_speeds_a
        self._mix_repeats = mix_repeats
        self._mix_volume = mix_volume
        self._positive_control_well = positive_control_well
        self._sample_aspirate = sample_aspirate
        self._sample_blow_out = sample_blow_out
        self._sample_dispense = sample_dispense
        self._sample_volume = sample_volume
        self._source_headroom_height = source_headroom_height
        self._source_position_top = source_position_top
        self._source_racks = source_racks
        self._source_racks_definition_filepath = source_racks_definition_filepath
        self._source_racks_slots = source_racks_slots
        self._source_top_height = source_top_height
        self._tempdeck_temp = tempdeck_temp
        self._tempdeck_bool = tempdeck_bool
        self._tipracks_slots = tipracks_slots
        self._tipracks_slots_20 = tipracks_slots_20

    @labware_loader(0, "_tempdeck")
    def load_tempdeck(self):
        if self._tempdeck_bool:
            self._tempdeck = self._ctx.load_module('Temperature Module Gen2', '4')
            if self._tempdeck_temp is not None:
                self._tempdeck.set_temperature(self._tempdeck_temp)
        else:
            pass

    @property
    def chilled_tubeblock_content(self) -> str:
        return self.get_msg_format("chilled tubeblock content", self.num_ic_strips, "{}")

    @labware_loader(0.1, "_strips_block")
    def load_strips_block(self):
        if self._tempdeck_bool:
            self._strips_block = self._tempdeck.load_labware(
                'opentrons_96_aluminumblock_generic_pcr_strip_200ul',
                "chilled tubeblock for {}".format(self.chilled_tubeblock_content.format(""))
            )
        else:
            self._strips_block = self._ctx.load_labware('opentrons_96_aluminumblock_generic_pcr_strip_200ul', '4',
                                                        "chilled tubeblock for {}".format(
                                                            self.chilled_tubeblock_content.format("")))

        self.logger.info("{} {}".format(
            type(self).get_message("using", self._language),
            self.chilled_tubeblock_content.format(self.get_msg_format("chilled tubeblock content with",
                                                                      self.cols_per_strip * self._iec_volume * self._ic_lys_headroom))
        ))

    def _load_source_racks(self):
        self._source_racks = [
            self._ctx.load_labware(
                self._source_racks, slot,
                'source tuberack ' + str(i + 1)
            ) for i, slot in enumerate(self._source_racks_slots)
        ]

    @labware_loader(1, "_source_racks")
    def load_source_racks(self):
        self.logger.debug("using source racks '{}'".format(self._source_racks))
        self._load_source_racks()

    @labware_loader(2, "_dest_plate")
    def load_dest_plate(self):
        self._dest_plate = self._ctx.load_labware(
            'nest_96_wellplate_2ml_deep', '1', '96-deepwell sample plate'
        )

    _lys_buf_name: str = '50ml tuberack for lysis buffer'

    @labware_loader(3, "_lys_buff")
    def load_lys_buf(self):
        self._lys_buff = self._ctx.load_labware(
            'opentrons_6_tuberack_falcon_50ml_conical', '7',
            self._lys_buf_name,
        ).wells()[0]

    @labware_loader(4, "_tipracks_main")
    def load_tipracks_main(self):
        self._tipracks_main = [
            self._ctx.load_labware(self._main_tiprack, slot, self._main_tiprack_label)
            for slot in self._tipracks_slots
        ]
        self.logger.debug("main tipracks: {}".format(", ".join(map(str, self._tipracks_main))))

    @labware_loader(5, "_tipracks20")
    def load_tipracks20(self):
        self._tipracks20 = [
            self._ctx.load_labware('opentrons_96_filtertiprack_20ul', slot, '20ul filter tiprack')
            for slot in self._tipracks_slots_20
        ]

    @instrument_loader(0, "_m20")
    def load_m20(self):
        self._m20 = self._ctx.load_instrument('p20_multi_gen2', 'left', tip_racks=self._tipracks20)

    @instrument_loader(1, "_p_main")
    def load_p_main(self):
        self._p_main = self._ctx.load_instrument(self._main_pipette, 'right', tip_racks=self._tipracks_main)
        self._p_main.flow_rate.blow_out = self._sample_blow_out
        self.logger.debug("main pipette: {}".format(self._p_main))

    @property
    def num_ic_strips(self) -> int:
        return math.ceil(self._iec_volume * self.num_cols * self._ic_lys_headroom / self._ic_capacity)

    @property
    def cols_per_strip(self) -> int:
        return math.ceil(self.num_cols / self.num_ic_strips)

    @property
    def initlial_volume_lys(self) -> float:
        return len(list(self.non_control_positions(repeat(None)))) * self._lysis_volume * self._ic_lys_headroom

    def setup_samples(self):
        self._sources = list(
            islice(chain.from_iterable(rack.wells() for rack in self._source_racks), self._num_samples))
        self._dests_single = self._dest_plate.wells()[:self._num_samples]
        self._dests_multi = self._dest_plate.rows()[0][:self.num_cols]
        self.logger.debug("positive control in {} of destination rack".format(self._positive_control_well))

    def setup_lys_tube(self):
        self._lysis_tube = LysisTube(self._lys_buff.diameter / 2, self._lysis_cone_height)
        self.logger.debug("%s", self._lysis_tube)
        self._lysis_tube.height = self._lysis_headroom_height
        self._lysis_tube.fill(self.initlial_volume_lys)
        self._lysis_tube.height += self._ic_lys_headroom
        self.logger.info(self.msg_format("lysis geometry", math.ceil(self._lysis_tube.volume), self._lysis_tube.height))
        self._lysis_tube.height -= self._ic_lys_headroom

    def transfer_sample(self, source, dest):
        self.logger.debug("transferring from {} to {}".format(source, dest))
        self.pick_up(self._p_main)

        self._p_main.move_to(source.top(self._source_position_top))
        self._ctx.max_speeds['A'] = self._max_speeds_a

        # Mix by aspirating and dispensing at different heights
        mix_bottom_top(
            self._p_main, self._mix_repeats, self._mix_volume,
            source.bottom, self._source_headroom_height, self._source_top_height
        )
        self._p_main.aspirate(self._sample_volume, source.bottom(self._source_headroom_height))

        # Wait to be sure the sample is aspirated
        self._ctx.delay(1)
        self._p_main.move_to(source.top(self._source_position_top))
        self._ctx.max_speeds['A'] = None
        self._p_main.air_gap(self._air_gap_sample)

        self._p_main.dispense(self._air_gap_sample, dest.top(self._hover_height))
        self._p_main.dispense(self._sample_volume, dest.bottom(self._dest_top_height))

        if self._lysis_first:
            self._p_main.flow_rate.aspirate = self._lysis_rate_aspirate
            self._p_main.flow_rate.dispense = self._lysis_rate_dispense

            # Mix with lysis buffer
            mix_bottom_top(
                self._p_main, self._lys_mix_repeats, self._lys_mix_volume,
                dest.bottom, self._dest_headroom_height, self._dest_top_height
            )

            self._p_main.flow_rate.aspirate = self._sample_aspirate
            self._p_main.flow_rate.dispense = self._sample_dispense

        self._p_main.air_gap(self._air_gap_sample)
        self.drop(self._p_main)

    def is_positive_control_well(self, dest) -> bool:
        return dest == self._dest_plate[self._positive_control_well]

    def non_control_positions(self, sources=None, dests=None):
        """Returns the iterator for the source/dest couples,
        excluding the couple where the destination is meant for the positive control.
        Sources and dests default to self._sources and self._dests"""
        sources = sources or self._sources
        dests = dests or self._dests_single
        return filter(lambda t: not self.is_positive_control_well(t[1]), zip(sources, dests))

    def non_control_dests(self, dests=None):
        dests = dests or self._dests_single
        return filter(lambda t: not self.is_positive_control_well(t), dests)

    def transfer_samples(self):
        self._p_main.flow_rate.aspirate = self._sample_aspirate
        self._p_main.flow_rate.dispense = self._sample_dispense

        n = len(list(self.non_control_positions()))
        for i, (s, d) in enumerate(self.non_control_positions()):
            if self.run_stage("transfer sample {}/{}".format(i + 1, n)):
                self.transfer_sample(s, d)

    def transfer_lys(self):
        num_samples_per_aspirate = self._p_main.max_volume // self._lysis_volume
        self.logger.info(
            "1 aspirate can dispense {} times of {}ul.".format(num_samples_per_aspirate, self._lysis_volume))

        pos = list(self.non_control_positions(repeat(None)))
        n = len(pos)
        for i, (_, dest) in enumerate(pos):
            remaining_samples = n - i
            self.logger.debug("Remaining {} samples.".format(remaining_samples))
            # Extracting at every cycle
            # to match correct volume when using start_at
            h = max(
                self._lysis_tube.extract(self._lysis_volume * self._ic_lys_headroom),
                self._lysis_headroom_height
            )

            if self.run_stage("transfer lysis {}/{}".format(i + 1, n)):
                if not self._p_main.has_tip:
                    self.pick_up(self._p_main)

                # checking if we've the necessary volume
                if self._p_main.current_volume < self._lysis_volume:
                    # not enough, filling the pipette
                    if self._p_main.current_volume > 0:
                        self._p_main.dispense(self._air_gap_lys, self._lys_buff.top())
                    fill_volume = min(remaining_samples, num_samples_per_aspirate) * self._lysis_volume
                    self._p_main.aspirate(fill_volume, self._lys_buff.bottom(h))
                    self._p_main.air_gap(self._air_gap_lys)
                self._p_main.dispense(self._lysis_volume + self._air_gap_lys, dest.top())
                self._p_main.air_gap(self._air_gap_lys)
                self.logger.debug("Actual volume: {}".format(self._p_main.current_volume))

        if self._p_main.has_tip:
            self.drop(self._p_main)

    def transfer_internal_control(self, idx: int, dest):
        self._p_main.flow_rate.aspirate = self._lysis_rate_aspirate
        self._p_main.flow_rate.dispense = self._lysis_rate_dispense

        strip_ind = idx // self.cols_per_strip
        self.logger.debug(
            "transferring internal control strip {}/{} to {}".format(strip_ind + 1, self.num_ic_strips, dest))
        internal_control = self._strips_block.rows()[0][strip_ind]
        self.pick_up(self._m20)
        # no air gap to use 1 transfer only avoiding drop during multiple transfers
        self._m20.transfer(self._iec_volume, internal_control, dest.bottom(self._ic_headroom_bottom), new_tip='never')
        self._m20.mix(self._ic_mix_repeats, self._ic_mix_volume, dest.bottom(self._dest_multi_headroom_height))
        self._m20.air_gap(self._air_gap_dest_multi)
        self.drop(self._m20)

    def transfer_internal_controls(self):
        n = len(self._dests_multi)
        for i, d in enumerate(self._dests_multi):
            if self.run_stage("transfer internal control {}/{}".format(i + 1, n)):
                self.transfer_internal_control(i, d)

    def _tipracks(self) -> dict:
        return {
            "_tipracks_main": "_p_main",
            "_tipracks20": "_m20",
        }

    def body(self):
        self.setup_samples()
        self.setup_lys_tube()
        self.msg = ""

        T = (self.transfer_lys, self.transfer_samples)
        for t in (T if self._lysis_first else reversed(T)):
            t()

        self.dual_pause("incubate", between=self.set_external)
        self.set_internal()
        self.transfer_internal_controls()
        self.logger.info(self.msg_format("move to B"))


# Copyright (c) 2020 Covmatic.
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
