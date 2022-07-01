from ..multi_tube_source import MultiTubeSource
from ..utils import MoveWithSpeed, mix_bottom_top
from .p1000 import StationAP1000
from .reload import StationAReloadMixin
from .copan_24 import Copan24Specs
from .copan_48 import copan_48_corrected_specs
from .copan_48_saliva import copan_48_saliva_corrected_specs
from typing import Tuple, Optional


class StationATechnogenetics(StationAP1000):
    def __init__(self,
        beads_flow_rate: float = 7.6,
        beads_mix_repeats: int = 0,
        beads_mix_volume: float = 20,
        beads_vol: float = 9,
        drop_threshold: int = 5000,
        deepwell_headroom_bottom: float = 2,
        lys_mix_repeats: int = 0,
        lys_mix_volume: float = 400,
        lys_mix_last_rate: float = 100,
        lysis_volume: float = 400,
        lysis_in_controls: bool = True,
        lysis_rate_aspirate: float = 600,
        lysis_rate_dispense: float = 600,
        lysis_rate_mix: float = 600,
        mix_repeats: int = 0,
        negative_control_well='A1',
        positive_control_well=None,
        prot_k_capacity: float = 180,
        prot_k_flow_rate: float = 20,
        prot_k_headroom: float = 1.1,
        prot_k_vertical_speed = 15,
        prot_k_vol: float = 20,
        sample_aspirate: float = 100,
        sample_dispense: float = 100,
        strip_headroom_bottom: float = 0.5,
        beads_vertical_speed: float = 5,
        tempdeck_temp: Optional[float] = None,
        tempdeck_bool: bool = False,
        tipracks_slots: Tuple[str, ...] = ('10', '11'),
        tipracks_slots_20: Tuple[str, ...] = ('8', '9'),
        touch_tip_height: float = -5,
        *args,
        **kwargs
    ):
        """
        :param beads_flow_rate: pipette flow rate in ul/s for aspirate, dipsense and blow_out
        :param beads_mix_repeats: number of repetitions during mixing the beads
        :param beads_mix_volume: volume aspirated for mixing the beads in uL
        :param beads_vol: volume of beads per sample in uL
        :param lysis_volume: volume of lysis buffer per sample in uL
        :param prot_k_flow_rate: pipette flow rate in ul/s for aspirate, dispense and blow_out
        :param prot_k_headroom: headroom for proteinase K (as a multiplier)
        :param prot_k_vol: volume of proteinase K per sample in uL
        :param sample_aspirate: aspiration rate for sampeles in uL/s
        :param sample_dispense: dispensation rate for sampeles in uL/s
        :param tempdeck_temp: tempdeck temperature in Celsius degrees
        :param tipracks_slots: Slots where the tipracks are positioned
        :param tipracks_slots_20: Slots where the tipracks (20 uL) are positioned
        :param kwargs: other keyword arguments. See: StationAP1000, StationA
        """
        super(StationATechnogenetics, self).__init__(
            *args,
            lysis_first=True,       # This not an option for this protocol
            lys_mix_repeats=lys_mix_repeats,
            lys_mix_volume=lys_mix_volume,
            lys_mix_last_rate=lys_mix_last_rate,
            lysis_volume=lysis_volume,
            lysis_in_controls=lysis_in_controls,
            lysis_rate_aspirate=lysis_rate_aspirate,
            lysis_rate_dispense=lysis_rate_dispense,
            lysis_rate_mix=lysis_rate_mix,
            mix_repeats=mix_repeats,
            negative_control_well=negative_control_well,
            positive_control_well=positive_control_well,
            sample_aspirate=sample_aspirate,
            sample_dispense=sample_dispense,
            iec_volume=prot_k_vol,
            ic_capacity=prot_k_capacity,
            deepwell_headroom_bottom=deepwell_headroom_bottom,
            ic_lys_headroom=prot_k_headroom,
            tempdeck_temp=tempdeck_temp,
            tipracks_slots=tipracks_slots,
            tipracks_slots_20=tipracks_slots_20,
            **kwargs
        )
        self._beads_flow_rate = beads_flow_rate
        self._beads_mix_repeats = beads_mix_repeats
        self._beads_mix_volume = beads_mix_volume
        self._beads_vol = beads_vol
        self._strip_headroom_bottom = strip_headroom_bottom
        self._drop_threshold = drop_threshold
        self._m20_fake_aspirate = True
        self._beads_vertical_speed = beads_vertical_speed
        self._tempdeck_bool = tempdeck_bool
        self._touch_tip_height = touch_tip_height
        self._prot_k_vertical_speed = prot_k_vertical_speed
        self._prot_k_flow_rate = prot_k_flow_rate
        self._pk_tube_source = MultiTubeSource(vertical_speed=self._prot_k_vertical_speed)

    # --- In Station A there is IC in the strips, these allow the renaming for Proteinase K -------
    _strips_content: str = "proteinase K"
    
    _lys_buf_name: str = '50ml tuberack for lysis buffer'
    
    @property
    def _prot_k_capacity(self) -> float:
        return self._ic_capacity
    
    @property
    def _prot_k_headroom(self) -> float:
        return self._ic_lys_headroom
    
    @property
    def _prot_k_volume(self) -> float:
        return self._iec_volume
            
    @property
    def num_pk_strips(self) -> int:
        return self.num_ic_strips
    # ---------------------------------------------------------------------------------------------
    
    @property
    def _prot_k(self):
        return self._strips_block.rows()[0][:self.num_pk_strips]
    
    @property
    def _beads(self):
        return self._strips_block.rows()[0][-1]

    def setup_pk(self):
        pk_volume_usable_in_strip = self.num_cols * self._prot_k_volume
        volume_per_strip = pk_volume_usable_in_strip / self.num_pk_strips
        requested_volume_per_strip = volume_per_strip * self._prot_k_headroom

        self.logger.info("Proteinase K: using {} strip{} with {}ul each".format(
            self.num_pk_strips, "s" if self.num_pk_strips > 1 else "", requested_volume_per_strip))

        for i in range(self.num_pk_strips):
            self.logger.info("APPENDING {} with {}ul".format(self._prot_k[i], volume_per_strip))
            self._pk_tube_source.append_tube_with_vol(self._prot_k[i], volume_per_strip)

    def fake_aspirate(self, pip, volume, location=None):
        pip.aspirate(volume, location)
        pip.dispense(volume, location)

    def transfer_proteinase(self):
        self._m20.flow_rate.aspirate = self._prot_k_flow_rate
        self._m20.flow_rate.dispense = self._prot_k_flow_rate
        self._m20.flow_rate.blow_out = self._prot_k_flow_rate

        for i, d in enumerate(self._dests_multi):
            if self.run_stage("transfer proteinase {}/{}".format(i + 1, len(self._dests_multi))):
                if not self._m20.has_tip:
                    self.pick_up(self._m20)

                if self._m20_fake_aspirate:
                    self._m20_fake_aspirate = False
                    self.fake_aspirate(self._m20, 0.5, self._prot_k[0].top())

                self._pk_tube_source.prepare_aspiration(self._prot_k_volume, min_height=self._strip_headroom_bottom)
                self._pk_tube_source.aspirate(self._m20)

                with MoveWithSpeed(self._m20,
                                   from_point=d.bottom(self._deepwell_headroom_bottom + 5),
                                   to_point=d.bottom(self._deepwell_headroom_bottom),
                                   speed=self._prot_k_vertical_speed, move_close=False):
                    self._m20.blow_out()
                self.fake_aspirate(self._m20, 0.5, d.top())

        if self._m20.has_tip:
            self._m20.drop_tip()
    
    def transfer_beads(self, new_tip: bool=True):
        self._m20.flow_rate.aspirate = self._beads_flow_rate
        self._m20.flow_rate.dispense = self._beads_flow_rate
        self._m20.flow_rate.blow_out = self._beads_flow_rate

        for i, d in enumerate(self._dests_multi):
            remaining = len(self._dests_multi) - i
            if self.run_stage("transfer beads {}/{}".format(i + 1, len(self._dests_multi))):
                if new_tip:
                    self.transfer_beads_new_tip(d)
                else:
                    self.distribute_beads(d, remaining)
        if self._m20.has_tip:
            self._m20.drop_tip()

    def transfer_beads_new_tip(self, dest):
        self.pick_up(self._m20)

        # Fake aspiration to avoid up and down movement
        if self._m20_fake_aspirate:
            self._m20_fake_aspirate = False
            self.fake_aspirate(self._m20, 2, self._beads.top())

        with MoveWithSpeed(self._m20,
                           from_point=self._beads.bottom(self._strip_headroom_bottom + 5),
                           to_point=self._beads.bottom(self._strip_headroom_bottom),
                           speed=self._beads_vertical_speed, move_close=False):
            self._m20.aspirate(self._beads_vol)
        self._m20.air_gap(self._air_gap_dest_multi)
        self._m20.dispense(self._air_gap_dest_multi, dest.top())
        self._m20.dispense(self._beads_vol, dest.bottom(self._dest_multi_headroom_height))

        if self._beads_mix_repeats:
            self._m20.mix(self._beads_mix_repeats, self._beads_mix_volume, dest.bottom(self._dest_multi_headroom_height))

        self._m20.air_gap(self._air_gap_dest_multi)
        self._m20.drop_tip()

    def distribute_beads(self, dest, remaining: int):

        if not self._m20.has_tip:
            self.pick_up(self._m20)

        # Fake aspiration to avoid up and down movement
        if self._m20_fake_aspirate:
            self._m20_fake_aspirate = False
            self._m20.aspirate(2, self._beads.top())
            self._m20.dispense(2)

        if self._m20.current_volume < self._beads_vol:
            # we need to fill the tip
            well_per_tip = min(self._m20.max_volume // self._beads_vol, remaining)
            volume_to_aspirate = well_per_tip * self._beads_vol
            self.logger.info("We aspirate {}ul to distribute to {} well".format(volume_to_aspirate, well_per_tip))

            if self._m20.current_volume > 0:
                self._m20.blow_out(self._beads.top())

            with MoveWithSpeed(self._m20,
                               from_point=self._beads.bottom(self._strip_headroom_bottom + 5),
                               to_point=self._beads.bottom(self._strip_headroom_bottom),
                               speed=self._beads_vertical_speed, move_close=False):
                self._m20.aspirate(volume_to_aspirate)

        self._m20.dispense(self._beads_vol, dest.bottom(self._dest_multi_headroom_height))

        if self._beads_mix_repeats:
            self._m20.mix(self._beads_mix_repeats, self._beads_mix_volume, dest.bottom(self._dest_multi_headroom_height))
        # Do not drop tip, we reuse the one we have

    def body(self):
        self.setup_pk()
        self.setup_samples()
        self.setup_lys_tube()
        self.msg = ""

        self.transfer_lys()
        self.transfer_beads(new_tip=False)
        self.transfer_proteinase()
        self.transfer_samples()

        if self.run_stage("positive control"):
            self.pause("add positive control")


class StationATechnogeneticsReload(StationAReloadMixin, StationATechnogenetics):
    _protocol_description = "station A protocol for Technogenetics kit and COPAN 330C refillable samples."


class StationATechnogenetics24(StationATechnogenetics):
    _protocol_description = "station A protocol for Technogenetics kit and COPAN 330C (x24 rack)"

    def _load_source_racks(self):
        labware_def = Copan24Specs().labware_definition()
        self._source_racks = [
            self._ctx.load_labware_from_definition(
                labware_def, slot,
                'source tuberack ' + str(i + 1)
            ) for i, slot in enumerate(self._source_racks_slots)
        ]


class StationATechnogenetics48(StationATechnogeneticsReload):
    _protocol_description = "station A protocol for Technogenetics kit and COPAN 330C (x48 rack)"
    
    def __init__(
        self,
        source_racks_slots: Tuple[str, ...] = ('2',),
        *args,
        **kwargs
    ):
        super(StationATechnogenetics48, self).__init__(
            *args,
            source_racks_slots=source_racks_slots,
            **kwargs
        )
    
    def _load_source_racks(self):
        labware_def = copan_48_corrected_specs.labware_definition()
        self._source_racks = [
            self._ctx.load_labware_from_definition(
                labware_def, slot,
                'source tuberack ' + str(i + 1)
            ) for i, slot in enumerate(self._source_racks_slots)
        ]


class StationATechnogenetics48Saliva(StationATechnogenetics48):
    def __init__(
            self,
            air_gap_sample_before=200,
            deepwell_vertical_speed=25,
            deepwell_after_dispense_touch_border=True,
            drop_height=-30,
            lys_mix_repeats: int = 4,
            lys_mix_volume=500,
            lysis_mix_rate=800,
            lys_mix_last_rate=100,
            lys_mix_last_volume=200,
            sample_lateral_air_gap=25,
            sample_lateral_top_height=11,
            sample_lateral_x_move=-10,
            sample_lateral_y_move=0,
            source_headroom_height=1,
            *args,
            **kwargs
    ):
        super(StationATechnogenetics48Saliva, self).__init__(
            air_gap_sample_before=air_gap_sample_before,
            deepwell_vertical_speed=deepwell_vertical_speed,
            deepwell_after_dispense_touch_border=deepwell_after_dispense_touch_border,
            drop_height=drop_height,
            lys_mix_repeats=lys_mix_repeats,
            lys_mix_volume=lys_mix_volume,
            lysis_rate_mix=lysis_mix_rate,
            lys_mix_last_rate=lys_mix_last_rate,
            lys_mix_last_volume=lys_mix_last_volume,
            sample_lateral_air_gap=sample_lateral_air_gap,
            sample_lateral_top_height=sample_lateral_top_height,
            sample_lateral_x_move=sample_lateral_x_move,
            sample_lateral_y_move=sample_lateral_y_move,
            source_headroom_height=source_headroom_height,
            *args,
            **kwargs
        )

    def _load_source_racks(self):
        labware_def = copan_48_saliva_corrected_specs.labware_definition()
        self._source_racks = [
            self._ctx.load_labware_from_definition(
                labware_def, slot,
                'source tuberack ' + str(i + 1)
            ) for i, slot in enumerate(self._source_racks_slots)
        ]

    def transfer_sample_mix(self, well, height1: float, height2: float):
        """ Just another mixing function to have a clean tip before ejecting """
        if self._lys_mix_repeats:
            for i in range(self._lys_mix_repeats):
                if self._lys_mix_repeats > 1:
                    vol_to_mix = round((self._lys_mix_volume - self._lys_mix_last_volume) * (1 - (i/(self._lys_mix_repeats-1)))
                                       + self._lys_mix_last_volume)
                else:
                    vol_to_mix = self._lys_mix_volume

                mix_bottom_top(
                    pip=self._p_main,
                    reps=1,
                    vol=vol_to_mix,
                    pos=well.bottom,
                    bottom=height1,
                    top=height2,
                    last_dispense_rate=self._lys_mix_last_rate if i == (self._lys_mix_repeats-1) else None
                )

if __name__ == "__main__":
    StationATechnogenetics48(num_samples=96, metadata={'apiLevel': '2.7'}).simulate()


# Copyright (c) 2020 Covmatic.
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
