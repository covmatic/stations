from .p1000 import StationAP1000
from .reload import StationAReload
from .copan_24 import Copan24Specs
from typing import Tuple, Optional


class StationATechnogenetics(StationAP1000):
    def __init__(self,
        beads_mix_repeats: int = 2,
        beads_mix_volume: float = 20,
        beads_vol: float = 10,
        lysis_first: bool = False,
        lys_mix_repeats: int = 2,
        lys_mix_volume: float = 100,
        lysis_volume: float = 400,
        mix_repeats: int = 1,
        prot_k_capacity: float = 180,
        prot_k_headroom: float = 1.1,
        prot_k_vol: float = 30,
        sample_aspirate: float = 100,
        sample_dispense: float = 100,
        tempdeck_temp: Optional[float] = None,
        tipracks_slots: Tuple[str, ...] = ('8', '9'),
        tipracks_slots_20: Tuple[str, ...] = ('7', '11'),
        **kwargs
    ):
        """
        :param beads_mix_repeats: number of repetitions during mixing the beads
        :param beads_mix_volume: volume aspirated for mixing the beads in uL
        :param beads_vol: volume of beads per sample in uL
        :param lysis_volume: volume of lysis buffer per sample in uL
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
            lysis_first=False,
            lys_mix_repeats=lys_mix_repeats,
            lys_mix_volume=lys_mix_volume,
            lysis_volume=lysis_volume,
            mix_repeats=mix_repeats,
            sample_aspirate=sample_aspirate,
            sample_dispense=sample_dispense,
            iec_volume=prot_k_vol,
            ic_capacity=prot_k_capacity,
            ic_lys_headroom=prot_k_headroom,
            tempdeck_temp=tempdeck_temp,
            tipracks_slots=tipracks_slots,
            tipracks_slots_20=tipracks_slots_20,
            **kwargs
        )
        self._beads_mix_repeats = beads_mix_repeats
        self._beads_mix_volume = beads_mix_volume
        self._beads_vol = beads_vol
        if self._lysis_first != lysis_first:
            self.logger.error("lysis_first=True is not supported for this protocol")
    
    # --- In Station A there is IC in the strips, these allow the renaming for Proteinase K -------
    _strips_content: str = "proteinase K"
    
    _lys_buf_name: str = '50ml tuberack for lysis buffer'
    
    @property
    def chilled_tubeblock_content(self) -> str:
        return "proteinase K (first {} strips{}) and beads (last strip)".format(self.num_ic_strips, "{}")
    
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
    
    def transfer_proteinase(self):
        self.stage = "transfer proteinase"
        self.pick_up(self._m20)
        for i, d in enumerate(self._dests_multi):
            self.stage = "transfer proteinase {}/{}".format(i + 1, len(self._dests_multi))
            self._m20.transfer(self._prot_k_volume, self._prot_k[i // self.cols_per_strip], d.bottom(self._ic_headroom_bottom), new_tip='never')
        self._m20.drop_tip()
    
    def transfer_beads(self):
        for i, d in enumerate(self._dests_multi):
            self.stage = "transfer beads {}/{}".format(i + 1, len(self._dests_multi))
            self.pick_up(self._m20)
            self._m20.transfer(self._beads_vol, self._beads, d.bottom(self._dest_multi_headroom_height), air_gap=self._air_gap_dest_multi, new_tip='never')
            self._m20.mix(self._beads_mix_repeats, self._beads_mix_volume, d.bottom(self._dest_multi_headroom_height))
            self._m20.air_gap(self._air_gap_dest_multi)
            self._m20.drop_tip()
    
    def body(self):
        self.setup_samples()
        self.setup_lys_tube()
        
        self.transfer_proteinase()
        self.transfer_samples()
        self.transfer_lys()
        
        self.stage = "incubation"
        self.msg = "Seal the deepwell plate with a sticker.\n" + \
                   "Put the deepwell plate in the thermomixer: 700 rpm for 3 minutes.\n" + \
                   "Finally, move the deepwell plate in the incubator at 55°C for 20 minutes.\n" + \
                   "(Resume to stop blinking)"
        self.pause(self.msg)
        self.msg = "\n".join(self.msg.split("\n")[:-1])
        self.external = True
        self.pause(self.msg, blink=False)
        self.msg = None
        self.external = False
        
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


# Copyright (c) 2020 Covmatic.
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
