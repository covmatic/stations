from ..station import instrument_loader, labware_loader
from .c import StationC
import math
import copy
from itertools import chain, repeat
from typing import Tuple


_MM_MIX = {
    "a": 6,
    "b": 8,
    "c": 6,
}


class StationCTechnogenetics(StationC):
    _protocol_description = "station C protocol for Technogenetics kit"
    
    def __init__(
        self,
        mm_mix: dict = _MM_MIX,
        mm_strip_capacity: float = 180,
        mm_tube_capacity: float = 1800,
        pause_on_mastermix_msg: bool = True,
        source_plate_name: str = 'chilled elution plate on block for Station B',
        tempdeck_bool: bool = False,
        tiprack_slots: Tuple[str, ...] = ('2', '3', '5', '6', '8', '9', '11'),
        transfer_samples: bool = False,
        tube_block_model: str = "opentrons_24_aluminumblock_nest_2ml_screwcap",
        **kwargs
    ):
        """ Build a :py:class:`.StationCTechnogenetics`.
        :param mm_mix: Mastermix reagent quantities per sample in uL
        :param mm_strip_capacity: Capacity of one cell of the strip for mastermix in uL
        :param mm_tube_capacity: Capacity of one tube for mastermix in uL
        :param pause_on_mastermix_msg: Pause when diplaying message with mastermix composition
        :param kwargs: other keyword arguments. See: StationC, Station
        """
        super(StationCTechnogenetics, self).__init__(
            source_plate_name=source_plate_name,
            tipracks_slots=tiprack_slots,
            transfer_samples=transfer_samples,
            tube_block_model=tube_block_model,
            **kwargs
        )
        self._mm_mix = copy.deepcopy(mm_mix)
        self._mm_strip_capacity = mm_strip_capacity
        self._mm_tube_capacity = mm_tube_capacity
        self._pause_on_mastermix_msg = pause_on_mastermix_msg
        self._tempdeck_bool = tempdeck_bool
        self._transfer_samples = transfer_samples
    
    def _tipracks(self) -> dict:
        return {
            "_tips300": "_p300",
            "_tips20": "_m20",
        }
    
    def load_tips20_no_a(self): pass
    
    @property
    def mm_per_sample(self) -> float:
        return sum(self._mm_mix.values())
    
    @property
    def _mastermix_vol(self) -> float:
        return self.mm_per_sample
    
    @_mastermix_vol.setter
    def _mastermix_vol(self, ignored):
        pass
    
    @property
    def mm_capacity(self) -> float:
        return min(self._mm_tube_capacity, 8 * self._mm_strip_capacity)
    
    @property
    def num_mm_tubes(self) -> int:
        return int(math.ceil(self.mm_per_sample * self._samples_this_cycle * self._mastermix_vol_headroom / self.mm_capacity))
    
    @property
    def samples_per_mm_tube(self) -> Tuple[int, ...]:
        samples_per_mm_tube = []
        for i in range(self.num_mm_tubes):
            remaining_samples = self._samples_this_cycle - sum(samples_per_mm_tube)
            samples_per_mm_tube.append(min(8 * int(math.ceil(remaining_samples / (8 * (self.num_mm_tubes - i)))), remaining_samples))
        return tuple(samples_per_mm_tube)
    
    @property
    def mm_per_tube(self) -> Tuple[float, ...]:
        return tuple(self.mm_per_sample * self._mastermix_vol_headroom * ns for ns in self.samples_per_mm_tube)
    
    @property
    def mm_tubes(self):
        return self._tube_block.wells()[:self.num_mm_tubes]
    
    @property
    def mm_strips(self):
        return self._mm_strips.columns()[:self.num_mm_tubes]
    
    @property
    def mm_indices(self):
        return list(chain.from_iterable(repeat(i, ns) for i, ns in enumerate(self.samples_per_mm_tube)))
    
    def log_mm_mix_info(self) -> str:
        ndigs = math.ceil(math.log10(math.floor(max(self.mm_per_tube) + 1)))
        fmt = lambda n: ("{:>" + str(ndigs + 3) + "}").format("{:.2f}".format(n))
        msg = ""
        for i, (mt, mm, ns) in enumerate(zip(self.mm_tubes, self.mm_per_tube, self.samples_per_mm_tube)):
            msg += (
                "\n  {} --> {} uL".format(str(mt).split(" ")[0], fmt(mm)) +
                "".join("\n    {} -> {} uL".format(k, fmt(ns * v * self._mastermix_vol_headroom)) for k, v in self._mm_mix.items())
            )
        return self.get_msg_format("load tubes", self.num_mm_tubes, msg)
    
    def cycle_begin(self):
        super(StationCTechnogenetics, self).cycle_begin()
        self.logger.debug("samples this cycle {}".format(self._samples_this_cycle))
        self.logger.debug("num mm tubes {}".format(self.num_mm_tubes))
        msg = self.log_mm_mix_info()
        if self._pause_on_mastermix_msg and self.run_stage("mastermix info{}{}".format(" " if self.num_cycles > 1 else "", self._cycle)):
            self.dual_pause(msg, home=(False, False))
        else:
            for r in msg.split("\n"):
                while "  " in r:
                    r = r.replace("  ", "\u2007 ")
                self.logger.info(r)


class StationCTechnogeneticsM300(StationCTechnogenetics):
    # variable names are kept as before for easy inheritance
    # although pipette is now a m300 
    @labware_loader(1, "_tips20")
    def load_tips20(self):
        self._tips20 = [
            self._ctx.load_labware('opentrons_96_filtertiprack_200ul', slot)
            for slot in self._tipracks_slots
        ]
    
    @instrument_loader(0, "_m20")
    def load_m20(self):
        self._m20 = self._ctx.load_instrument('p300_multi_gen2', 'right', tip_racks=self._tips20)
        self._m20.flow_rate.aspirate = self._aspirate_rate
        self._m20.flow_rate.dispense = self._dispense_rate


if __name__ == "__main__":
    StationCTechnogenetics(num_samples=96, metadata={'apiLevel': '2.7'}).simulate()
