from ..station import Station, labware_loader, instrument_loader
from ..multi_tube_source import MultiTubeSource
from ..utils import uniform_divide, get_labware_json_from_filename, MoveWithSpeed


class BioerPreparation(Station):
    def __init__(self,
                 num_samples: int = 16,
                 pk_tube_bottom_height: float = 2,
                 deepwell_slot: int = 3,
                 pk_dw_bottom_height: float = 13.5,
                 pk_volume: float = 10,
                 pk_dead_volume: float = 5,
                 pk_vertical_speed: float = 20,
                 sample_vertical_speed: float = 20,
                 tube_block_model: str = 'opentrons_24_tuberack_nest_1.5ml_screwcap',
                 p300_max_volume: float = 200,
                 ** kwargs):

        assert num_samples <= 16, "Protocol must be used with 16 or less samples"

        super(BioerPreparation, self).__init__(
            num_samples=num_samples,
            ** kwargs)
        self._pk_volume = pk_volume
        self._pk_vertical_speed = pk_vertical_speed
        self._sample_vertical_speed = sample_vertical_speed
        self._pk_tube_bottom_height = pk_tube_bottom_height
        self._pk_dw_bottom_height = pk_dw_bottom_height
        self._pk_dead_volume = pk_dead_volume
        self._deepwell_slot = deepwell_slot
        self._tube_block_model = tube_block_model
        self._p300_max_volume = p300_max_volume

    @labware_loader(1, "_tips200")
    def load_tips200(self):
        self._tips200 = [self._ctx.load_labware('opentrons_96_filtertiprack_200ul', slot, '200ul filter tiprack')
                                for slot in ['11']]

    @labware_loader(1, "_tips200")
    def load_tips1000(self):
        self._tips1000 = [self._ctx.load_labware('opentrons_96_filtertiprack_1000ul', slot, '1000ul filter tiprack')
                                for slot in ['10']]
    @labware_loader(4, "_tube_rack")
    def load_tube_rack(self):
        self._tube_rack = self._ctx.load_labware(self._tube_block_model, '6', 'tube rack for proteinase')

    @labware_loader(5, "_dests_plate")
    def load_dests_plate(self):
        self._dests_plates = [self._ctx.load_labware_from_definition(get_labware_json_from_filename("bioer_96_wellplate_2000ul.json"),
                                         slot,
                                         '96-deepwell sample plate {}'.format(i+1)) for i, slot in enumerate([self._deepwell_slot])]

    @instrument_loader(0, "_p300")
    def load_p300(self):
        self._p300 = self._ctx.load_instrument('p300_single_gen2', 'left', tip_racks=self._tips200)

    @instrument_loader(0, "_p1000")
    def load_p1000(self):
        self._p1000 = self._ctx.load_instrument('p1000_single_gen2', 'right', tip_racks=self._tips1000)

    def _tipracks(self) -> dict:
        return {"_tips200": "_p300",
                "_tips1000": "_p1000"}

    @property
    def samples_destination_rows(self):
        return [row for plate in self._dests_plates for row in plate.columns()[::6]]

    @property
    def samples_destination_single(self):
        return [sample for row in self.samples_destination_rows for sample in row]

    @property
    def proteinase_destinations(self):
        return self.samples_destination_single

    @property
    def p300_available_vol(self):
        return self._p300_max_volume - self._pk_dead_volume

    def transfer_proteinase(self):
        num_samples_per_aspirate = self.p300_available_vol // self._pk_volume
        aspirate_volume = num_samples_per_aspirate*self._pk_volume + self._pk_dead_volume
        self.log("One PK aspirate of {}ul can dispense to {} destination".format(aspirate_volume, num_samples_per_aspirate))

        aspirate_dead_volume = True
        self.pick_up(self._p300)

        # Fake aspiration and dispense to avoid a bug that move the pipette to the top of the well.
        self._p300.aspirate(10, self._tube_rack.wells()[0].top())
        self._p300.dispense(self._p300.current_volume)

        for done_count, sample in enumerate(self.samples_destination_single):
            if self._p300.current_volume - self._pk_dead_volume < self._pk_volume:
                remaining_samples = self._num_samples - done_count
                self.log("remaining {} samples".format(remaining_samples))
                volume_for_samples = min([self._p300_max_volume,
                                          self._p300.current_volume + remaining_samples * self._pk_volume])
                volume_to_aspirate = volume_for_samples + self._pk_dead_volume if aspirate_dead_volume else 0
                aspirate_dead_volume = False
                self.log("aspirate {}ul".format(volume_to_aspirate))
                with MoveWithSpeed(self._p300,
                                   from_point=self._tube_rack.wells()[0].top(),
                                   to_point=self._tube_rack.wells()[0].bottom(self._pk_tube_bottom_height),
                                   speed=self._pk_vertical_speed):
                    self._p300.aspirate(volume_to_aspirate)

            with MoveWithSpeed(self._p300,
                               from_point=sample.bottom(self._pk_dw_bottom_height + 5),
                               to_point=sample.bottom(self._pk_dw_bottom_height),
                               speed=self._pk_vertical_speed, move_close=False):
                self._p300.dispense(self._pk_volume)

        self.drop(self._p300)

    def log(self, s):
        self._ctx.comment(s)

    def body(self):
        #
        # num_dw = math.ceil(self._num_samples / self._max_sample_per_dw)
        #
        # self.logger.info("Controls in {}".format(self._control_well_positions))

        # #proteinase_destinations
        # dests_pk_unique = []
        # for d in self.proteinase_destinations:
        #     dests_pk_unique += d
        # #self.logger.info("dests_pk_unique: {}".format(dests_pk_unique))

        # #tube_block_pk
        # volume_for_samples = self._pk_volume * self._num_samples
        # volume_to_distribute_to_dw = volume_for_samples
        # num_pk_tube = math.ceil(volume_for_samples / self._pk_volume_tube)
        #
        # [self._pk_tube_source.append_tube_with_vol(t, self._pk_volume_tube) for t in self._tube_block.wells()[0:num_pk_tube]]
        # self.logger.info("We need {} tubes with {}ul of proteinase each in {}".format(num_pk_tube,
        #                                                                               self._pk_volume_tube,
        #                                                                               self._pk_tube_source.locations_str))
        #
        # pk_requirements = self.get_msg_format("load pk tubes",
        #                                    num_pk_tube,
        #                                    self._pk_volume_tube,
        #                                    self._pk_tube_source.locations_str)
        #
        #
        # #tube_block_mm
        # volume_for_controls = len(self.control_wells_not_in_samples) * self._mm_volume
        # volume_for_samples = self._mm_volume * self._num_samples
        # volume_to_distribute_to_pcr_plate = volume_for_samples + volume_for_controls
        # num_tubes, vol_per_tube = uniform_divide(
        #     volume_to_distribute_to_pcr_plate + self._headroom_vol_from_tubes_to_pcr, self._mm_volume_tube)
        # mm_tubes = self._tube_block.wells()[:num_tubes]
        # available_volume = volume_to_distribute_to_pcr_plate / len(mm_tubes)
        # if self._headroom_vol_from_tubes_to_pcr > 0:
        #     if self._vol_mm_offset < (self._headroom_vol_from_tubes_to_pcr / len(mm_tubes)):
        #         available_volume += self._vol_mm_offset
        # assert vol_per_tube > available_volume, \
        #     "Error in volume calculations: requested {}ul while total in tubes {}ul".format(available_volume, vol_per_tube)
        #
        # [self._mm_tube_source.append_tube_with_vol(t, available_volume) for t in self._tube_block.wells()[len(self._tube_block.wells())-num_tubes::]]
        #
        # self.logger.info("We need {} tubes with {}ul of mastermix each in {}".format(num_tubes,
        #                                                                               vol_per_tube,
        #                                                                               self._mm_tube_source.locations_str))
        # mmix_requirements = self.get_msg_format("load mm tubes",
        #                                    num_tubes,
        #                                    vol_per_tube,
        #                                    self._mm_tube_source.locations_str)
        #
        # control_positions = self.get_msg_format("control positions",
        #                                         self._control_well_positions)
        #
        # #transfer_proteinase
        # if self.transfer_proteinase_phase:
        #     self.pause(pk_requirements, home=False)
        self.stage = "Transfer proteinase"
        self.transfer_proteinase()
        #
        # #mix_beads
        # if self._mix_beads_phase:
        #     self.stage = "Mix beads"
        #     self.mix_beads()
        #
        # #Bioer phase
        # if (self.transfer_proteinase_phase or self._mix_beads_phase) and (self._mastermix_phase or self.transfer_elutes_phase):
        #     self.dual_pause("Move deepwells to Bioer")
        #
        # #transfer mastermix
        # if self._mastermix_phase:
        #     self.pause(control_positions, home=False)
        #     self.pause(mmix_requirements, home=False)
        #     self.stage = "Transfer mastermix"
        #     self.transfer_mastermix()
        #
        # #transfer elutes
        # if self.transfer_elutes_phase:
        #     self.stage = "Transfer elutes"
        #     self.transfer_elutes()

# protocol for loading in Opentrons App or opentrons_simulate
# =====================================
#logging.getLogger(BioerPreparation.__name__).setLevel(logging.INFO)

metadata = {'apiLevel': '2.7'}
station = BioerPreparation(num_samples = 16)

def run(ctx):
    return station.run(ctx)

if __name__ == "__main__":
    BioerPreparation(metadata={'apiLevel':'2.7'}).simulate()
