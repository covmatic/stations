from ..station import Station, labware_loader, instrument_loader
from opentrons.protocol_api import ProtocolContext
import math
import logging
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
        mastermix_vol_headroom: float = 1.1,
        metadata: Optional[dict] = None,
        num_samples: int = 96,
        positive_control_well: str = 'A10',
        samples_per_col: int = 8,
        samples_per_cycle: int = 96,
        skip_delay: bool = False,
        tipracks_slots: Tuple[str, ...] = ('2', '3', '6', '7', '9'),
        tip_log_filename: str = 'tip_log.json',
        tip_log_folder_path: str = './data/C',
        tip_track: bool = False,
    ):
        """ Build a :py:class:`.StationC`.
        :param bottom_headroom_height: Height to keep from the bottom
        :param drop_loc_l: offset for dropping to the left side (should be positive) in mm
        :param drop_loc_r: offset for dropping to the right side (should be negative) in mm
        :param drop_threshold: the amount of dropped tips after which the run is paused for emptying the trash
        :param logger: logger object. If not specified, the default logger is used that logs through the ProtocolContext comment method
        :param mastermix_vol_headroom: Headroom for mastermix volume as a multiplier
        :param metadata: protocol metadata
        :param num_samples: The number of samples that will be loaded on the station B
        :param positive_control_well: Position of the positive control well
        :param samples_per_col: The number of samples in a column of the destination plate
        :param samples_per_cycle: The number of samples processable in one cycle
        :param skip_delay: If True, pause instead of delay.
        :param tip_log_filename: file name for the tip log JSON dump
        :param tip_log_folder_path: folder for the tip log JSON dump
        :param tip_track: If True, try and load previous tiprack log from the JSON file
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
            tip_log_filename=tip_log_filename,
            tip_log_folder_path=tip_log_folder_path,
            tip_track=tip_track,
        )
        self._bottom_headroom_height = bottom_headroom_height
        self._mastermix_vol_headroom = mastermix_vol_headroom
        self._positive_control_well = positive_control_well 
        self._samples_per_cycle = samples_per_cycle
        self._tipracks_slots = tipracks_slots
        
        self._remaining_samples = self._num_samples
    
    @property
    def num_cycles(self) -> int:
        return int(math.ceil(self._num_samples / self._samples_per_cycle))
    
    @labware_loader(0, "_source_plate")
    def load_tips300(self):
        self._source_plate = self._ctx.load_labware('opentrons_96_aluminumblock_nest_wellplate_100ul', '1', 'chilled elution plate on block from Station B')
    
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
        self._tube_block = self._ctx.load_labware('opentrons_24_aluminumblock_nest_1.5ml_snapcap', '5', '2ml screw tube aluminum block for mastermix + controls')
    
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
    def mm_tube(self):
        return self._tube_block.wells()[0]
    
    @property
    def mm_dict(self):
        return {
            'volume': 12,
            'components': {tube: vol for tube, vol in zip(self._tube_block.columns()[1], [10, 2])}
        }
    
    @property
    def mm_strip(self):
        return self._mm_strips.columns()[0]
    
    @property
    def remaining_cols(self) -> int: 
        return int(math.ceil(min(self._remaining_samples, self._samples_per_cycle) / self._m20.channels))
    
    def fill_mm_strips(self):
        vol_per_strip_well = self.remaining_cols * self.mm_dict['volume'] * self._mastermix_vol_headroom
        
        self.pick_up(self._p300)        
        for well in self.mm_strip:
            self.logger.debug("filling mastermix at {}".format(well))
            self._p300.transfer(vol_per_strip_well, self.mm_tube, well, new_tip='never')
        self._p300.drop_tip()
    
    def transfer_mm(self):
        mm_vol = self.mm_dict['volume']
        self.pick_up(self._m20)
        self._m20.transfer(mm_vol, self.mm_strip[0].bottom(self._bottom_headroom_height), self.sample_dests[:self.remaining_cols], new_tip='never')
        self._m20.drop_tip()
    
    def transfer_sample(self, vol: float, source, dest):
        self.logger.debug("transferring {:.0f} uL from {} to {}".format(vol, source, dest))
        self.pick_up(self._m20, tiprack="_tips20_no_a" if source.display_name.split(" ")[0] == self._positive_control_well else None)
        self._m20.transfer(vol, source.bottom(2), dest.bottom(2), new_tip='never')
        self._m20.mix(1, 10, dest.bottom(2))
        self._m20.blow_out(dest.top(-2))
        self._m20.aspirate(5, dest.top(2))
        self._m20.drop_tip()
        self._remaining_samples -= self._m20.channels
    
    def run_cycle(self):
        self.fill_mm_strips()
        self.transfer_mm()
        for s, d in zip(self.sources, self.sample_dests):
            self.transfer_sample(20 - self.mm_dict['volume'], s, d)
            if self._remaining_samples <= 0:
                break
    
    def run(self, ctx: ProtocolContext):
        super(StationC, self).run(ctx)
        self.logger.info("set up for {} samples in {} cycle{}".format(self._num_samples, self.num_cycles, "" if self.num_cycles == 1 else "s"))
        
        for i in range(self.num_cycles):
            self.logger.info("cycle {}/{}".format(i + 1, self.num_cycles))
            self.run_cycle()
            if self._remaining_samples > 0:
                self.pause(
                    "end of cycle {}/{}. Please, load a new plate from station B. Resume when it is ready".format(i + 1, self.num_cycles),
                    blink=True, color="green",
                )
        
        self.track_tip()
        self._ctx.home()


if __name__ == "__main__":
    StationC(metadata={'apiLevel': '2.3'}).simulate()
