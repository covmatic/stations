from ..station import Station, labware_loader, instrument_loader
from ..multi_tube_source import MultiTubeSource
from ..utils import uniform_divide, MoveWithSpeed, get_labware_json_from_filename
import math
import logging

class BioerProtocol(Station):

    def __init__(self,
            debug_mode = False,
            num_samples: int = 96,
            pk_tube_bottom_height = 2,
            mm_tube_bottom_height = 2,
            pcr_bottom_headroom_height = 4.5,
            dw_bottom_height = 17.5,
            mix_bottom_height = 0.5,
            mix_bottom_height_dw = 2.2,
            mm_plate_bottom_height = 1.2,
            dw_elutes_bottom_height = 0,
            pk_volume_tube = 320,
            vol_pk_offset = 5,
            vol_mm_offset = 10,
            elution_volume = 12,
            mm_volume = 17,
            mm_volume_tube = 1800,
            mm_tube_vertical_speed = 25,
            headroom_vol_from_tubes_to_pcr = 60,
            headroom_vol_from_tubes_to_dw = 10,
            headroom_factor_mm: float = 1,
            control_well_positions = ['G12', 'H12'],
            pause_between_mastermix_and_elutes: bool = True,
            tube_block_model: str = 'opentrons_24_aluminumblock_nest_2ml_screwcap',
            transfer_elutes_phase: bool = False,
            transfer_proteinase_phase: bool = False,
            mix_beads_phase: bool = False,
            mastermix_phase: bool = False,
            vertical_offset = -16,
            slow_vertical_speed: float = 25,
            very_slow_vertical_speed: float = 5,
            elution_air_gap = 10,
            final_mix_blow_out_height = -2,
            p300_tip_max_volume: float = 200,        # ul max volume managed by tips
            mastermix_type: str = "ELITECH",
            ** kwargs):

        super(BioerProtocol, self).__init__(
            num_samples = num_samples,
            ** kwargs)

        self._debug_mode = debug_mode
        self._dests_sample = []
        self._max_sample_per_dw = 16
        self._elution_volume = elution_volume
        self._pk_volume = 10
        self._pk_volume_tube = pk_volume_tube
        self._mm_volume = mm_volume
        self._mm_volume_tube = mm_volume_tube
        self._mm_tube_bottom_height = mm_tube_bottom_height
        self._mm_tube_vertical_speed = mm_tube_vertical_speed
        self._dw_bottom_height = dw_bottom_height
        self._mix_bottom_height_dw = mix_bottom_height_dw
        self._pcr_bottom_headroom_height = pcr_bottom_headroom_height
        self._mix_bottom_height = mix_bottom_height
        self._mm_plate_bottom_height = mm_plate_bottom_height
        self._dw_elutes_bottom_height = dw_elutes_bottom_height
        self._mastermix_type: str = mastermix_type
        self._pk_tube_source = MultiTubeSource()
        self._mm_tube_source = MultiTubeSource(vertical_speed=15, name=self._mastermix_type)
        self._control_well_positions = control_well_positions
        self._pk_tube_bottom_height = pk_tube_bottom_height
        self._headroom_vol_from_tubes_to_pcr = headroom_vol_from_tubes_to_pcr
        self._headroom_factor_mm = headroom_factor_mm
        self._headroom_vol_from_tubes_to_dw = headroom_vol_from_tubes_to_dw
        self._pause_between_mastermix_and_elutes = pause_between_mastermix_and_elutes
        self._tube_block_model = tube_block_model
        self._mix_beads_phase = mix_beads_phase
        self._mastermix_phase = mastermix_phase
        self.transfer_elutes_phase = transfer_elutes_phase
        self.transfer_proteinase_phase = transfer_proteinase_phase
        self._vertical_offset = vertical_offset
        self._vol_pk_offset = vol_pk_offset
        self._vol_mm_offset = vol_mm_offset
        self._slow_vertical_speed = slow_vertical_speed
        self._very_slow_vertical_speed = very_slow_vertical_speed
        self._elution_air_gap = elution_air_gap
        self._final_mix_blow_out_height = final_mix_blow_out_height
        self._s300_fake_aspirate: bool = True
        self._p300_fake_aspirate: bool = True
        self._p300_tip_max_volume = p300_tip_max_volume

        if self._num_samples > 80:
            self._dws = ['8', '9', '5', '6', '2', '3']
        elif self._num_samples > 64:
            self._dws = ['8', '9', '5', '6', '2']
        elif self._num_samples > 48:
            self._dws = ['8', '9', '5', '6']
        elif self._num_samples > 32:
            self._dws = ['8', '9', '5']
        elif self._num_samples > 16:
            self._dws = ['8', '9']
        else:
            self._dws = ['8']

    @labware_loader(1, "_tips200")
    def load_tips200(self):
        self._tips200 = [self._ctx.load_labware('opentrons_96_filtertiprack_200ul', slot, '200µl filter tiprack multi')
                                for slot in ['7', '10']]

    @labware_loader(2, "_tips200_single")
    def load_tips200_single(self):
        self._tips200_single = [self._ctx.load_labware('opentrons_96_tiprack_300ul', '11', '200µl filter tiprack single')]

    @labware_loader(3, "_plate_elute")
    def load_dest_plate_elute(self):
        self._dest_plate_elute = self._ctx.load_labware('opentrons_96_aluminumblock_nest_wellplate_100ul', '1', 'chilled elution plate')

    @labware_loader(4, "_tube_block")
    def load_tube_block(self):
        self._tube_block = self._ctx.load_labware(self._tube_block_model, '4', 'aluminum block')

    @labware_loader(5, "_dests_plates")
    def load_dests_plate(self):
        self._dests_plates = [self._ctx.load_labware_from_definition(
                                    get_labware_json_from_filename("bioer_96_wellplate_2000ul.json"),
                                    slot, 'Bioer 96-deepwell sample plate 1' + str(e + 1))
                                for e, slot in enumerate(self._dws)]

    @instrument_loader(0, "_p300")
    def load_p300(self):
        self._p300 = self._ctx.load_instrument('p300_multi_gen2', 'left', tip_racks=self._tips200)

    @instrument_loader(0, "_s300")
    def load_s300(self):
        self._s300 = self._ctx.load_instrument('p300_single_gen2', 'right', tip_racks=self._tips200_single)

    def _tipracks(self) -> dict:
        return {"_tips200":"_p300", "_tips200_single":"_s300"}


    @property
    def sample_dests_wells(self):
        return self._dest_plate_elute.wells()[:self._num_samples]


    def is_well_in_samples(self, well):
        """
        Function that check if a well is within the samples well.
        :param well: well to check
        :return: True if the well is included in the samples list.
        """
        return well in self.sample_dests_wells


    @property
    def control_dests_wells(self):
        return [self._dest_plate_elute.wells_by_name()[i] for i in self._control_well_positions]


    @property
    def control_wells_not_in_samples(self):
        """
        :return: a list of wells for controls that are not already filled with the 8-channel pipette
        """
        return [c for c in self.control_dests_wells if not self.is_well_in_samples(c)]


    @property
    def destinations(self):
        for plate in self._dests_plates:
            self._dests_sample += plate.wells()[:8]
            self._dests_sample += plate.wells()[48:56]
        return self._dests_plates


    @property
    def proteinase_destinations(self):
        return [row for plate in self._dests_plates for row in plate.columns()[::6]]


    @property
    def proteinase_destinations_unique(self):
        dests_pk_unique = []
        for d in self.proteinase_destinations:
            dests_pk_unique += d
        return dests_pk_unique

    @property
    def mastermix_tube_list(self):
        return list(reversed(self._tube_block.wells()))

    @property
    def beads_destinations(self):
        return [row for plate in self._dests_plates for row in plate.rows()[0]][5::6]

    def transfer_proteinase(self, stage="transfer proteinase"):
        done_samples = 0
        num_cycle = 1
        num_samples_per_fill = 16

        if self.run_stage(stage):
            self.logger.info("Trasferring proteinase from tube to deepwells")

            self.pick_up(self._s300)
            while done_samples < self._num_samples:
                samples_to_do = self.proteinase_destinations_unique[done_samples:(done_samples + num_samples_per_fill)]
                # self.logger.info("Cycle {} - samples to do: {}".format(num_cycle, samples_to_do))
                # self.logger.info(
                #     "PK:Cycle {} - before filling: samples done: {}, samples to do: {}".format(num_cycle, done_samples,
                #                                                                                len(samples_to_do)))
                if num_cycle > 1:
                    self._vol_pk_offset = 0
                vol_pk = len(samples_to_do) * self._pk_volume
                if num_cycle == 1:
                    self._s300.aspirate(self._vol_pk_offset, self._tube_block.wells()[0].bottom(self._pk_tube_bottom_height))
                self._pk_tube_source.prepare_aspiration(vol_pk, self._pk_tube_bottom_height)
                self._pk_tube_source.aspirate(self._s300)
                #self.logger.info("Aspirating {} at: {} mm".format(vol_pk, self._pk_tube_bottom_height))
                for s, ss in enumerate(samples_to_do):
                    self._s300.dispense(self._pk_volume, ss.bottom(self._dw_bottom_height))
                    self._s300.touch_tip(ss, 0.6, self._vertical_offset)
                done_samples += num_samples_per_fill
                # self.logger.info("PK:Cycle {} - after distribution: samples done: {}".format(num_cycle, done_samples))
                num_cycle += 1
            if self._s300.has_tip:
                self.drop(self._s300)


    def mix_beads(self):
        done_mix = 0
        destbeads = self.beads_destinations[done_mix:(done_mix + len(self.beads_destinations))]

        self.logger.info("Mix beads in deepwells")

        self.pick_up(self._p300)
        for b, d in enumerate(destbeads):
            self._p300.mix(3, 15, d.bottom(self._mix_bottom_height_dw))
            done_mix = done_mix + len(self.beads_destinations)
        if self._p300.has_tip:
            self.drop(self._p300)

    def transfer_mastermix(self, stage="transfer mastermix"):
        samples_with_controls = self.sample_dests_wells + self.control_wells_not_in_samples

        self.logger.info("Trasferring mastermix from tube to pcr plate")

        for i, sample in enumerate(samples_with_controls):
            remaining_samples = len(samples_with_controls) - i

            if self.run_stage("{} {}/{}".format(stage,  i + 1, len(samples_with_controls))):
                if not self._s300.has_tip:
                    self.pick_up(self._s300)

                self.fake_aspirate_mmix()
                self.check_and_aspirate_mmix(remaining_samples)

                with MoveWithSpeed(self._s300,
                                   from_point=sample.bottom(self._mm_plate_bottom_height + 5),
                                   to_point=sample.bottom(self._mm_plate_bottom_height),
                                   speed=self._slow_vertical_speed, move_close=False):
                    self._s300.dispense(self._mm_volume)
            else:
                # Stage not executed
                self._mm_tube_source.use_volume_only(self._mm_volume)
        if self._s300.has_tip:
            self.drop(self._s300)

    def check_and_aspirate_mmix(self, num_samples):
        '''This function will check if the tip has mastermix to dispense to one sample.
            If the tip is empty it will aspirate the needed quantity to serve the num_samples passed
            @param num_samples: num samples that needed to be served
            @return: If the aspiration is needed '''
        if self._s300.current_volume < self._mm_volume:
            max_num_samples = (self._p300_tip_max_volume - self._vol_mm_offset) // self._mm_volume
            num_samples = min(max_num_samples, num_samples)

            vol_mm = self._vol_mm_offset if self._s300.current_volume < self._vol_mm_offset else 0
            vol_mm += (num_samples * self._mm_volume)
            self.logger.info("Calculating mastermix: {}ul; num samples: {}".format(vol_mm, num_samples))

            self._mm_tube_source.prepare_aspiration(vol_mm, min_height=self._mm_tube_bottom_height)
            self._mm_tube_source.aspirate(self._s300)

    def fake_aspirate_mmix(self):
        if self._s300_fake_aspirate:
            self._s300_fake_aspirate = False
            self._s300.aspirate(10, self._mm_tube_source.get_current_well().top())
            self._s300.dispense(10)

    def transfer_elutes(self, stage="transfer elutes"):
        set_of_source = math.ceil(self._num_samples / self._max_sample_per_dw)
        source_plate = [row for plate in self._dests_plates for row in plate.columns()[4::6]]
        dests_sample_elute = self._dest_plate_elute.columns()[:self.num_cols]

        if self._pause_between_mastermix_and_elutes:
            self.dual_pause(self.get_msg_format("insert deepwell", ", ".join([str(d) for d in self._dests_plates])), home=(False, False))

        self.logger.info("Trasferring elutes from deepwells to pcr plate")

        done_col = 0
        source_el = source_plate[done_col:(done_col + len(source_plate))]

        for i, (s, d) in enumerate(zip(source_el, dests_sample_elute)):
            controls = any([w in d for w in self.control_dests_wells])

            if controls:
                self.logger.info("Found controls in this row")

            samples_and_pipette = []
            if controls:
                self.logger.info("We will use single pipetting")
                for w, z in zip(s, d):
                    if z not in self.control_dests_wells:
                        if z in self.sample_dests_wells:
                            samples_and_pipette.append((w, z, self._s300))
                        else:
                            self.logger.info("Skipping well {} since it is not in samples list".format(z))
            else:
                samples_and_pipette.append((s[0], d[0], self._p300))

            for j, (t, o, pipette) in enumerate(samples_and_pipette):
                if self.run_stage("{} {}{}".format(stage, i+1, " {}/{}".format(j+1, len(samples_and_pipette)) if len(samples_and_pipette)>1 else "")):
                    self.transfer_elute(t, o, pipette)
            done_col = done_col + len(source_plate)

    def transfer_elute(self, source, dest, pipette):
        self.pick_up(pipette)
        if self._p300_fake_aspirate or self._s300_fake_aspirate:
            pipette.aspirate(1, source.top())
            pipette.dispense(1)
            if pipette == self._p300:
                self._p300_fake_aspirate = False
            elif pipette == self._s300:
                self._s300_fake_aspirate = False

        with MoveWithSpeed(pipette,
                           from_point=source.bottom(self._dw_elutes_bottom_height + 3),
                           to_point=source.bottom(self._dw_elutes_bottom_height),
                           speed=self._very_slow_vertical_speed, move_close=False):
            pipette.aspirate(self._elution_volume)
        pipette.air_gap(self._elution_air_gap)
        pipette.dispense(self._elution_air_gap, dest.top())
        pipette.dispense(self._elution_volume, dest.bottom(self._pcr_bottom_headroom_height))
        pipette.mix(5, 20, dest.bottom(self._mix_bottom_height))
        pipette.blow_out(dest.top(self._final_mix_blow_out_height))
        pipette.air_gap(self._elution_air_gap)
        self.drop(pipette)

    @property
    def mastermix_needed_volume(self):
        """ Calculates the needed mastermix volume to ditribute to plate"""
        volume_for_controls = len(self.control_wells_not_in_samples) * self._mm_volume
        self.logger.info(
            "Calculated {} ul for controls: {}".format(volume_for_controls, self.control_wells_not_in_samples))
        volume_for_samples = self._mm_volume * self._num_samples
        self.logger.info("Calcuated {} ul for samples".format(volume_for_samples))
        return volume_for_samples + volume_for_controls

    @property
    def mastermix_total_volume(self):
        """ Calculates the total volume of the mastermix: needed plus overheads """
        return self.mastermix_needed_volume * self._headroom_factor_mm + self._headroom_vol_from_tubes_to_pcr

    def calculate_and_load_mastermix_tubes(self):
        num_tubes, vol_per_tube = uniform_divide(
            self.mastermix_total_volume, self._mm_volume_tube)
        available_volume = self.mastermix_needed_volume / num_tubes
        available_volume += self._vol_mm_offset  # Adding volume for initial aspiration
        assert vol_per_tube > available_volume, \
            "Error in volume calculations: requested {}ul while total in tubes {}ul".format(available_volume,
                                                                                            vol_per_tube)
        [self._mm_tube_source.append_tube_with_vol(t, available_volume) for t in self.mastermix_tube_list[:num_tubes]]

    def body(self):

        num_dw = math.ceil(self._num_samples / self._max_sample_per_dw)

        self.logger.info("Controls in {}".format(self._control_well_positions))

        #proteinase_destinations
        dests_pk_unique = []
        for d in self.proteinase_destinations:
            dests_pk_unique += d
        #self.logger.info("dests_pk_unique: {}".format(dests_pk_unique))

        #tube_block_pk
        volume_for_samples = self._pk_volume * self._num_samples
        volume_to_distribute_to_dw = volume_for_samples
        num_pk_tube = math.ceil(volume_for_samples / self._pk_volume_tube)

        [self._pk_tube_source.append_tube_with_vol(t, self._pk_volume_tube) for t in self._tube_block.wells()[0:num_pk_tube]]
        self.logger.info("We need {} tubes with {}ul of proteinase each in {}".format(num_pk_tube,
                                                                                      self._pk_volume_tube,
                                                                                      self._pk_tube_source.locations_str))

        pk_requirements = self.get_msg_format("load pk tubes",
                                           num_pk_tube,
                                           self._pk_volume_tube,
                                           self._pk_tube_source.locations_str)


        #tube_block_mm

        self.calculate_and_load_mastermix_tubes()

        mmix_requirements = self.get_msg_format("load mm tubes",
                                                self._mm_tube_source.num_tubes,
                                                self._mm_tube_source)
        self.logger.info(mmix_requirements)
        control_positions = self.get_msg_format("control positions",
                                                self._control_well_positions)

        #transfer_proteinase
        if self.transfer_proteinase_phase:
            self.pause(pk_requirements, home=False)
            self.transfer_proteinase()

        #mix_beads
        if self._mix_beads_phase:
            self.stage = "Mix beads"
            self.mix_beads()

        #Bioer phase
        if (self.transfer_proteinase_phase or self._mix_beads_phase) and (self._mastermix_phase or self.transfer_elutes_phase):
            self.dual_pause("Move deepwells to Bioer")

        #transfer mastermix
        if self._mastermix_phase:
            if self._control_well_positions:
                self.pause(control_positions, home=False)
            self.pause(mmix_requirements, home=False)
            self.transfer_mastermix()

        #transfer elutes
        if self.transfer_elutes_phase:
            self.transfer_elutes()

    def drop(self, pip):
        if self._debug_mode:
            pip.return_tip()
        else:
            super(BioerProtocol, self).drop(pip)

