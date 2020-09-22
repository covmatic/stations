from .b import StationB, labware_loader
from typing import Tuple


class StationBTechnogenetics(StationB):
    _protocol_description = "station B protocol for Technogenetics kit"

    def __init__(self,
                 bind_max_transfer_vol: float = 200,
                 elute_incubate: bool = False,
                 sample_mix_height: float = 0.3,
                 sample_mix_times: float = 10,
                 sample_mix_vol: float = 280,
                 starting_vol: float = 650,
                 tipracks_slots: Tuple[str, ...] = ('3', '7', '8', '9', '10'),
                 wash_1_vol: float = 680,
                 wash_2_vol: float = 680,
                 **kwargs
                 ):
        """ Build a :py:class:`.StationBTechnogenetics`.
        :param sample_mix_times: Mixing height for samples in mm from the bottom
        :param sample_mix_times: Mixing repetitions for samples
        :param sample_mix_vol: Mixing volume for samples in uL
        """
        super(StationBTechnogenetics, self).__init__(
            bind_max_transfer_vol=bind_max_transfer_vol,
            elute_incubate=elute_incubate,
            starting_vol=starting_vol,
            tipracks_slots=tipracks_slots,
            wash_1_vol=wash_1_vol,
            wash_2_vol=wash_2_vol,
            **kwargs
        )
        self._sample_mix_height = sample_mix_height
        self._sample_mix_times = sample_mix_times
        self._sample_mix_vol = sample_mix_vol
    
    def load_tempdeck(self): pass
    
    @labware_loader(5, "_flatplate")
    def load_flatplate(self):
        self._flatplate = self._ctx.load_labware('opentrons_96_aluminumblock_nest_wellplate_100ul', '1', 'chilled elution plate on block for Station C')
    
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
    
    def mix_samples(self):
        for m in self.mag_samples_m:
            self.pick_up(self._m300)
            self._m300.mix(self._sample_mix_times, self._sample_mix_vol, m.bottom(self._sample_mix_height))
            self.drop(self._m300)
    
    def elute(self):
        self._magdeck.disengage()
        self.pause("check the drying of deepwell plate")
        super(StationBTechnogenetics, self).elute()
    
    def body(self):
        self.mix_samples()
        
        self.delay(20, 'incubating off magnet at room temperature')
        self._magdeck.engage(height=self._magheight)
        self.delay(9, 'incubating on magnet at room temperature')
        
        self.remove_supernatant(self._starting_vol)
        self.wash(self._wash_1_vol, self.wash1, self._wash_1_times)
        self.wash(self._wash_2_vol, self.wash2, self._wash_2_times)
        self.elute()
        
        self._magdeck.disengage()
        self.logger.info("move chilled elution plate on block (slot 1) to Station C")


if __name__ == "__main__":
    StationBTechnogenetics(metadata={'apiLevel': '2.3'}).simulate()
