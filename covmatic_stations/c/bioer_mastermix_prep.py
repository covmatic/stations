from ..multi_tube_source import MultiTubeSource
from ..utils import uniform_divide
from .technogenetics import StationCTechnogenetics
import logging


class StationCBioerMastermixPrep(StationCTechnogenetics):
    _protocol_description = "Bioer mastermix preparation protocol"

    def __init__(self,
            aspirate_rate: float = 30,
            debug_mode: bool = False,
            tube_bottom_headroom_height: float = 4.0,
            strip_bottom_headroom_height: float = 4.0,
            pcr_bottom_headroom_height: float = 4.5,
            dispense_rate: float = 30,
            mastermix_vol: float = 20,
            mastermix_vol_headroom: float = 60,
            mastermix_headroom_part_in_strip: float = 0.7,
            mm_tube_capacity = 1800,
            num_samples: int = 96,
            control_well_positions = ['A12', 'H12'],
            skip_delay: bool = False,
            source_plate_name: str = 'Clean PCR plate on block ',
            tube_block_model: str = "opentrons_24_aluminumblock_nest_1.5ml_screwcap",
            ** kwargs

        ):
        """ Build a :py:class:`.StationC`.
        :param aspirate_rate: Aspiration rate in uL/s
        :param tube_bottom_headroom_height: Height to keep from the bottom for mastermix tubes
        :param strip_bottom_headroom_height: Height to keep from the bottom for the strips
        :param pcr_bottom_headroom_height: Height to keep from the bottom for the output pcr plate
        :param dispense_rate: Dispensation rate in uL/s
        :param drop_loc_l: offset for dropping to the left side (should be positive) in mm
        :param drop_loc_r: offset for dropping to the right side (should be negative) in mm
        :param drop_threshold: the amount of dropped tips after which the run is paused for emptying the trash
        :param logger: logger object. If not specified, the default logger is used that logs through the ProtocolContext comment method
        :param mastermix_vol: Mastermix volume per sample in uL
        :param mastermix_vol_headroom: Headroom for mastermix preparation volume to add to needed volume
        :param metadata: protocol metadata
        :param num_samples: The number of samples that will be loaded on the station B
        :param control_well_positions: Position of the control wells to be filled with mastermix
        :param samples_per_col: The number of samples in a column of the destination plate
        :param source_plate_name: Name for the source plate
        :param skip_delay: If True, pause instead of delay.
        :param tube_block_model: Tube block model name
        """
        super(StationCBioerMastermixPrep, self).__init__(
            mm_tube_capacity = mm_tube_capacity,
            num_samples = num_samples,
            skip_delay = skip_delay,
            tube_block_model = tube_block_model,
            source_plate_name = source_plate_name,
            aspirate_rate = aspirate_rate,
            dispense_rate = dispense_rate,
            ** kwargs
        )
        self._debug_mode = debug_mode
        self._tube_bottom_headroom_height = tube_bottom_headroom_height
        self._strip_bottom_headroom_height = strip_bottom_headroom_height
        self._pcr_bottom_headroom_height = pcr_bottom_headroom_height
        self._mastermix_vol = mastermix_vol
        self._mastermix_vol_headroom = mastermix_vol_headroom

        assert 0 <= mastermix_headroom_part_in_strip <= 1, \
            "Mastermix headroom in strip part must be between or equal to 0 and 1"
        self._mastermix_headroom_part_in_strip = mastermix_headroom_part_in_strip
        self._control_well_positions = control_well_positions

        self._remaining_samples = self._num_samples
        self._done_cols: int = 0
        self._mastermix_volume_in_tip = 0       # Volume of mastermix passed present in p300 tip before distributing to strips
        self._mm_sources = MultiTubeSource("Mastermix tubes", self.logger)

    @property
    def sample_dests_wells(self):
        return self._pcr_plate.wells()[:self.num_cols*8]

    @property
    def remaining_cols(self):
        return self.num_cols - self._done_cols

    @property
    def mm_strip(self):
        # We use only one column
        return self._mm_strips.columns()[0]

    @property
    def headroom_from_strip_to_pcr(self):
        return ((self._mastermix_vol_headroom - 1.0) / 2) + 1.0

    @property
    def headroom_vol_from_strip_to_pcr(self):
        return self._mastermix_vol_headroom * self._mastermix_headroom_part_in_strip

    @property
    def headroom_vol_from_strip_to_pcr_single(self):
        return self.headroom_vol_from_strip_to_pcr / 8

    @property
    def headroom_vol_from_tubes_to_strip(self):
        return self._mastermix_vol_headroom * (1 - self._mastermix_headroom_part_in_strip)

    @property
    def control_dests_wells(self):
        return [self._pcr_plate.wells_by_name()[i] for i in self._control_well_positions]  # controlli in posizione A12 e H12

    def is_well_in_samples(self, well):
        """
        Function that check if a well is within the samples well.
        :param well: well to check
        :return: True if the well is included in the samples list.
        """
        return well in self.sample_dests_wells

    @property
    def control_wells_not_in_samples(self):
        """
        :return: a list of wells for controls that are not already filled with the 8-channel pipette
        """
        return [c for c in self.control_dests_wells if not self.is_well_in_samples(c)]

    def fill_strip(self, volume):
        if not self._p300.has_tip:
            self.pick_up(self._p300)

        total_vol = volume * 8
        self.logger.debug("Filling strips with {}ul each; used volume: {}".format(volume, total_vol))

        for well in self.mm_strip:
            self._mm_sources.prepare_aspiration(volume - self._mastermix_volume_in_tip, self._tube_bottom_headroom_height)
            self._mm_sources.aspirate(self._p300)
            self._mastermix_volume_in_tip = 0   # only doing the first time
            self._p300.dispense(volume, well.bottom(self._strip_bottom_headroom_height))

        self.drop(self._p300)


    def fill_controls(self, dead_volume: float = 0):

        if len(self.control_wells_not_in_samples) > 0:
            self.logger.info(self.msg_format("fill control", self.control_wells_not_in_samples))
            if not self._p300.has_tip:
                self.pick_up(self._p300)

            vol = self._mastermix_vol * len(self.control_wells_not_in_samples) + dead_volume
            self._mm_sources.prepare_aspiration(vol, self._tube_bottom_headroom_height)
            self._mm_sources.aspirate(self._p300)

            for w in self.control_dests_wells:
                self._p300.dispense(self._mastermix_vol, w.bottom(self._pcr_bottom_headroom_height))

            assert self._p300.current_volume == dead_volume, \
                "Please verify: dead volume in tip is not as expected. in tip {}, expected {}".format(
                    self._p300.current_volume, dead_volume)

            self._mastermix_volume_in_tip = dead_volume     # Saving volume, eventually it will be disposed to strip...
        else:
            self.logger.info(self.get_msg("controls already filled"))

    def transfer_to_pcr_plate_and_mark_done(self, num_columns: int):
        num_columns = int(num_columns)
        self.logger.info("Transferring to pcr place {:d} columns.".format(num_columns))
        self.pick_up(self._m20)
        for s in self.get_next_pcr_plate_dests(num_columns):
            self._m20.transfer(self._mastermix_vol,
                               self.mm_strip[0].bottom(self._strip_bottom_headroom_height),
                               s.bottom(self._pcr_bottom_headroom_height),
                               new_tip='never')
        self.drop(self._m20)

    def get_next_pcr_plate_dests(self, num_columns: int):
        if self._done_cols < self.num_cols:
            to_do = int(min(self.num_cols - self._done_cols, num_columns))
        else:
            raise Exception("No more columns to do")
        samples_to_do = self.sample_dests[self._done_cols:self._done_cols+to_do]
        self._done_cols += to_do
        return samples_to_do

    def body(self):
        volume_for_controls = len(self.control_wells_not_in_samples) * self._mastermix_vol
        volume_for_samples = self._mastermix_vol * self.num_cols * 8
        volume_to_distribute_to_pcr_plate = volume_for_samples + volume_for_controls
        volume_to_distribute_to_strip = volume_for_samples + self.headroom_vol_from_strip_to_pcr

        total_volume = volume_to_distribute_to_strip + volume_for_controls + self.headroom_vol_from_tubes_to_strip
        self.logger.info("For this run we need a total of {}ul of mastermix".format(total_volume))

        num_tubes, vol_per_tube = uniform_divide(total_volume, self._mm_tube_capacity)
        mm_tubes = self._tube_block.wells()[:num_tubes]

        # Filling source class to calculate where to aspirate
        available_volume = (volume_to_distribute_to_strip + volume_for_controls) / len(mm_tubes)
        assert vol_per_tube > available_volume, \
            "Error in volume calcuations: requested {}ul while total in tubes {}ul".format(available_volume,
                                                                                           vol_per_tube)
        for source in mm_tubes:
            self._mm_sources.append_tube_with_vol(source, available_volume)

        self.logger.info("")
        self.logger.info("We need {} tubes with {}ul of mastermix each in {}.".format(num_tubes,
                                                                                      vol_per_tube,
                                                                                      self._mm_sources))
        self.logger.debug("{}ul will be dispensed to control positions.".format(volume_for_controls))
        self.logger.debug("{}ul will be dispensed to PCR plate".format(volume_to_distribute_to_pcr_plate))
        self.logger.debug("{}ul will be dispensed to strips".format(volume_to_distribute_to_strip))
        self.logger.debug("")
        self.logger.debug("In this run we use a volume overhead of: {}ul".format(self._mastermix_vol_headroom))
        self.logger.debug("\t- {:.1f}ul will remain in tubes".format(self.headroom_vol_from_tubes_to_strip))
        self.logger.debug("\t- {:.1f}ul will remain in strips".format(self.headroom_vol_from_strip_to_pcr))

        # Variable to transfer headroom to strip only the first time
        strip_headroom_vol_single_first_time = self.headroom_vol_from_strip_to_pcr_single

        # First fill controls
        self.fill_controls(dead_volume=self._p300.min_volume)

        # Main loop filling the plate
        while self.remaining_cols > 0:
            # calcuations for filling strip each time
            self.logger.debug("Remaining columns: {}".format(self.remaining_cols))
            strip_volume = min(self._mm_strip_capacity,
                               self.remaining_cols * self._mastermix_vol + strip_headroom_vol_single_first_time)

            samples_per_this_strip = (strip_volume - strip_headroom_vol_single_first_time) // self._mastermix_vol


            strip_fill_volume = samples_per_this_strip * self._mastermix_vol + strip_headroom_vol_single_first_time
            strip_headroom_vol_single_first_time = 0 # resetting the headroom volume, will still be present in strips

            self.logger.debug("Filling strip with {}ul and using it for {} samples".format(strip_fill_volume,
                                                                                          samples_per_this_strip))
            self.fill_strip(strip_fill_volume)

            self.transfer_to_pcr_plate_and_mark_done(samples_per_this_strip)

        if self._p300.has_tip:
            self.drop(self._p300)

        self.logger.debug("Remaining vols: {}".format(self._mm_sources))

    def drop(self, pip):
        if self._debug_mode:
            pip.return_tip()
        else:
            super(StationCBioerMastermixPrep, self).drop(pip)

arguments = dict(num_samples=88, debug_mode=False)

# protocol for loading in Opentrons App or opentrons_simulate
# =====================================
logging.getLogger(StationCBioerMastermixPrep.__name__).setLevel(logging.INFO)
metadata = {'apiLevel': '2.7'}
station = StationCBioerMastermixPrep(**arguments)


def run(ctx):
    return station.run(ctx)


# for running directly with python command 'py Mastermix_prep_stations.py"
# ========================================================================
if __name__ == "__main__":
    StationCBioerMastermixPrep(**arguments, metadata={'apiLevel': '2.7'}).simulate()
