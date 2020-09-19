from .p1000 import StationAP1000
from .reload import StationAReload
from .copan_24 import Copan24Specs


class StationATechnogenetics(StationAP1000):
    def __init__(self,
        beads_mix_repeats: int = 5,
        beads_mix_volume: float = 20,
        beads_vol: float = 10,
        chilled_tubeblock_content: str = "proteinase K (strip 1) and beads (strip 2)",
        lysis_first: bool = False,
        lysis_volume: float = 400,
        prot_k_vol: float = 30,
        sample_aspirate: float = 100,
        sample_dispense: float = 100,
        **kwargs
    ):
        """
        :param beads_mix_repeats: number of repetitions during mixing the beads
        :param beads_mix_volume: volume aspirated for mixing the beads in uL
        :param beads_vol: volume of beads per sample in uL
        :param chilled_tubeblock_content: label for the chilled tubeblock
        :param lysis_volume: volume of lysis buffer per sample in uL
        :param prot_k_vol: volume of proteinase K per sample in uL
        :param sample_aspirate: aspiration rate for sampeles in uL/s
        :param sample_dispense: dispensation rate for sampeles in uL/s
        :param kwargs: other keyword arguments. See: StationAP1000, StationA
        """
        super(StationATechnogenetics, self).__init__(
            chilled_tubeblock_content=chilled_tubeblock_content,
            lysis_first=False,
            lysis_volume=lysis_volume,
            sample_aspirate=sample_aspirate,
            sample_dispense=sample_dispense,
            **kwargs
        )
        self._beads_mix_repeats = beads_mix_repeats
        self._beads_mix_volume = beads_mix_volume
        self._beads_vol = beads_vol
        self._prot_k_vol = prot_k_vol
        if self._lysis_first != lysis_first:
            self.logger.error("lysis_first=True is not supported for this protocol")
            
    @property
    def num_ic_strips(self) -> int:
        return 2
    
    @property
    def _prot_k(self):
        return self._strips_block[0]
    
    @property
    def _beads(self):
        return self._strips_block[1]
    
    def transfer_proteinase(self):
        self.pick_up(self._m20)
        for i, d in enumerate(self._dests_multi):
            self._m20.move_to(d.top())
            # Air gap must be 'dispensed' if tip is to be reused
            if i:
                self._m20.dispense(self._air_gap_dest_multi)
            self._m20.transfer(self._prot_k_vol, self._prot_k, d.bottom(self._ic_headroom_bottom), new_tip='never')
            self._m20.air_gap(self._air_gap_dest_multi)
        self._m20.drop_tip()
    
    def transfer_beads(self):
        for i, d in enumerate(self._dests_multi):
            self.pick_up(self._m20)
            self._m20.transfer(self._beads_vol, self._beads, d.bottom(self._dest_multi_headroom_height), air_gap=self._air_gap_dest_multi, new_tip='never')
            self._m20.mix(self._beads_mix_repeats, self._beads_vol, d.bottom(self._dest_multi_headroom_height))
            self._m20.air_gap(self._air_gap_dest_multi)
            self._m20.drop_tip()
    
    def body(self):
        self.setup_samples()
        self.setup_lys_tube()
        
        self.transfer_proteinase()
        self.transfer_samples()
        self.transfer_lys()
        
        self.pause("move deepwell plate to the incubator for 20 minutes at 55°C", blink=True)
        
        self.transfer_beads()
        self.logger.info('move deepwell plate to Station B for RNA extraction.')


class StationATechnogeneticsReload(StationAReload, StationATechnogenetics):
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


if __name__ == "__main__":
    StationATechnogenetics24(num_samples=96, metadata={'apiLevel': '2.3'}).simulate()
