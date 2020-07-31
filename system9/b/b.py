from ..station import Station, labware_loader, instrument_loader
from ..utils import mix_bottom_top, uniform_divide, mix_walk
from opentrons.protocol_api import ProtocolContext
from opentrons.types import Point, Location
from itertools import repeat
from typing import Optional, Tuple
import logging
import math


class StationB(Station):
    _protocol_description = "station B protocol"
    
    def __init__(
        self,
        bind_air_gap: float = 20,
        bind_aspiration_rate: float = 50,
        bind_blowout_rate: float = 300,
        bind_dispense_rate: float = 150,
        bind_max_transfer_vol: float = 180,
        bind_mix_loc_bottom: float = 1,
        bind_mix_loc_top: float = 5,
        bind_mix_times: int = 8,
        bind_mix_vol: float = 180,
        bind_sample_mix_times: int = 5,
        bind_sample_mix_vol: float = 20,
        bind_vol: float = 210,
        bottom_headroom_height: float = 0.5,
        default_aspiration_rate: float = 150,
        drop_loc_l: float = 30,
        drop_loc_r: float = -18,
        drop_threshold: int = 296,
        elute_air_gap: float = 20,
        elute_aspiration_rate: float = 50,
        elute_mix_times: int = 10,
        elute_mix_vol: float = 30,
        elution_height: float = 5,
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
        supernatant_removal_air_gap: float = 20,
        supernatant_removal_aspiration_rate: float = 25,
        supernatant_removal_height: float = 0.5,
        starting_vol: float = 380,
        tip_log_filename: str = 'tip_log.json',
        tip_log_folder_path: str = './data/B',
        tip_track: bool = False,
        tipracks_slots: Tuple[str, ...] = ('3', '6', '8', '9', '10'),
        touch_tip_height: float = -5,
        wait_time_bind_off: float = 5,
        wait_time_bind_on: float = 5,
        wait_time_dry: float = 12,
        wait_time_elute_off: float = 5,
        wait_time_elute_on: float = 3,
        wait_time_wash_on: float = 5,
        wash_air_gap: float = 20,
        wash_etoh_times: int = 4,
        wash_etoh_vol: float = 800,
        wash_max_transfer_vol: float = 200,
        wash_mix_aspiration_rate: float = 400,
        wash_mix_dispense_rate: float = 400,
        wash_mix_speed: float = 20,
        wash_mix_vol: float = 150,
        wash_mix_walk: bool = False,
        wash_1_times: int = 20,
        wash_1_vol: float = 500,
        wash_2_times: int = 20,
        wash_2_vol: float = 500,
    ):
        """ Build a :py:class:`.StationB`.
        :param bind_air_gap: Air gap for bind beads in uL
        :param bind_aspiration_rate: Aspiration flow rate when aspirating bind beads in uL/s
        :param bind_blowout_rate: Blowout flow rate when aspirating bind beads in uL/s
        :param bind_dispense_rate: Dispensation flow rate when aspirating bind beads in uL/s
        :param bind_max_transfer_vol: Maximum volume transferred of bind beads
        :param bind_mix_loc_bottom: Mixing location for bind beads at the bottom in mm
        :param bind_mix_loc_top: Mixing location for bind beads at the top in mm
        :param bind_mix_times: Mixing repetitions for bind beads
        :param bind_mix_vol: Mixing volume for bind beads
        :param bind_sample_mix_times: Mixing repetitions for bind beads and samples
        :param bind_sample_mix_vol: Mixing repetitions for bind beads in uL
        :param bind_vol: Total volume transferred of bind beads
        :param bottom_headroom_height: Height to keep from the bottom
        :param default_aspiration_rate: Default aspiration flow rate in uL/s
        :param drop_loc_l: offset for dropping to the left side (should be positive) in mm
        :param drop_loc_r: offset for dropping to the right side (should be negative) in mm
        :param drop_threshold: the amount of dropped tips after which the run is paused for emptying the trash
        :param elute_air_gap: Air gap when aspirating elution buffer in uL
        :param elute_aspiration_rate: Aspiration flow rate when aspirating elution buffer in uL/s
        :param elute_mix_times: Mix times for elution
        :param elute_mix_vol: Mix volume for elution
        :param elution_height: Height at which to sample after elution in mm
        :param elution_vol: The volume of elution buffer to aspirate in uL
        :param logger: logger object. If not specified, the default logger is used that logs through the ProtocolContext comment method
        :param magheight: Height of the magnet, in mm
        :param magplate_model: Magnetic plate model
        :param metadata: protocol metadata
        :param num_samples: The number of samples that will be loaded on the station B
        :param park: Whether to park or not
        :param samples_per_col: The number of samples in a column of the destination plate
        :param skip_delay: If True, pause instead of delay.
        :param supernatant_removal_air_gap: Air gap when removing the supernatant in uL
        :param supernatant_removal_aspiration_rate: Aspiration flow rate when removing the supernatant in uL/s
        :param supernatant_removal_height: Height from the bottom when removing the supernatant in mm
        :param starting_vol: Sample volume at start (volume coming from Station A) 
        :param tip_log_filename: file name for the tip log JSON dump
        :param tip_log_folder_path: folder for the tip log JSON dump
        :param tip_track: If True, try and load previous tiprack log from the JSON file
        :param tipracks_slots: Slots where the tipracks are positioned
        :param touch_tip_height: Touch-tip height in mm (should be negative)
        :param wait_time_bind_off: Wait time for bind beads phase off magnet in minutes
        :param wait_time_bind_on: Wait time for bind beads phase on magnet in minutes
        :param wait_time_dry: Wait time for airdrying phase in minutes
        :param wait_time_elute_off: Wait time for elution phase off magnet in minutes
        :param wait_time_elute_on: Wait time for elution phase on magnet in minutes
        :param wait_time_wash_on: Wait time for wash phase on magnet in minutes
        :param wash_air_gap: Air gap for wash in uL
        :param wash_etoh_times: Mix times for ethanol
        :param wash_etoh_vol: Volume of ethanol in uL
        :param wash_max_transfer_vol: Maximum volume transferred of wash in uL
        :param wash_mix_aspiration_rate: Aspiration flow rate when mixing wash buffer in uL/s
        :param wash_mix_dispense_rate: Dispensation flow rate when mixing wash buffer in uL/s
        :param wash_mix_speed: Movement speed of the pipette while mixing in mm/s
        :param wash_mix_vol: Mix volume for wash
        :param wash_mix_walk: Whether to move or not when mixing the wash buffer
        :param wash_1_times: Mix times for wash 1
        :param wash_1_vol: Volume of wash 1 buffer in uL
        :param wash_2_times: Mix times for wash 2
        :param wash_2_vol: Volume of wash 2 buffer in uL
        """
        super(StationB, self).__init__(
            drop_loc_l=drop_loc_l,
            drop_loc_r=drop_loc_r,
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
        self._bind_air_gap = bind_air_gap
        self._bind_aspiration_rate = bind_aspiration_rate
        self._bind_blowout_rate = bind_blowout_rate
        self._bind_dispense_rate = bind_dispense_rate
        self._bind_max_transfer_vol = bind_max_transfer_vol
        self._bind_mix_loc_bottom = bind_mix_loc_bottom
        self._bind_mix_loc_top = bind_mix_loc_top
        self._bind_mix_times = bind_mix_times
        self._bind_mix_vol = bind_mix_vol
        self._bind_sample_mix_times = bind_sample_mix_times
        self._bind_sample_mix_vol = bind_sample_mix_vol
        self._bind_vol = bind_vol
        self._bottom_headroom_height = bottom_headroom_height
        self._default_aspiration_rate = default_aspiration_rate
        self._drop_threshold = drop_threshold
        self._elute_air_gap = elute_air_gap
        self._elute_aspiration_rate = elute_aspiration_rate
        self._elute_mix_times = elute_mix_times
        self._elute_mix_vol = elute_mix_vol
        self._elution_height = elution_height
        self._elution_vol = elution_vol
        self._magheight = magheight
        self._magplate_model = magplate_model
        self._park = park
        self._supernatant_removal_air_gap = supernatant_removal_air_gap
        self._supernatant_removal_aspiration_rate = supernatant_removal_aspiration_rate
        self._supernatant_removal_height = supernatant_removal_height
        self._starting_vol = starting_vol
        self._tipracks_slots = tipracks_slots
        self._touch_tip_height = touch_tip_height
        self._wait_time_bind_off = wait_time_bind_off
        self._wait_time_bind_on = wait_time_bind_on
        self._wait_time_dry = wait_time_dry
        self._wait_time_elute_off = wait_time_elute_off
        self._wait_time_elute_on = wait_time_elute_on
        self._wait_time_wash_on = wait_time_wash_on
        self._wash_air_gap = wash_air_gap
        self._wash_etoh_times = wash_etoh_times
        self._wash_etoh_vol = wash_etoh_vol
        self._wash_max_transfer_vol = wash_max_transfer_vol
        self._wash_mix_aspiration_rate = wash_mix_aspiration_rate
        self._wash_mix_dispense_rate = wash_mix_dispense_rate
        self._wash_mix_speed = wash_mix_speed
        self._wash_mix_vol = wash_mix_vol
        self._wash_mix_walk = wash_mix_walk
        self._wash_1_times = wash_1_times
        self._wash_1_vol = wash_1_vol
        self._wash_2_times = wash_2_times
        self._wash_2_vol = wash_2_vol
    
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
    
    def _tipracks(self) -> dict:
        return {"_tips300": "_m300",}
    
    def drop(self, pip, loc: Optional[Location] = None):
        if loc is None or not self._park:
            super(StationB, self).drop(pip)
        else:
            self._m300.drop_tip(loc)
    
    def remove_supernatant(self, vol: float):
        self._m300.flow_rate.aspirate = self._supernatant_removal_aspiration_rate
        num_trans = math.ceil(vol / self._bind_max_transfer_vol)
        vol_per_trans = vol / num_trans
        
        for i, (m, spot) in enumerate(zip(self.mag_samples_m, self._parking_spots)):
            self.pick_up(self._m300, spot if self._park else None)
            loc = m.bottom(self._supernatant_removal_height).move(Point(x=(-1 if i % 2 == 0 else 1)*2))
            for _ in range(num_trans):
                if self._m300.current_volume > 0:
                    self._m300.dispense(self._m300.current_volume, m.top())
                self._m300.move_to(m.center())
                self._m300.transfer(vol_per_trans, loc, self._waste, new_tip='never', air_gap=self._supernatant_removal_air_gap)
                self._m300.blow_out(self._waste)
                self._m300.air_gap(self._supernatant_removal_air_gap)
            self.drop(self._m300)
        self._m300.flow_rate.aspirate = self._default_aspiration_rate
        
    def bind(self):
        """Add bead binding buffer and mix samples"""
        self._m300.flow_rate.aspirate = self._bind_aspiration_rate
        
        for i, (well, spot) in enumerate(zip(self.mag_samples_m, self._parking_spots)):
            source = self.binding_buffer[i // ((len(self.mag_samples_m) // len(self.binding_buffer)) or 1)]
            self.pick_up(self._m300)
            mix_bottom_top(
                self._m300,
                self._bind_mix_times,
                self._bind_mix_vol,
                source.bottom,
                self._bind_mix_loc_bottom,
                self._bind_mix_loc_top
            )
            
            num_trans, vol_per_trans = uniform_divide(self._bind_vol, self._bind_max_transfer_vol)
            
            for t in range(num_trans):
                if self._m300.current_volume > 0:
                    self._m300.dispense(self._m300.current_volume, source.top())  # void air gap if necessary
                self._m300.transfer(vol_per_trans, source, well.top(), air_gap=self._bind_air_gap, new_tip='never')
                if t == 0:
                    self._m300.air_gap(self._bind_air_gap)
            self._m300.mix(self._bind_sample_mix_times, self._bind_sample_mix_vol, well)
            
            self._m300.touch_tip(v_offset=self._touch_tip_height)
            self._m300.air_gap(self._bind_air_gap)
            self.drop(self._m300, spot)
        
        # Time Issue in Station B After the waiting time of 5 min the magnetic module should run for 6 min.
        self.delay(self._wait_time_bind_off, 'waiting before magnetic module activation')
        self._magdeck.engage(height=self._magheight)
        
        # Time Issue in Station B After the waiting time of 5 min the magnetic module should run for 6 min.
        self.delay(self._wait_time_bind_on, 'incubating on MagDeck')

        # Remove initial supernatant
        self.remove_supernatant(self._bind_vol + self._starting_vol)
    
    def wash(self, vol: float, source, mix_reps: int):
        self.logger.info("washing with {} uL of wash for {} times".format(vol, mix_reps))
        self._m300.flow_rate.aspirate = self._default_aspiration_rate
        dispense_rate = self._m300.flow_rate.dispense
        self._magdeck.disengage()
        num_trans, vol_per_trans = uniform_divide(vol, self._wash_max_transfer_vol)
        
        for i, (m, spot) in enumerate(zip(self.mag_samples_m, self._parking_spots)):
            self.pick_up(self._m300)
            src = source[i // ((len(self.mag_samples_m) // len(source)) or 1)]
            
            for n in range(num_trans):
                if self._m300.current_volume > 0:
                    self._m300.dispense(self._m300.current_volume, src.top())
                self._m300.transfer(vol_per_trans, src, m.top(), air_gap=20, new_tip='never')
                if n < num_trans - 1:  # only air_gap if going back to source
                    self._m300.air_gap(self._wash_air_gap)
            
            # Mix
            self._m300.flow_rate.aspirate = self._wash_mix_aspiration_rate
            self._m300.flow_rate.dispense = self._wash_mix_dispense_rate
            if self._wash_mix_walk:
                a_locs = [m.bottom(self._bottom_headroom_height).move(Point(x=2*(-1 if i % 2 else +1), y=2*(2*j/(mix_reps - 1) - 1))) for j in range(mix_reps)]
                mix_walk(self._m300, mix_reps, self._wash_mix_vol, a_locs, speed=self._wash_mix_speed, logger=self.logger)
            else:
                loc = m.bottom(self._bottom_headroom_height).move(Point(x=2*(-1 if i % 2 else +1)))
                self._m300.mix(mix_reps, self._wash_mix_vol, loc)
            self._m300.flow_rate.aspirate = self._default_aspiration_rate
            self._m300.flow_rate.dispense = dispense_rate
            
            # self._m300.blow_out(m.top())
            self._m300.touch_tip(v_offset=self._touch_tip_height)
            self._m300.air_gap(self._wash_air_gap)
            self.drop(self._m300, spot)
        
        self._magdeck.engage(height=self._magheight)
        self.delay(self._wait_time_wash_on, 'incubating on MagDeck')
        self.remove_supernatant(vol)
    
    def elute(self):
        """Resuspend beads in elution"""
        self._m300.flow_rate.aspirate = self._elute_aspiration_rate
        for i, (m, spot) in enumerate(zip(self.mag_samples_m, self._parking_spots)):
            self.pick_up(self._m300)
            side = 1 if i % 2 == 0 else -1
            loc = m.bottom(self._bottom_headroom_height).move(Point(x=side*2))
            self._m300.aspirate(self._elution_vol, self.water)
            self._m300.move_to(m.center())
            self._m300.dispense(self._elution_vol, loc)
            self._m300.mix(self._elute_mix_times, self._elute_mix_vol, loc)
            # self._m300.blow_out(m.bottom(5))		# trying not to make bubbles
            self._m300.touch_tip(v_offset=self._touch_tip_height)
            self._m300.air_gap(self._elute_air_gap)
            self.drop(self._m300, spot)
        
        self.delay(self._wait_time_elute_off, 'incubating off magnet at room temperature')
        self._magdeck.engage(height=self._magheight)
        self.delay(self._wait_time_elute_on, 'incubating on magnet at room temperature')
        
        for i, (m, e, spot) in enumerate(zip(
            self.mag_samples_m,
            self.elution_samples_m,
            self._parking_spots,
        )):
            self.pick_up(self._m300, spot if self._park else None)
            side = -1 if i % 2 == 0 else 1
            loc = m.bottom(self._bottom_headroom_height).move(Point(x=side*2))
            self._m300.transfer(self._elution_vol, loc, e.bottom(self._elution_height), air_gap=self._elute_air_gap, new_tip='never')
            # m300.blow_out(e.top(-2))
            self._m300.air_gap(self._elute_air_gap)
            self.drop(self._m300)
    
    def run(self, ctx: ProtocolContext):
        super(StationB, self).run(ctx)
        self.bind()
        self.wash(self._wash_1_vol, self.wash1, self._wash_1_times)
        self.wash(self._wash_2_vol, self.wash2, self._wash_2_times)
        self.wash(self._wash_etoh_vol, self._etoh, self._wash_etoh_times)
        self._magdeck.disengage()
        self.delay(self._wait_time_dry, 'airdrying beads at room temperature')
        self.elute()
        self._magdeck.disengage()
        self.track_tip()
        self._ctx.home()


if __name__ == "__main__":
    StationB(metadata={'apiLevel': '2.3'}).simulate()
