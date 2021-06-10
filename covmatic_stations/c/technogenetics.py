from ..station import instrument_loader, labware_loader
from .c import StationC
from ..multi_tube_source import MultiTubeSource
import math
import copy
from itertools import chain, repeat
from typing import Tuple

from ..utils import uniform_divide

_MM_MIX = {
    "a": 6,
    "b": 8,
    "c": 6,
}


class StationCTechnogenetics(StationC):
    _protocol_description = "station C protocol for Technogenetics kit"
    
    def __init__(
        self,
        control_well_positions=['G12', 'H12'],
        headroom_vol_from_tubes_to_pcr = 60,
        max_vol_200ul_tip = 180,
        mm_mix: dict = _MM_MIX,
        mm_strip_capacity: float = 180,
        mm_tube_capacity: float = 1800,
        vol_mm_offset = 10,
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
        self._control_well_positions = control_well_positions
        self._headroom_vol_from_tubes_to_pcr = headroom_vol_from_tubes_to_pcr
        self._max_vol_200ul_tip = max_vol_200ul_tip
        self._mm_mix = copy.deepcopy(mm_mix)
        self._mm_strip_capacity = mm_strip_capacity
        self._mm_tube_capacity = mm_tube_capacity
        self._vol_mm_offset = vol_mm_offset
        self._pause_on_mastermix_msg = pause_on_mastermix_msg
        self._tempdeck_bool = tempdeck_bool
        self._transfer_samples = transfer_samples
        self._mm_tube_source = MultiTubeSource()
        self._num_mm_tubes = 0      # To be calculated afterward
        self._vol_per_tube = 0      # To be calculated afterward
        self._samples_per_mm_tube = 0  # To be calculated afterward
    
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
    #
    # @property
    # def num_mm_tubes(self) -> int:
    #     return int(math.ceil(self.mm_per_sample * self._samples_this_cycle * self._mastermix_vol_headroom / self.mm_capacity))

    # @property
    # def samples_per_mm_tube(self) -> Tuple[int, ...]:
    #     samples_per_mm_tube = []
    #     for i in range(self.num_mm_tubes):
    #         remaining_samples = self._samples_this_cycle - sum(samples_per_mm_tube)
    #         samples_per_mm_tube.append(min(8 * int(math.ceil(remaining_samples / (8 * (self.num_mm_tubes - i)))), remaining_samples))
    #     return tuple(samples_per_mm_tube)
    
    # @property
    # def mm_per_tube(self) -> Tuple[float, ...]:
    #     return tuple(self.mm_per_sample * self._mastermix_vol_headroom * ns for ns in self.samples_per_mm_tube)
    
    @property
    def mm_tubes(self):
        return self._tube_block.wells()[:self._num_mm_tubes]
    
    # @property
    # def mm_strips(self):
    #     return self._mm_strips.columns()[:self.num_mm_tubes]
    
    # @property
    # def mm_indices(self):
    #     return list(chain.from_iterable(repeat(i, ns) for i, ns in enumerate(self.samples_per_mm_tube)))

    @property
    def pcr_plate_wells(self):
        return self._pcr_plate.wells()[:self._num_samples]

    def is_well_in_samples(self, well):
        """
        Function that check if a well is within the samples well.
        :param well: well to check
        :return: True if the well is included in the samples list.
        """
        return well in self.pcr_plate_wells


    @property
    def control_wells(self):
        return [self._pcr_plate.wells_by_name()[i] for i in self._control_well_positions]


    @property
    def control_wells_not_in_samples(self):
        """
        :return: a list of wells for controls that are not already filled with the 8-channel pipette
        """
        return [c for c in self.control_wells if not self.is_well_in_samples(c)]


    def log_mm_mix_info(self) -> str:
        ndigs = math.ceil(math.log10(math.floor(self._vol_per_tube + 1)))
        fmt = lambda n: ("{:>" + str(ndigs + 3) + "}").format("{:.2f}".format(n))
        msg = ""
        for i, (mt, mm, ns) in enumerate(zip(self.mm_tubes, repeat(self._vol_per_tube), repeat(self._samples_per_mm_tube))):
            msg += (
                "\n  {} --> {} uL".format(str(mt).split(" ")[0], fmt(mm)) +
                "".join("\n    {} -> {} uL".format(k, fmt(ns * v * self._mastermix_vol_headroom)) for k, v in self._mm_mix.items())
            )
        return self.get_msg_format("load tubes", self._num_mm_tubes, msg)

    def transfer_mm_setup(self):
        volume_for_controls = len(self.control_wells_not_in_samples) * self._mastermix_vol
        volume_for_samples = self._mastermix_vol * self._num_samples
        volume_to_distribute_to_pcr_plate = volume_for_samples + volume_for_controls
        self._num_mm_tubes, self._vol_per_tube = uniform_divide(
            volume_to_distribute_to_pcr_plate + self._headroom_vol_from_tubes_to_pcr, self._mm_tube_capacity)
        self._samples_per_mm_tube = math.floor(self._vol_per_tube / self._mastermix_vol)
        mm_tubes = self._tube_block.wells()[:self._num_mm_tubes]
        available_volume = volume_to_distribute_to_pcr_plate / len(mm_tubes)
        if self._headroom_vol_from_tubes_to_pcr > 0:
            if self._vol_mm_offset < (self._headroom_vol_from_tubes_to_pcr / len(mm_tubes)):
                available_volume += self._vol_mm_offset
        assert self._vol_per_tube > available_volume, \
            "Error in volume calculations: requested {}ul while total in tubes {}ul".format(available_volume,
                                                                                            self._vol_per_tube)

        [self._mm_tube_source.append_tube_with_vol(t, available_volume) for t in
         self._tube_block.wells()[:self._num_mm_tubes]]

        self.logger.info("We need {} tubes with {}ul of mastermix each in {}".format(self._num_mm_tubes,
                                                                                     self._vol_per_tube,
                                                                                     self._mm_tube_source.locations_str))
        mmix_requirements = self.get_msg_format("load mm tubes",
                                                self._num_mm_tubes,
                                                self._vol_per_tube,
                                                self._mm_tube_source.locations_str)

        control_positions = self.get_msg_format("control positions",
                                                self._control_well_positions)

    def transfer_mm(self, stage = ""):
        done_samples = 0
        num_cycle = 1
        num_samples_per_fill = 8

        samples_with_controls = self.pcr_plate_wells
        samples_with_controls += self.control_wells_not_in_samples

        self.logger.info("Trasferring mastermix from tube to pcr plate")

        self.pick_up(self._p300)
        while done_samples < self._num_samples + len(self.control_wells_not_in_samples):
            samples_to_do = samples_with_controls[done_samples:(done_samples + num_samples_per_fill)]
            # self.logger.info("Cycle {} - samples to do: {}".format(num_cycle, samples_to_do))
            # self.logger.info("MM:Cycle {} - before filling: samples done: {}, samples to do: {}".format(num_cycle,
            #                                                                     done_samples, len(samples_to_do)))
            if num_cycle > 1:
                self._vol_mm_offset = 0
            vol_mm = (len(samples_to_do) * self._mastermix_vol) + self._vol_mm_offset
            self._mm_tube_source.calculate_aspirate_volume(vol_mm)
            self._mm_tube_source.aspirate(self._p300, self._tube_bottom_headroom_height)
            # self.logger.info("Aspirating at: {} mm".format(self._mm_tube_bottom_height))
            for s in samples_to_do:
                self._p300.dispense(self._mastermix_vol, s.bottom(self._pcr_bottom_headroom_height))
            done_samples += num_samples_per_fill
            # self.logger.info("MM:Cycle {} - after distribution: samples done: {}".format(num_cycle, done_samples))
            num_cycle += 1
        if self._p300.has_tip:
            self.drop(self._p300)

    def fill_mm_strips(self):
        pass

    def fill_control(self):
        pass

    def cycle_begin(self):
        super(StationCTechnogenetics, self).cycle_begin()
        self.transfer_mm_setup()
        self.logger.debug("samples this cycle {}".format(self._samples_this_cycle))
        self.logger.debug("num mm tubes {}".format(self._num_mm_tubes))
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
    StationCTechnogenetics(num_samples=96, metadata={'apiLevel': '2.3'}).simulate()