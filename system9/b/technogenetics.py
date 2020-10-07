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
                 final_mix_height: float = 0.3,
                 final_mix_times: int = 5,
                 final_mix_vol: float = 20,
                 final_transfer_rate_aspirate: float = 30,
                 final_transfer_rate_dispense: float = 30,
                 final_vol: float = 20,
                 sample_mix_height: float = 0.3,
                 sample_mix_times: float = 10,
                 sample_mix_vol: float = 180,
                 starting_vol: float = 650,
                 supernatant_removal_height: float = 0.2,
                 tempdeck_slot: str = '7',
                 tempdeck_temp: float = 55,
                 tipracks_slots: Tuple[str, ...] = ('3', '6', '8', '9', '10'),
                 wash_1_vol: float = 680,
                 wash_2_vol: float = 680,
                 wash_mix_aspiration_rate: float = 150,
                 wash_mix_dispense_rate: float = 150,
                 **kwargs
                 ):
        """ Build a :py:class:`.StationBTechnogenetics`.
        :param final_mix_height: Mixing height (from the bottom) for final transfer in mm
        :param final_mix_times: Mixing repetitions for final transfer
        :param final_mix_vol: Mixing volume for final transfer in uL
        :param final_transfer_rate_aspirate: Aspiration rate during final transfer in uL/s
        :param final_transfer_rate_dispense: Dispensation rate during final transfer in uL/s
        :param final_vol: Volume to transfer to the PCR plate in uL
        :param sample_mix_times: Mixing height for samples in mm from the bottom
        :param sample_mix_times: Mixing repetitions for samples
        :param sample_mix_vol: Mixing volume for samples in uL
        """
        super(StationBTechnogenetics, self).__init__(
            bind_max_transfer_vol=bind_max_transfer_vol,
            elute_mix_times=elute_mix_times,
            elution_vol=elution_vol,
            elute_incubate=elute_incubate,
            starting_vol=starting_vol,
            supernatant_removal_height=supernatant_removal_height,
            tempdeck_slot=tempdeck_slot,
            tempdeck_temp=tempdeck_temp,
            tipracks_slots=tipracks_slots,
            wash_1_vol=wash_1_vol,
            wash_2_vol=wash_2_vol,
            wash_mix_aspiration_rate=wash_mix_aspiration_rate,
            wash_mix_dispense_rate=wash_mix_dispense_rate,
            **kwargs
        )
        self._final_mix_height = final_mix_height
        self._final_mix_times = final_mix_times
        self._final_mix_vol = final_mix_vol
        self._final_transfer_rate_aspirate = final_transfer_rate_aspirate
        self._final_transfer_rate_dispense = final_transfer_rate_dispense
        self._final_vol = final_vol
        self._sample_mix_height = sample_mix_height
        self._sample_mix_times = sample_mix_times
        self._sample_mix_vol = sample_mix_vol
    
    @labware_loader(5, "_flatplate")
    def load_flatplate(self):
        self._flatplate = self._ctx.load_labware('opentrons_96_aluminumblock_nest_wellplate_100ul', '1', 'chilled elution plate on block for Station C')
    
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
        for m in self.mag_samples_m:
            self.pick_up(self._m300)
            self._m300.mix(self._sample_mix_times, self._sample_mix_vol, m.bottom(self._sample_mix_height))
            self._m300.air_gap(self._bind_air_gap)
            self.drop(self._m300)
    
    def elute(self, positions=None, transfer: bool = False):
        if positions is None:
            positions = self.temp_samples_m
        self._magdeck.disengage()
        self.pause("check the drying of deepwell plate")
        super(StationBTechnogenetics, self).elute(positions=positions, transfer=transfer)
    
    def remove_wash(self, vol):
        self._magdeck.engage(height=self._magheight)
        self._m300.flow_rate.aspirate = self._supernatant_removal_aspiration_rate
        num_trans, vol_per_trans = uniform_divide(vol, self._wash_max_transfer_vol)
        
        for i, m in enumerate(self.mag_samples_m):
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
        for i, (m, e) in enumerate(zip(self.mag_samples_m, self.pcr_samples_m)):
            self.pick_up(self._m300)
            side = -1 if i % 2 == 0 else 1
            loc = m.bottom(0.3).move(Point(x=side*2))
            self._m300.transfer(self._final_vol, loc, e.bottom(self._elution_height), air_gap=self._elute_air_gap, new_tip='never')
            self._m300.mix(self._final_mix_times, self._final_mix_vol, e.bottom(self._final_mix_height))
            self._m300.air_gap(self._elute_air_gap)
            self.drop(self._m300)
    
    def body(self):
        self.logger.info("wash 1 volume: {:.3f} mL".format(self._wash_headroom * self._wash_1_vol * self._num_samples / 1000))
        self.logger.info("wash 2 volume: {:.3f} mL".format(self._wash_headroom * self._wash_2_vol * self._num_samples / 1000))
        self.logger.info("elution volume: {:.3f} mL".format(self._wash_headroom * self._elution_vol * self._num_samples / 1000))
        self.mix_samples()
        
        self.delay(20, 'incubating off magnet at room temperature')
        self._magdeck.engage(height=self._magheight)
        self.delay(5, 'incubating on magnet at room temperature')
        
        self.remove_supernatant(self._starting_vol)
        self.wash(self._wash_1_vol, self.wash1, self._wash_1_times)
        self.wash(self._wash_2_vol, self.wash2, self._wash_2_times)
        
        self.pause("spin the deepwell plate for 20 seconds at room temperature.\nThen, put the deepwell plate back onto the magnetic module")
        
        self.remove_wash(50)
        
        self.pause("move the deepwell plate on the temperature module at 55°C.\n" +
                   "Incubate for 40 minutes, at least. Set a timer.\n" +
                   "Meanwhile, prepare the PCR plate in Station C.\n" + 
                   "Press resume to stop blinking")
        self.pause("move the deepwell plate on the temperature module at 55°C.\n" +
                   "Incubate for 40 minutes, at least. Set a timer.\n" +
                   "Meanwhile, prepare the PCR plate in Station C.\n" + 
                   "When the beads have dried completely, press resume to make the robot continue", blink=False, color='yellow', home=False)
        
        self.elute()
        
        self.pause("Seal the deepwell plate with a sticker.\n" + 
                   "Put the deepwell plate in the thermomixer at 700 rpm, 55°C for 5 minutes, at least.\n" + 
                   "When the beads are re-suspended, place the deepwell plate onto the magnetic module.\n" + 
                   "Press resume to stop blinking")
        self.pause("Seal the deepwell plate with a sticker.\n" + 
                   "Put the deepwell plate in the thermomixer at 700 rpm, 55°C for 5 minutes, at least.\n" + 
                   "When the beads are re-suspended, place the deepwell plate onto the magnetic module.\n" + 
                   "Press resume to make the robot continue", blink=False, color='yellow', home=False)
        
        self._magdeck.engage(height=self._magheight)
        self.delay(5, 'incubating on magnet at room temperature')
        
        self.pause("put the PCR plate in slot 1, onto the aluminum block.")
        
        self.final_transfer()
        
        self._magdeck.disengage()
        self.logger.info("move the PCR plate to the RT-PCR")


if __name__ == "__main__":
    StationBTechnogenetics(metadata={'apiLevel': '2.3'}).simulate()


# Copyright (c) 2020 Covmatic.
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
