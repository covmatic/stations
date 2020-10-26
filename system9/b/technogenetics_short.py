from .technogenetics import StationBTechnogenetics
from typing import Tuple


class StationBTechnogeneticsElutionRemoval(StationBTechnogenetics):
    _protocol_description = "elution removal protocol for station B with Technogenetics kit"
    
    def __init__(
        self,
        bind_aspiration_rate=None,
        bind_dispense_rate=None,
        bind_blowout_rate=None,
        bottom_headroom_height: float = 0.1,
        elution_vol: float = 40,
        num_cycles: int = 1,
        tempdeck_temp = None,
        tipracks_slots: Tuple[str, ...] = ('2', '3', '5', '6', '7', '8', '9'),
        *args,
        **kwargs
    ):
        super(StationBTechnogeneticsElutionRemoval, self).__init__(
            *args,
            bind_aspiration_rate=bind_aspiration_rate,
            bind_dispense_rate=bind_dispense_rate,
            bind_blowout_rate=bind_blowout_rate,
            bottom_headroom_height=bottom_headroom_height,
            elution_vol=elution_vol,
            tempdeck_temp=tempdeck_temp,
            tipracks_slots=tipracks_slots,
            **kwargs
        )
        self._num_cycles = num_cycles
    
    def load_tempdeck(self):
        pass
    
    def load_tempplate(self):
        pass
    
    def load_res12(self):
        pass
    
    def load_elut12(self):
        pass
    
    def cycle(self, idx: int, stage: str = "cycle"):
        if self.run_stage("{} {}/{}".format(stage, idx + 1, self._num_cycles)):
            self._magdeck.engage(height=self._magheight)
            self.delay(2, self.get_msg_format("incubate on magdeck", self.get_msg("on")))
            for i, (m, e) in enumerate(zip(self.mag_samples_m, self.pcr_samples_m)):
                self.pick_up(self._m300)
                self._m300.flow_rate.aspirate = self._elute_aspiration_rate
                self._m300.transfer(self._elution_vol, m.bottom(self._bottom_headroom_height), e.bottom(self._elution_height), air_gap=self._elute_air_gap, new_tip='never')
                self.drop(self._m300)
            
            self._magdeck.disengage()
            
            if idx < self._num_cycles - 1:
                self.dual_pause("store nest reload")
            else:
                self.pause("store nest")
        
    def body(self):
        for i in range(self._num_cycles):
            self.cycle(i)
