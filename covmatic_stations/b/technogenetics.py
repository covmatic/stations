from .b import StationB, labware_loader
from typing import Tuple
from opentrons.types import Point
from ..utils import get_labware_json_from_filename


class StationBTechnogenetics(StationB):
    _protocol_description = "station B protocol for Technogenetics kit"

    def __init__(self,
                 elute_mix_times: int = 0,
                 elution_vol: float = 50,
                 elute_incubate: bool = False,
                 external_deepwell_incubation: bool = True,
                 final_mix_height: float = 0.5,
                 final_mix_times: int = 5,
                 final_mix_vol: float = 20,
                 final_mix_blow_out_height: float = -2,
                 final_transfer_rate_aspirate: float = 30,
                 final_transfer_rate_dispense: float = 30,
                 final_transfer_side: float = 0.5,
                 final_transfer_dw_bottom_height: float = 0.6,
                 final_vol: float = 20,
                 flatplate_slot: str = '3',
                 h_bottom: float = 1,
                 n_bottom: float = 3,
                 mix_incubate_on_time: float = 20,
                 mix_incubate_off_time: float = 5,
                 postspin_incubation_time: float = 3,
                 remove_wash_vol: float = 50,
                 sample_mix_height: float = 0.3,
                 sample_mix_times: float = 10,
                 sample_mix_vol: float = 180,
                 sample_vertical_speed: float = 35,
                 mix_samples_rate_aspirate = 200,
                 mix_samples_rate_dispense = 200,
                 starting_vol: float = 650,
                 supernatant_removal_aspiration_rate_first_phase = 94,
                 tempdeck_slot: str = '10',
                 tempdeck_temp: float = 60,
                 tempdeck_auto_turnon: bool = False,
                 tempdeck_auto_turnoff: bool = True,
                 thermomixer_incubation_time: float = 5,
                 tipracks_slots: Tuple[str, ...] = ('4', '6', '7', '8', '9'),
                 wash_1_vol: float = 650,
                 wash_2_vol: float = 650,
                 wash_headroom: float = 1.05,
                 watchdog_serial_timeout_seconds: int = 30,
                 **kwargs
                 ):
        """ Build a :py:class:`.StationBTechnogenetics`.
        :param external_deepwell_incubation: whether or not to perform deepwell incubation outside the robot
        :param final_mix_height: Mixing height (from the bottom) for final transfer in mm
        :param final_mix_times: Mixing repetitions for final transfer
        :param final_mix_vol: Mixing volume for final transfer in uL
        :param final_transfer_rate_aspirate: Aspiration rate during final transfer in uL/s
        :param final_transfer_rate_dispense: Dispensation rate during final transfer in uL/s
        :param final_vol: Volume to transfer to the PCR plate in uL
        :param mix_incubate_on_time: Time for incubation on magnet after mix in minutes 
        :param mix_incubate_off_time: Time for incubation off magnet after mix in minutes
        :param postspin_incubation_time: Post-spin incubation time in minutes
        :param remove_wash_vol: Volume to remove during wash removal in uL
        :param sample_mix_times: Mixing height for samples in mm from the bottom
        :param sample_mix_times: Mixing repetitions for samples
        :param sample_mix_vol: Mixing volume for samples in uL
        :param sample_vertical_speed: speed of vertical movement exiting well
        :param thermomixer_incubation_time: Time for incubation after thermomixer in minutes
        """
        super(StationBTechnogenetics, self).__init__(
            elute_mix_times=elute_mix_times,
            elution_vol=elution_vol,
            elute_incubate=elute_incubate,
            flatplate_slot=flatplate_slot,
            starting_vol=starting_vol,
            supernatant_removal_aspiration_rate_first_phase = supernatant_removal_aspiration_rate_first_phase,
            tempdeck_slot=tempdeck_slot,
            tempdeck_temp=tempdeck_temp,
            tempdeck_auto_turnon=tempdeck_auto_turnon,
            tempdeck_auto_turnoff=tempdeck_auto_turnoff,
            tipracks_slots=tipracks_slots,
            wash_1_vol=wash_1_vol,
            wash_2_vol=wash_2_vol,
            wash_headroom=wash_headroom,
            **kwargs
        )
        self._external_deepwell_incubation = external_deepwell_incubation
        self._final_mix_blow_out_height = final_mix_blow_out_height
        self._final_mix_height = final_mix_height
        self._final_mix_times = final_mix_times
        self._final_transfer_side = final_transfer_side
        self._final_transfer_dw_bottom_height = final_transfer_dw_bottom_height
        self._final_mix_vol = final_mix_vol
        self._final_transfer_rate_aspirate = final_transfer_rate_aspirate
        self._final_transfer_rate_dispense = final_transfer_rate_dispense
        self._mix_samples_rate_aspirate = mix_samples_rate_aspirate
        self._mix_samples_rate_dispense = mix_samples_rate_dispense
        self._final_vol = final_vol
        self._flatplate_slot = flatplate_slot
        self._h_bottom = h_bottom
        self._n_bottom = n_bottom
        self._mix_incubate_on_time = mix_incubate_on_time
        self._mix_incubate_off_time = mix_incubate_off_time
        self._postspin_incubation_time = postspin_incubation_time
        self._remove_wash_vol = remove_wash_vol
        self._sample_mix_height = sample_mix_height
        self._sample_mix_times = sample_mix_times
        self._sample_mix_vol = sample_mix_vol
        self._sample_vertical_speed = sample_vertical_speed
        self._thermomixer_incubation_time = thermomixer_incubation_time
        self._watchdog_serial_timeout_seconds = watchdog_serial_timeout_seconds
    
    @labware_loader(5, "_flatplate")
    def load_flatplate(self):
        self._flatplate = self._ctx.load_labware('opentrons_96_aluminumblock_nest_wellplate_100ul', self._flatplate_slot, 'chilled elution plate on block for Station C')
    
    @labware_loader(5, "_tempplate")
    def load_tempplate(self):
        self._tempplate = self._tempdeck.load_labware(self._magplate_model)

    @labware_loader(6, "_waste")
    def load_waste(self):
        self._waste = self._ctx.load_labware_from_definition(
            get_labware_json_from_filename("biofil_3_reservoir_200000ul.json"), '11', 'Liquid Waste').wells()[0].top()

    @property
    def pcr_samples_m(self):
        return self._flatplate.rows()[0][:self.num_cols]
    
    @property
    def temp_samples_m(self):
        return self._tempplate.rows()[0][:self.num_cols]
    
    def load_etoh(self): pass

    @labware_loader(9, "_elut12")
    def load_elut12(self):
        self._elut12 = self._ctx.load_labware('nest_12_reservoir_15ml', '2', 'Trough with Wash B and Elution')

    @property
    def water(self):
        return self._elut12.wells()[11]

    @property
    def wash1(self):
        return self._res12.wells()[:6]
    
    @property
    def wash2(self):
        return self._elut12.wells()[:6]

    
    @staticmethod
    def wash_getcol(sample_col_idx: int, wash_cols: int, source):
        return source[sample_col_idx // 2]
    
    def mix_samples(self):
        self._m300.flow_rate.aspirate = self._mix_samples_rate_aspirate
        self._m300.flow_rate.dispense = self._mix_samples_rate_dispense
        for i, m in enumerate(self.mag_samples_m):
            if self.run_stage("mix sample {}/{}".format(i + 1, len(self.mag_samples_m))):
                self.pick_up(self._m300)
                self._m300.mix(self._sample_mix_times, self._sample_mix_vol, m.bottom(self._sample_mix_height))
                self._m300.move_to(m.top(0), speed=self._sample_vertical_speed)
                self._m300.air_gap(self._bind_air_gap)
                self.drop(self._m300)
    
    def elute(self, positions=None, transfer: bool = False, stage: str = "elute"):
        if positions is None:
            positions = self.temp_samples_m
        self._magdeck.disengage()
        super(StationBTechnogenetics, self).elute(positions=positions, transfer=transfer, stage=stage)
        self._magdeck.disengage()
    
    def remove_wash(self, vol, stage: str = "remove wash"):
        self.remove_supernatant(vol, stage)
    
    def final_transfer(self):
        self._m300.flow_rate.aspirate = self._final_transfer_rate_aspirate
        self._m300.flow_rate.dispense = self._final_transfer_rate_dispense
        n = len(list(zip(self.mag_samples_m, self.pcr_samples_m)))

        for i, (m, e) in enumerate(zip(self.mag_samples_m, self.pcr_samples_m)):
            if self.run_stage("final transfer {}/{}".format(i + 1, n)):
                self.pick_up(self._m300)
                side = -1 if i % 2 == 0 else 1
                loc = m.bottom(self._final_transfer_dw_bottom_height).move(Point(x=side*self._final_transfer_side))
                self._m300.aspirate(self._final_vol, loc)
                self._m300.air_gap(self._elute_air_gap)
                self._m300.dispense(self._elute_air_gap, e.top())
                self._m300.dispense(self._m300.current_volume, e.bottom(self._final_mix_height))

                #self._m300.transfer(self._final_vol, loc, e.bottom(self._elution_height), air_gap=self._elute_air_gap, new_tip='never')
                self._m300.mix(self._final_mix_times, self._final_mix_vol, e.bottom(self._final_mix_height))
                self._m300.blow_out(e.top(self._final_mix_blow_out_height))
                self._m300.air_gap(self._elute_air_gap)
                self.drop(self._m300)

    def body(self):
        self.logger.info(self.get_msg_format("volume", "wash 1", self._wash_headroom * self._wash_1_vol * self._num_samples / 1000))
        self.logger.info(self.get_msg_format("volume", "wash 2", self._wash_headroom * self._wash_2_vol * self._num_samples / 1000))
        self.logger.info(self.get_msg_format("volume", "elution buffer", self._wash_headroom * self._elution_vol * self._num_samples / 1000))
        self.mix_samples()
        
        if self.run_stage("mix incubate on"):
            self.delay(self._mix_incubate_on_time, self.get_msg_format("incubate on magdeck", self.get_msg("off")))
        self._magdeck.engage(height=self._magheight)
        self.check()
        if self.run_stage("mix incubate off"):
            self.delay(self._mix_incubate_off_time, self.get_msg_format("incubate on magdeck", self.get_msg("on")))
        
        self.remove_supernatant(self._starting_vol)
        self.wash(self._wash_1_vol, self.wash1, self._wash_1_times, "wash A")

        if self.run_stage("spin deepwell wash A"):
            self._magdeck.disengage()
            self.dual_pause("spin the deepwell", between=self.set_external)
            self.set_internal()
            self._magdeck.engage(height=self._magheight)
            self.check()

        if self.run_stage("post spin incubation wash A"):
            self.delay(self._postspin_incubation_time, self.get_msg_format("incubate on magdeck", self.get_msg("on")))

        self.remove_wash(self._remove_wash_vol, "remove wash A after spin")

        if self.run_stage("remove wash A"):
            self._magdeck.disengage()
            self.dual_pause("Check Wash A removal and empty waste reservoir")

        self.wash(self._wash_2_vol, self.wash2, self._wash_2_times, "wash B")
        
        if self.run_stage("spin deepwell wash B"):
            self._magdeck.disengage()
            self.dual_pause("spin the deepwell", between=self.set_external)
            self.set_internal()
            self._magdeck.engage(height=self._magheight)
            self.check()
        
        if self.run_stage("post spin incubation wash B"):
            self.delay(self._postspin_incubation_time, self.get_msg_format("incubate on magdeck", self.get_msg("on")))

        if self._tempdeck_temp is not None and not self._tempdeck_auto_turnon:
            # self._tempdeck.start_set_temperature(self._tempdeck_temp)
            self.tempdeck_set_temperature(self._tempdeck_temp)

        self.remove_wash(self._remove_wash_vol, "remove wash B after spin")

        if self.run_stage("remove wash B"):
            self._magdeck.disengage()
            self.dual_pause("Check Wash B removal and empty waste reservoir")

        if self.run_stage("deepwell incubation"):
            self.dual_pause("deepwell incubation", between=self.set_external if self._external_deepwell_incubation else None)
            self.set_internal()
        
        self.elute()
        
        if self.run_stage("thermomixer"):
            self.dual_pause("seal the deepwell", between=self.set_external)
            self.set_internal()
        
        self._magdeck.engage(height=self._magheight)
        self.check()
        if self.run_stage("post thermomixer incubation"):
            self.delay(self._thermomixer_incubation_time, self.get_msg_format("incubate on magdeck", self.get_msg("on")))
        
        if self.run_stage("input PCR"):
            self.dual_pause("input PCR")
        
        self.final_transfer()
        
        self._magdeck.disengage()
        self.logger.info(self.msg_format("move to PCR"))

    def tempdeck_set_temperature(self, temperature):
        self.watchdog_reset(self._watchdog_serial_timeout_seconds)
        self._tempdeck.start_set_temperature(temperature)
        self.watchdog_stop()

    def tempdeck_deactivate(self):
        self.watchdog_reset(self._watchdog_serial_timeout_seconds)
        self._tempdeck.deactivate()
        self.watchdog_stop()

if __name__ == "__main__":
    StationBTechnogenetics(metadata={'apiLevel': '2.3'}).simulate()


# Copyright (c) 2020 Covmatic.
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
