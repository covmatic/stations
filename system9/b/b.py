from ..station import Station, labware_loader, instrument_loader
from opentrons.protocol_api import ProtocolContext
from itertools import repeat
from opentrons.types import Point
from typing import Optional, Tuple
import logging


class StationB(Station):
    _protocol_description = "station B protocol"
    
    def __init__(
        self,
        bind_aspiration_rate: float = 50,
        bind_blowout_rate: float = 300,
        bind_dispense_rate: float = 150,
        bind_max_transfer_vol: float = 180,
        default_aspiration_rate: float = 150,
        drop_loc_l: float = -18,
        drop_loc_r: float = 30,
        drop_threshold: int = 296,
        elute_aspiration_rate: float = 50,
        elution_vol: float = 40,
        jupyter: bool = True,
        logger: Optional[logging.getLoggerClass()] = None,
        magheight: float = 6.65,
        magplate_model: str = 'nest_96_wellplate_2ml_deep',
        metadata: Optional[dict] = None,
        num_samples: int = 96,
        park: bool = True,
        samples_per_col: int = 8,
        skip_delay: bool = False,
        supernatant_removal_aspiration_rate: float = 25,
        starting_vol: float = 380,
        tip_log_filename: str = 'tip_log.json',
        tip_log_folder_path: str = './data/B',
        tip_rack: bool = False,
        tipracks_slots: Tuple[str, ...] = ('3', '6', '8', '9', '10'),
    ):
        """ Build a :py:class:`.StationB`.
        :param bind_aspiration_rate: Aspiration flow rate when aspirating bind beads in uL/s
        :param bind_blowout_rate: Blowout flow rate when aspirating bind beads in uL/s
        :param bind_dispense_rate: Dispensation flow rate when aspirating bind beads in uL/s
        :param bind_max_transfer_vol: Maximum volume transferred of bind beads
        :param default_aspiration_rate: Default aspiration flow rate in uL/s
        :param drop_loc_l: offset for dropping to the left side (should be negative) in mm
        :param drop_loc_r: offset for dropping to the right side (should be positive) in mm
        :param drop_threshold: the amount of dropped tips after which the run is paused for emptying the trash
        :param elute_aspiration_rate: Aspiration flow rate when aspirating elution buffer in uL/s
        :param elution_vol: The volume of elution buffer to aspirate in uL
        :param logger: logger object. If not specified, the default logger is used that logs through the ProtocolContext comment method
        :param magheight: Height of the magnet, in mm
        :param magplate_model: Magnetic plate model
        :param metadata: protocol metadata
        :param num_samples: The number of samples that will be loaded on the station B
        :param park: Whether to park or not
        :param samples_per_col: The number of samples in a column of the destination plate
        :param skip_delay: If True, pause instead of delay.
        :param supernatant_removal_aspiration_rate: Aspiration flow rate when removing the supernatant in uL/s
        :param starting_vol: Sample volume at start (volume coming from Station A) 
        :param tip_log_filename: file name for the tip log JSON dump
        :param tip_log_folder_path: folder for the tip log JSON dump
        :param tip_rack: If True, try and load previous tiprack log from the JSON file
        :param tipracks_slots: Slots where the tipracks are positioned
        """
        super(StationB, self).__init__(
            jupyter=jupyter,
            logger=logger,
            metadata=metadata,
            num_samples=num_samples,
            samples_per_col=samples_per_col,
            tip_log_filename=tip_log_filename,
            tip_log_folder_path=tip_log_folder_path,
            tip_rack=tip_rack,
        )
        self._bind_aspiration_rate = bind_aspiration_rate
        self._bind_blowout_rate = bind_blowout_rate
        self._bind_dispense_rate = bind_dispense_rate
        self._bind_max_transfer_vol = bind_max_transfer_vol
        self._default_aspiration_rate = default_aspiration_rate
        self._drop_loc_l = drop_loc_l
        self._drop_loc_r = drop_loc_r
        self._drop_threshold = drop_threshold
        self._elute_aspiration_rate = elute_aspiration_rate
        self._elution_vol = elution_vol
        self._magheight = magheight
        self._magplate_model = magplate_model
        self._park = park
        self._skip_delay = skip_delay
        self._supernatant_removal_aspiration_rate = supernatant_removal_aspiration_rate
        self._starting_vol = starting_vol
        self._tipracks_slots = tipracks_slots
        
        self._drop_count = 0
        self._side_switch = True
    
    def delay(self, mins: float, msg: str):
        msg = "{} for {} minutes".format(msg, mins)
        if self._skip_delay:
            self.logger.info("{}. Pausing for skipping delay. Please resume".format(msg))
            self._ctx.pause()
        else:
            self.logger.info(msg)
            self._ctx.delay(minutes=mins)
    
    @labware_loader(0, "_tips300")
    def load_tips300(self):
        self._tips300 = [
            self._ctx.load_labware('opentrons_96_tiprack_300ul', slot, '200ul filtertiprack')
            for slot in self._tipracks_slots
        ]
    
    @labware_loader(1, "_parking_spots")
    def load_parking_spots(self):
        parkingrack = self._ctx.load_labware(
            'opentrons_96_tiprack_300ul',
            '7',
            'empty tiprack for parking' if self._park else '200ul filtertiprack'
        )
        if self._park:
            self._parking_spots = parkingrack.rows()[0][:self.num_cols]
        else:
            self._tips300.append(parkingrack)
            self._parking_spots = list(repeat(None, self.num_cols))
        self.logger.debug("parking spots: {}".format(self._parking_spots))
    
    @labware_loader(2, "_magdeck")
    def load_magdeck(self):
        self._magdeck = self._ctx.load_module('Magnetic Module Gen2', '4')
        self._magdeck.disengage()
    
    @labware_loader(3, "_magplate")
    def load_magplate(self):
        self._magplate = self._magdeck.load_labware(self._magplate_model)
        self.logger.debug("using '{}' magnetic plate".format(self._magplate_model))
    
    @property
    def mag_samples_m(self):
        return self._magplate.rows()[0][:self.num_cols]
    
    @labware_loader(4, "_tempdeck")
    def load_tempdeck(self):
        self._tempdeck = self._ctx.load_module('Temperature Module Gen2', '1')
        self._tempdeck.set_temperature(4)
    
    @labware_loader(5, "_flatplate")
    def load_flatplate(self):
        self._flatplate = self._tempdeck.load_labware('opentrons_96_aluminumblock_nest_wellplate_100ul')
    
    @property
    def elution_samples_m(self):
        return self._flatplate.rows()[0][:self.num_cols]
    
    @labware_loader(6, "_waste")
    def load_waste(self):
        self._waste = self._ctx.load_labware('nest_1_reservoir_195ml', '11', 'Liquid Waste').wells()[0].top()
    
    @labware_loader(7, "_etoh")
    def load_etoh(self):
        self._etoh = self._ctx.load_labware('nest_1_reservoir_195ml', '2', 'Trough with Ethanol').wells()[:1]
    
    @labware_loader(8, "_res12")
    def load_res12(self):
        self._res12 = self._ctx.load_labware('nest_12_reservoir_15ml', '5', 'Trough with Reagents')
    
    @property
    def binding_buffer(self):
        return self._res12.wells()[:2]
    
    @property
    def wash1(self):
        return self._res12.wells()[3:7]
    
    @property
    def wash2(self):
        return self._res12.wells()[7:11]
    
    @property
    def water(self):
        return self._res12.wells()[11]
    
    @instrument_loader(0, "_m300")
    def load_m300(self):
        self._m300 = self._ctx.load_instrument('p300_multi_gen2', 'left', tip_racks=self._tips300)
        self._m300.flow_rate.aspirate = self._bind_aspiration_rate
        self._m300.flow_rate.dispense = self._bind_dispense_rate
        self._m300.flow_rate.blow_out = self._bind_blowout_rate
        
    def _tiprack_log_args(self):
        # first of each is the m20, second the main pipette
        return ('m300',), (self._m300,), (self._tips300,)
    
    def drop(self, pip):
        # Drop in the Fixed Trash (on 12) at different positions to avoid making a tall heap of tips
        drop_loc = self._ctx.loaded_labwares[12].wells()[0].top().move(Point(x=self._drop_loc_r if self._side_switch else self._drop_loc_l))
        self._side_switch = not self._side_switch
        pip.drop_tip(drop_loc)
        self._drop_count += self._samples_per_col
        self.logger.debug("Dropped at the {} side ({}). There are {} tips in the trash bin".format("right" if self._side_switch else "left", drop_loc, self._drop_count))
        if self._drop_count >= self._drop_threshold:
            self.pause('Pausing. Please empty tips from waste before resuming.', color='red', blink_time=8, level=logging.INFO)
            self._drop_count = 0
    
    def run(self, ctx: ProtocolContext):
        super(StationB, self).run(ctx)


if __name__ == "__main__":
    StationB(metadata={'apiLevel': '2.3'}).simulate()
