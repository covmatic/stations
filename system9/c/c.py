from ..station import Station, labware_loader, instrument_loader
from opentrons.protocol_api import ProtocolContext
import logging
from typing import Optional, Tuple


class StationC(Station):
    _protocol_description = "station C protocol"
    
    def __init__(
        self,
        drop_loc_l: float = 0,
        drop_loc_r: float = 0,
        drop_threshold: int = 296,
        jupyter: bool = True,
        logger: Optional[logging.getLoggerClass()] = None,
        metadata: Optional[dict] = None,
        num_samples: int = 96,
        samples_per_col: int = 8,
        skip_delay: bool = False,
        tipracks_slots: Tuple[str, ...] = ('2', '3', '6', '7', '9'),
        tip_log_filename: str = 'tip_log.json',
        tip_log_folder_path: str = './data/C',
        tip_track: bool = False,
    ):
        """ Build a :py:class:`.StationC`.
        :param drop_loc_l: offset for dropping to the left side (should be positive) in mm
        :param drop_loc_r: offset for dropping to the right side (should be negative) in mm
        :param drop_threshold: the amount of dropped tips after which the run is paused for emptying the trash
        :param logger: logger object. If not specified, the default logger is used that logs through the ProtocolContext comment method
        :param metadata: protocol metadata
        :param num_samples: The number of samples that will be loaded on the station B
        :param samples_per_col: The number of samples in a column of the destination plate
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
        self._tipracks_slots = tipracks_slots
    
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
    def load_mp300(self):
        self._p300 = self._ctx.load_instrument('p300_single_gen2', 'left', tip_racks=self._tips300)

    def _tiprack_log_args(self):
        return (), (), ()
    
    def run(self, ctx: ProtocolContext):
        super(StationC, self).run(ctx)


if __name__ == "__main__":
    StationC(metadata={'apiLevel': '2.3'}).simulate()
