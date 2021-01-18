from .b import StationB, labware_loader
from typing import Tuple
from ..utils import uniform_divide
from opentrons.types import Point


class StationBTechnogenetics(StationB):
    _protocol_description = "station B protocol for Technogenetics kit"

    def __init__(self,
                 bind_max_transfer_vol: float = 200,
                 elute_mix_times: int = 15,
                 elution_vol: float = 50,
                 elute_incubate: bool = False,
                 external_deepwell_incubation: bool = True,
                 final_mix_height: float = 0.3,
                 final_mix_times: int = 5,
                 final_mix_vol: float = 20,
                 final_transfer_rate_aspirate: float = 30,
                 final_transfer_rate_dispense: float = 30,
                 final_vol: float = 20,
                 flatplate_slot: str = '3',
                 mix_incubate_on_time: float = 20,
                 mix_incubate_off_time: float = 5,
                 postspin_incubation_time: float = 3,
                 remove_wash_vol: float = 50,
                 sample_mix_height: float = 0.3,
                 sample_mix_times: float = 10,
                 sample_mix_vol: float = 180,
                 starting_vol: float = 650,
                 supernatant_removal_height: float = 0.2,
                 tempdeck_slot: str = '10',
                 tempdeck_temp: float = 60,
                 thermomixer_incubation_time: float = 5,
                 tipracks_slots: Tuple[str, ...] = ('4', '6', '7', '8', '9'),
                 wash_1_vol: float = 680,
                 wash_2_vol: float = 680,
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
        :param thermomixer_incubation_time: Time for incubation after thermomixer in minutes 
        """
        super(StationBTechnogenetics, self).__init__(
            bind_max_transfer_vol=bind_max_transfer_vol,
            elute_mix_times=elute_mix_times,
            elution_vol=elution_vol,
            elute_incubate=elute_incubate,
            flatplate_slot=flatplate_slot,
            starting_vol=starting_vol,
            supernatant_removal_height=supernatant_removal_height,
            tempdeck_slot=tempdeck_slot,
            tempdeck_temp=tempdeck_temp,
            tipracks_slots=tipracks_slots,
            wash_1_vol=wash_1_vol,
            wash_2_vol=wash_2_vol,
            **kwargs
        )
        self._external_deepwell_incubation = external_deepwell_incubation
        self._final_mix_height = final_mix_height
        self._final_mix_times = final_mix_times
        self._final_mix_vol = final_mix_vol
        self._final_transfer_rate_aspirate = final_transfer_rate_aspirate
        self._final_transfer_rate_dispense = final_transfer_rate_dispense
        self._final_vol = final_vol
        self._flatplate_slot = flatplate_slot
        self._mix_incubate_on_time = mix_incubate_on_time
        self._mix_incubate_off_time = mix_incubate_off_time
        self._postspin_incubation_time = postspin_incubation_time
        self._remove_wash_vol = remove_wash_vol
        self._sample_mix_height = sample_mix_height
        self._sample_mix_times = sample_mix_times
        self._sample_mix_vol = sample_mix_vol
        self._thermomixer_incubation_time = thermomixer_incubation_time
    
    @labware_loader(5, "_flatplate")
    def load_flatplate(self):
        self._flatplate = self._ctx.load_labware('opentrons_96_aluminumblock_nest_wellplate_100ul', self._flatplate_slot, 'chilled elution plate on block for Station C')
    
    @labware_loader(5, "_tempplate")
    def load_tempplate(self):
        self._tempplate = self._tempdeck.load_labware(self._magplate_model)
    
    @property
    def pcr_samples_m(self):
        return self._flatplate.rows()[0][:self.num_cols]
    
    @property
    def temp_samples_m(self):
        return self._tempplate.rows()[0][:self.num_cols]
    
    def load_etoh(self): pass
    
    @property
    def wash1(self):
        return self._res12.wells()[:6]
    
    @property
    def wash2(self):
        return self._res12.wells()[-6:]
    
    @labware_loader(9, "_elut12")
    def load_elut12(self):
        self._elut12 = self._ctx.load_labware('nest_12_reservoir_15ml', '2', 'Trough with Elution')
    
    @property
    def water(self):
        return self._elut12.wells()[11]
    
    @staticmethod
    def wash_getcol(sample_col_idx: int, wash_cols: int, source):
        return source[sample_col_idx // 2]
    
    def mix_samples(self):
        self._m300.flow_rate.aspirate = 94
        for i, m in enumerate(self.mag_samples_m):
            if self.run_stage("mix sample {}/{}".format(i + 1, len(self.mag_samples_m))):
                self.pick_up(self._m300)
                self._m300.mix(self._sample_mix_times, self._sample_mix_vol, m.bottom(self._sample_mix_height))
                self._m300.air_gap(self._bind_air_gap)
                self.drop(self._m300)
    
    def elute(self, positions=None, transfer: bool = False, stage: str = "elute"):
        if positions is None:
            positions = self.temp_samples_m
        self._magdeck.disengage()
        super(StationBTechnogenetics, self).elute(positions=positions, transfer=transfer, stage=stage)
        self._magdeck.disengage()
    
    def remove_wash(self, vol):
        self._magdeck.engage(height=self._magheight)
        self._m300.flow_rate.aspirate = self._supernatant_removal_aspiration_rate
        num_trans, vol_per_trans = uniform_divide(vol, self._wash_max_transfer_vol)
        
        for i, m in enumerate(self.mag_samples_m):
            if self.run_stage("remove wash {}/{}".format(i + 1, len(self.mag_samples_m))):
                self.pick_up(self._m300)
                for _ in range(num_trans):
                    if self._m300.current_volume > 0:
                        self._m300.dispense(self._m300.current_volume, m.top())  # void air gap if necessary
                    self._m300.move_to(m.center())
                    self._m300.transfer(vol_per_trans, m.bottom(self._supernatant_removal_height), self._waste, air_gap=self._supernatant_removal_air_gap, new_tip='never')
                    self._m300.air_gap(self._supernatant_removal_air_gap)
                self.drop(self._m300)
        self._m300.flow_rate.aspirate = self._default_aspiration_rate
        self._magdeck.disengage()
    
    def final_transfer(self):
        self._m300.flow_rate.aspirate = self._final_transfer_rate_aspirate
        self._m300.flow_rate.dispense = self._final_transfer_rate_dispense
        n = len(list(zip(self.mag_samples_m, self.pcr_samples_m)))
        for i, (m, e) in enumerate(zip(self.mag_samples_m, self.pcr_samples_m)):
            if self.run_stage("final transfer {}/{}".format(i + 1, n)):
                self.pick_up(self._m300)
                side = -1 if i % 2 == 0 else 1
                loc = m.bottom(0.3).move(Point(x=side*2))
                self._m300.transfer(self._final_vol, loc, e.bottom(self._elution_height), air_gap=self._elute_air_gap, new_tip='never')
                self._m300.mix(self._final_mix_times, self._final_mix_vol, e.bottom(self._final_mix_height))
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
        if self.run_stage("mix incubate off"):
            self.delay(self._mix_incubate_off_time, self.get_msg_format("incubate on magdeck", self.get_msg("on")))
        
        self.remove_supernatant(self._starting_vol)
        self.wash(self._wash_1_vol, self.wash1, self._wash_1_times, "wash 1")
        self.wash(self._wash_2_vol, self.wash2, self._wash_2_times, "wash 2")
        
        if self.run_stage("spin deepwell"):
            self._magdeck.disengage()
            self.dual_pause("spin the deepwell", between=self.set_external)
            self.set_internal()
            self._magdeck.engage(height=self._magheight)
        
        if self.run_stage("post spin incubation"):
            self.delay(self._postspin_incubation_time, self.get_msg_format("incubate on magdeck", self.get_msg("on")))
        
        self.remove_wash(self._remove_wash_vol)
        
        if self.run_stage("deepwell incubation"):
            self.dual_pause("deepwell incubation", between=self.set_external if self._external_deepwell_incubation else None)
            self.set_internal()
        
        self.elute()
        
        if self.run_stage("thermomixer"):
            self.dual_pause("seal the deepwell", between=self.set_external)
            self.set_internal()
        
        self._magdeck.engage(height=self._magheight)
        if self.run_stage("post thermomixer incubation"):
            self.delay(self._thermomixer_incubation_time, self.get_msg_format("incubate on magdeck", self.get_msg("on")))
        
        if self.run_stage("input PCR"):
            self.dual_pause("input PCR")
        
        self.final_transfer()
        
        self._magdeck.disengage()
        self.logger.info(self.msg_format("move to PCR"))


if __name__ == "__main__":
    StationBTechnogenetics(metadata={'apiLevel': '2.3'}).simulate()


# Copyright (c) 2020 Covmatic.
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