# class BioerPreparationToBioer(BioerProtocol):
#     def __init__(self, ** kwargs):
#         super(BioerPreparationToBioer, self).__init__(
#             mix_beads_phase = False,
#             transfer_proteinase_phase = True,
#             ** kwargs)

class BioerPreparationToPcr(BioerProtocol):
    def __init__(self,
                 transfer_elutes_phase: bool = True,
                 ** kwargs):
        super(BioerPreparationToPcr, self).__init__(
            mastermix_phase = True,
            transfer_elutes_phase = transfer_elutes_phase,
            ** kwargs)


class BioerPreparationToPcrTechogenetics(BioerPreparationToPcr):
    _protocol_description = "Technogenetics mastermix and elutes distribution"
    
    def __init__(self,
                 mm_volume=20,
                 elution_volume=20,
                 mm_volume_tube=1400,
                 transfer_elutes_phase: bool = True,
                 **kwargs):
        super(BioerPreparationToPcrTechogenetics, self).__init__(
            mm_volume = mm_volume,
            elution_volume = elution_volume,
            mm_volume_tube = mm_volume_tube,
            transfer_elutes_phase = transfer_elutes_phase,
            mastermix_type = "KHB",
            **kwargs)


class DistributeMastermixTechnogenetics(BioerPreparationToPcrTechogenetics):
    _protocol_description = "Technogenetics mastermix distribution"

    def __init__(self, **kwargs):
        super(DistributeMastermixTechnogenetics, self).__init__(
            transfer_elutes_phase=False,
            headroom_factor_mm = 1.2,               # set 20% overhead for mmix transfer
            headroom_vol_from_tubes_to_pcr = 0,     # set 0ul additive overhead for mmix transfer
            control_well_positions = [],
            **kwargs)


# protocol for loading in Opentrons App or opentrons_simulate
# =====================================
logging.getLogger(BioerProtocol.__name__).setLevel(logging.INFO)
metadata = {'apiLevel': '2.7'}
station = BioerProtocol(num_samples = 32)

def run(ctx):
    return station.run(ctx)

if __name__ == "__main__":
    DistributeMastermixTechnogenetics(metadata={'apiLevel':'2.7'}, num_samples=8).simulate()

