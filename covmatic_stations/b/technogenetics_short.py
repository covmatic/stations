from .technogenetics import StationBTechnogenetics
from typing import Tuple
from itertools import repeat


class StationBTechnogeneticsShort(StationBTechnogenetics):    
    def __init__(
        self,
        air_gap_drop: float = 0,
        bind_aspiration_rate=None,
        bind_dispense_rate=None,
        bind_blowout_rate=None,
        bottom_headroom_height: float = 0.1,
        elution_vol: float = 40,
        flatplate_slot: str = '3',
        magdeck_slot: str = '1',
        num_cycles: int = 1,
        tempdeck_temp = None,
        tipracks_slots: Tuple[str, ...] = ('4', '6', '7', '8', '9'),
        *args,
        **kwargs
    ):
        super(StationBTechnogeneticsShort, self).__init__(
            *args,
            bind_aspiration_rate=bind_aspiration_rate,
            bind_dispense_rate=bind_dispense_rate,
            bind_blowout_rate=bind_blowout_rate,
            bottom_headroom_height=bottom_headroom_height,
            elution_vol=elution_vol,
            flatplate_slot=flatplate_slot,
            magdeck_slot=magdeck_slot,
            tempdeck_temp=tempdeck_temp,
            tipracks_slots=tipracks_slots,
            **kwargs
        )
        self._air_gap_drop = air_gap_drop
        self._num_cycles = num_cycles

    def load_tempdeck(self):
        pass
    
    def load_tempplate(self):
        pass
    
    def load_res12(self):
        pass
    
    def load_elut12(self):
        pass
    
    @property
    def transfer_dest(self):
        return (e.bottom(self._elution_height) for e in self.pcr_samples_m)
    
    def cycle(self, idx: int, stage: str = "cycle"):
        if self.run_stage("{} {}/{}".format(stage, idx + 1, self._num_cycles)):
            self._magdeck.engage(height=self._magheight)
            self.delay(2, self.get_msg_format("incubate on magdeck", self.get_msg("on")))
            for i, (m, e) in enumerate(zip(self.mag_samples_m, self.transfer_dest)):
                self.pick_up(self._m300)
                self._m300.flow_rate.aspirate = self._elute_aspiration_rate
                self._m300.transfer(self._elution_vol, m.bottom(self._bottom_headroom_height), e, air_gap=self._elute_air_gap, new_tip='never')
                if self._air_gap_drop:
                    self._m300.air_gap(self._air_gap_drop)
                self.drop(self._m300)
            
            self._magdeck.disengage()
            
            if idx < self._num_cycles - 1:
                self.dual_pause("end of cycle")
            else:
                self.pause("final cycle")
        
    def body(self):
        for i in range(self._num_cycles):
            self.cycle(i)


class StationBTechnogeneticsElutionRemoval(StationBTechnogeneticsShort):
    _protocol_description = "elution removal protocol for station B with Technogenetics kit"
    
    def load_waste(self):
        pass


class StationBTechnogeneticsWashBRemoval(StationBTechnogeneticsShort):
    _protocol_description = "wash B removal protocol for station B with Technogenetics kit"
    
    def __init__(
        self,
        air_gap_drop: float = 20,
        wash_b_vol: float = 55,
        *args,
        **kwargs
    ):
        super(StationBTechnogeneticsWashBRemoval, self).__init__(
            *args,
            air_gap_drop=air_gap_drop,
            elution_vol=wash_b_vol,
            **kwargs
        )
    
    def load_flatplate(self):
        pass
    
    @property
    def transfer_dest(self):
        return repeat(self._waste)
