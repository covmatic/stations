from ..station import Station, labware_loader, instrument_loader
from itertools import chain
import math
import logging
from itertools import repeat
from typing import Optional, Tuple


class StationC(Station):
    _protocol_description = "station C protocol"
    
    def __init__(
        self,
        bottom_headroom_height: float = 0.5,
        drop_loc_l: float = 0,
        drop_loc_r: float = 0,
        drop_threshold: int = 296,
        jupyter: bool = True,
        logger: Optional[logging.getLoggerClass()] = None,
        mastermix_vol: float = 12,
        mastermix_vol_headroom: float = 1.2,
        mastermix_vol_headroom_aspirate: float = 20/18,
        metadata: Optional[dict] = None,
        num_samples: int = 96,
        positive_control_well: str = 'A10',
        sample_blow_height: float = -2,
        sample_bottom_height: float = 2,
        sample_mix_vol: float = 10,
        sample_mix_reps: int = 1,
        sample_vol: float = 8,
        samples_per_col: int = 8,
        samples_per_cycle: int = 96,
        skip_delay: bool = False,
        source_plate_name: str = 'chilled elution plate on block from Station B',
        suck_height: float = 2,
        suck_vol: float = 5,
        tipracks_slots: Tuple[str, ...] = ('2', '3', '6', '7', '9'),
        transfer_samples: bool = True,
        tube_block_model: str = "opentrons_24_aluminumblock_nest_1.5ml_snapcap",
        **kwargs
    ):
        """ Build a :py:class:`.StationC`.
        :param bottom_headroom_height: Height to keep from the bottom
        :param drop_loc_l: offset for dropping to the left side (should be positive) in mm
        :param drop_loc_r: offset for dropping to the right side (should be negative) in mm
        :param drop_threshold: the amount of dropped tips after which the run is paused for emptying the trash
        :param logger: logger object. If not specified, the default logger is used that logs through the ProtocolContext comment method
        :param mastermix_vol: Mastermix volume per sample in uL
        :param mastermix_vol_headroom: Headroom for mastermix preparation volume as a multiplier
        :param mastermix_vol_headroom_aspirate: Headroom for mastermix aspiration volume as a divisor
        :param metadata: protocol metadata
        :param num_samples: The number of samples that will be loaded on the station B
        :param positive_control_well: Position of the positive control well
        :param sample_blow_height: Height from the top when blowing out in mm (should be negative)
        :param sample_bottom_height: Height to keep from the bottom in mm when dealing with samples
        :param sample_mix_vol: Samples mixing volume in uL
        :param sample_mix_reps: Samples mixing repetitions 
        :param sample_vol: Sample volume
        :param samples_per_col: The number of samples in a column of the destination plate
        :param samples_per_cycle: The number of samples processable in one cycle
        :param source_plate_name: Name for the source plate
        :param skip_delay: If True, pause instead of delay.
        :param suck_height: Height from the top when sucking in any remaining droplets on way to trash in mm
        :param suck_vol: Volume for sucking in any remaining droplets on way to trash in uL
        :param transfer_samples: Whether to transfer samples or not
        :param tube_block_model: Tube block model name
        """
        super(StationC, self).__init__(
            drop_loc_l=drop_loc_l,
            drop_loc_r=drop_loc_r,
            drop_threshold=drop_threshold,
            jupyter=jupyter,
            logger=logger,
            metadata=metadata,
            num_samples=num_samples,
            samples_per_col=samples_per_col,
            skip_delay=skip_delay,
            **kwargs
        )
        self._bottom_headroom_height = bottom_headroom_height
        self._mastermix_vol = mastermix_vol
        self._mastermix_vol_headroom = mastermix_vol_headroom
        self._mastermix_vol_headroom_aspirate = mastermix_vol_headroom_aspirate
        self._positive_control_well = positive_control_well
        self._sample_blow_height = sample_blow_height
        self._sample_bottom_height = sample_bottom_height
        self._sample_mix_vol = sample_mix_vol
        self._sample_mix_reps = sample_mix_reps
        self._sample_vol = sample_vol
        self._samples_per_cycle = int(math.ceil(samples_per_cycle / 8) * 8)
        self._source_plate_name = source_plate_name
        self._suck_height = suck_height
        self._suck_vol = suck_vol
        self._tipracks_slots = tipracks_slots
        self._transfer_samples = transfer_samples
        self._tube_block_model = tube_block_model
        
        self._remaining_samples = self._num_samples
        self._samples_this_cycle = min(self._remaining_samples, self._samples_per_cycle)
    
    @property
    def num_cycles(self) -> int:
        return int(math.ceil(self._num_samples / self._samples_per_cycle))
    
    @labware_loader(0, "_source_plate")
    def load_source_plate(self):
        self._source_plate = self._ctx.load_labware('opentrons_96_aluminumblock_nest_wellplate_100ul', '1', self._source_plate_name)
    
    @labware_loader(1, "_tips20")
    def load_tips20(self):
        self._tips20 = [
            self._ctx.load_labware('opentrons_96_filtertiprack_20ul', slot)
            for slot in self._tipracks_slots
        ]
    
    @labware_loader(2, "_tips20_no_a")
    def load_tips20_no_a(self):
        self._tips20_no_a = [self._ctx.load_labware('opentrons_96_filtertiprack_20ul', '11', '20ul tiprack - no tips in row A')]
    
    @labware_loader(3, "_tips300")
    def loadtips300(self):
        self._tips300 = [self._ctx.load_labware('opentrons_96_filtertiprack_200ul', '10')]
    
    @labware_loader(4, "_tempdeck")
    def load_tempdeck(self):
        self._tempdeck = self._ctx.load_module('Temperature Module Gen2', '4')

    @labware_loader(5, "_pcr_plate")
    def load_pcr_plate(self):
        self._pcr_plate = self._tempdeck.load_labware('opentrons_96_aluminumblock_biorad_wellplate_200ul', 'PCR plate')
        
    @labware_loader(6, "_mm_strips")
    def load_mm_strips(self):
        self._mm_strips = self._ctx.load_labware('opentrons_96_aluminumblock_generic_pcr_strip_200ul', '8', 'mastermix strips')
    
    @labware_loader(7, "_tube_block")
    def load_tube_block(self):
        self._tube_block = self._ctx.load_labware(self._tube_block_model, '5', 'screw tube aluminum block for mastermix + controls')
    
    @instrument_loader(0, "_m20")
    def load_m20(self):
        self._m20 = self._ctx.load_instrument('p20_multi_gen2', 'right', tip_racks=self._tips20)
    
    @instrument_loader(0, "_p300")
    def load_p300(self):
        self._p300 = self._ctx.load_instrument('p300_single_gen2', 'left', tip_racks=self._tips300)
    
    @property
    def sources(self):
        return self._source_plate.rows()[0][:self.num_cols]
    
    @property
    def sample_dests(self):
        return self._pcr_plate.rows()[0][:self.num_cols]
    
    def _tipracks(self) -> dict:
        return {
            "_tips300": "_p300",
            "_tips20": "_m20",
            "_tips20_no_a": "_m20",
        }
    
    def pick_up_no_a(self):
        self.pick_up(self._m20, tiprack="_tips20_no_a")
        
    @property
    def mm_tubes(self):
        return self._tube_block.wells()[:1]
    
    @property
    def mm_strips(self):
        return self._mm_strips.columns()[:1]
    
    @property
    def remaining_cols(self) -> int: 
        return int(math.ceil(min(self._remaining_samples, self._samples_per_cycle) / self._m20.channels))
    
    def fill_mm_strips(self):
        vol_per_strip_well = self.remaining_cols * self._mastermix_vol / len(self.mm_strips)
        
        has_tip = False        
        for j, (strip, tube) in enumerate(zip(self.mm_strips, self.mm_tubes)):
            for i, well in enumerate(strip):
                if self.run_stage("transfer mastermix {}/{} to strip {}/{}{}{}".format(i + 1, len(strip), j + 1, len(self.mm_strips), " " if self.num_cycles > 1 else "", self._cycle)):
                    if not has_tip:
                        self.pick_up(self._p300)
                        has_tip = True
                    self.logger.debug("filling mastermix at {}".format(well))
                    self._p300.transfer(vol_per_strip_well, tube, well, new_tip='never')
        if has_tip:
            self._p300.drop_tip()
    
    @property
    def mm_indices(self):
        return list(repeat(0, self._samples_per_cycle))
    
    def transfer_mm(self, stage="transfer mastermix {}/{}"):
        has_tip = False
        n = len(list(zip(self.mm_indices[::self._m20.channels], self.sample_dests[:self.remaining_cols])))
        for i, (m_idx, s) in enumerate(zip(self.mm_indices[::self._m20.channels], self.sample_dests[:self.remaining_cols])):
            if self.run_stage(stage.format(i + 1, n)):
                if not has_tip:
                    self.pick_up(self._m20)
                    has_tip = True
            self._m20.transfer(self._mastermix_vol / self._mastermix_vol_headroom_aspirate, self.mm_strips[m_idx][0].bottom(0.5), s, new_tip='never')
        if has_tip:
            self._m20.drop_tip()
    
    def transfer_sample(self, vol: float, source, dest):
        self.logger.debug("transferring {:.0f} uL from {} to {}".format(vol, source, dest))
        self.pick_up(self._m20, tiprack="_tips20_no_a" if source.display_name.split(" ")[0] == self._positive_control_well else None)
        self._m20.transfer(vol, source.bottom(self._sample_bottom_height), dest.bottom(self._sample_bottom_height), new_tip='never')
        self._m20.mix(self._sample_mix_reps, self._sample_mix_vol, dest.bottom(self._sample_bottom_height))
        self._m20.blow_out(dest.top(self._sample_blow_height))
        self._m20.aspirate(self._suck_vol, dest.top(self._suck_height))  # suck in any remaining droplets on way to trash
        self._m20.drop_tip()
        
    def cycle_begin(self):
        self.logger.info(self.get_msg_format("current cycle", self._cycle.split(" ")[-1]))
        self._cycle = self._cycle if self.num_cycles > 1 else ""
    
    def run_cycle(self):
        self._cycle = self.stage
        n = self._remaining_samples
        self._samples_this_cycle = min(n, self._samples_per_cycle)
        
        self.cycle_begin()
        
        self.fill_mm_strips()
        self.transfer_mm(stage="transfer mastermix to plate {}{}{}".format("{}/{}", " " if self.num_cycles > 1 else "", self._cycle))
        for i, (s, d) in enumerate(zip(self.sources, self.sample_dests)):
            if self._transfer_samples and self.run_stage("transfer samples {}/{}".format(self._num_samples + min(self._m20.channels - self._remaining_samples, 0), self._num_samples)):
                if self.num_cycles > 1:
                    self.msg_format("sample per cycle", (i + 1) * self._m20.channels, self._samples_this_cycle, self._cycle.split(" ")[-1])
                    self.logger.info(self.msg)
                self.transfer_sample(self._sample_vol, s, d)
                self.msg = ""
            self._remaining_samples -= self._m20.channels
            if self._remaining_samples <= 0 or n - self._remaining_samples >= self._samples_this_cycle:
                break 
    
    def body(self):
        self.logger.info(self.get_msg_format("number of cycles", self._num_samples, self.num_cycles))
        
        for i in range(self.num_cycles):
            self.run_stage("cycle {}/{}".format(i + 1, self.num_cycles))
            self.run_cycle()
            self.pause(self.get_msg_format("end of cycle", i + 1, self.num_cycles), color="yellow")
            if i + 1 < self.num_cycles and self.run_stage("pausing for next cycle {}/{}".format(i + 2, self.num_cycles)):
                self.pause("new cycle", color="green", blink=False, home=False)


if __name__ == "__main__":
    StationC(num_samples=480, metadata={'apiLevel': '2.3'}).simulate()


# Copyright (c) 2020 Covmatic.
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
