from ..station import Station, labware_loader, instrument_loader
from ..multi_tube_source import MultiTubeSource
from ..utils import uniform_divide, get_labware_json_from_filename, MoveWithSpeed, WellWithVolume
from ..a.copan_48 import copan_48_corrected_specs


class BioerPreparation(Station):
    def __init__(self,
                 num_samples: int = 16,
                 deepwell_slot: int = 3,
                 deepwel_initial_volume: float = 600,
                 pk_tube_bottom_height: float = 2,
                 pk_dw_bottom_height: float = 13.5,
                 pk_rate_aspirate: float = 100,
                 pk_rate_dispense: float = 100,
                 pk_volume: float = 10,
                 pk_dead_volume: float = 5,
                 pk_vertical_speed: float = 50,
                 sample_vertical_speed: float = 50,
                 sample_air_gap: float = 25,
                 sample_rate_aspirate: float = 200,
                 sample_rate_dispense: float = 200,
                 sample_volume: float = 300,
                 sample_destination_bottom_height: float = 13.5,
                 source_racks_slots=[1],
                 source_bottom_height_aspirate: float = 6,
                 source_bottom_height_start: float = 40,
                 tube_block_model: str = 'opentrons_24_tuberack_nest_1.5ml_screwcap',
                 tube_rack_slot: int = 6,
                 p300_max_volume: float = 200,
                 ** kwargs):

        assert num_samples <= 16, "Protocol must be used with 16 or less samples"

        super(BioerPreparation, self).__init__(
            num_samples=num_samples,
            ** kwargs)
        self._pk_volume = pk_volume
        self._pk_rate_aspirate = pk_rate_aspirate
        self._pk_rate_dispense = pk_rate_dispense
        self._pk_vertical_speed = pk_vertical_speed
        self._sample_vertical_speed = sample_vertical_speed
        self._pk_tube_bottom_height = pk_tube_bottom_height
        self._pk_dw_bottom_height = pk_dw_bottom_height
        self._pk_dead_volume = pk_dead_volume
        self._deepwell_slot = deepwell_slot
        self._deepwel_initial_volume = deepwel_initial_volume
        self._sample_air_gap = sample_air_gap
        self._sample_rate_aspirate = sample_rate_aspirate
        self._sample_rate_dispense = sample_rate_dispense
        self._sample_volume = sample_volume
        self._sample_destination_bottom_height = sample_destination_bottom_height
        self._source_racks_slots = source_racks_slots
        self._source_bottom_height_start = source_bottom_height_start
        self._source_bottom_height_aspirate = source_bottom_height_aspirate
        self._tube_block_model = tube_block_model
        self._tube_rack_slot = tube_rack_slot
        self._p300_max_volume = p300_max_volume
        self._p1000_fake_aspirate = True

    @labware_loader(0, "_tips200")
    def load_tips200(self):
        self._tips200 = [self._ctx.load_labware('opentrons_96_filtertiprack_200ul', slot, '200ul filter tiprack')
                                for slot in ['10']]

    @labware_loader(1, "_tips1000")
    def load_tips1000(self):
        self._tips1000 = [self._ctx.load_labware('opentrons_96_filtertiprack_1000ul', slot, '1000ul filter tiprack')
                                for slot in ['11']]

    @labware_loader(2, "_source_racks")
    def load_source_racks(self):
        labware_def = copan_48_corrected_specs.labware_definition()
        self._source_racks = [
            self._ctx.load_labware_from_definition(
                labware_def, slot,
                'source tuberack ' + str(i + 1)
            ) for i, slot in enumerate(self._source_racks_slots)
        ]

    @labware_loader(4, "_tube_rack")
    def load_tube_rack(self):
        self._tube_rack = self._ctx.load_labware(self._tube_block_model, self._tube_rack_slot, 'tube rack for proteinase')

    @labware_loader(5, "_dests_plates")
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
        return [sample for row in self.samples_destination_rows for sample in row][:self._num_samples]

    @property
    def samples_source_single(self):
        return [sample for rack in self._source_racks for sample in rack.wells()]

    @property
    def proteinase_destinations(self):
        return self.samples_destination_single

    @property
    def p300_available_vol(self):
        return self._p300_max_volume - self._pk_dead_volume

    def transfer_proteinase(self, stage: str = "transfer proteinase"):
        self._p300.flow_rate.aspirate = self._pk_rate_aspirate
        self._p300.flow_rate.dispense = self._pk_rate_dispense

        num_samples_per_aspirate = self.p300_available_vol // self._pk_volume
        aspirate_volume = num_samples_per_aspirate*self._pk_volume + self._pk_dead_volume
        self.logger.info("One PK aspirate of {}ul can dispense to {} destination".format(aspirate_volume, num_samples_per_aspirate))

        aspirate_dead_volume = True
        p300_fake_aspirate = True

        for done_count, sample in enumerate(self.samples_destination_single):
            if self.run_stage("{} {}/{}".format(stage, done_count+1, len(self.samples_destination_single))):
                if not self._p300.has_tip:
                    self.pick_up(self._p300)
                if self._p300.current_volume - self._pk_dead_volume < self._pk_volume:
                    # Fake aspiration and dispense to avoid a bug that moves the pipette to the top of the well.
                    if p300_fake_aspirate:
                        p300_fake_aspirate = False
                        self._p300.aspirate(10, self._tube_rack.wells()[0].top())
                        self._p300.dispense(self._p300.current_volume)

                    remaining_samples = self._num_samples - done_count
                    volume_for_samples = min([self._p300_max_volume,
                                              self._p300.current_volume + remaining_samples * self._pk_volume])
                    volume_to_aspirate = volume_for_samples + self._pk_dead_volume if aspirate_dead_volume else 0
                    aspirate_dead_volume = False

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

        if self._p300.has_tip:          # at least one stage has been executed
            self.drop(self._p300)

    def transfer_sample(self, source, dest):
        self.logger.debug("transferring from {} to {}".format(source, dest))
        dest_with_volume = WellWithVolume(dest, self._deepwel_initial_volume, headroom_height=0)
        dest_initial_height = dest_with_volume.height

        self.pick_up(self._p1000)

        if self._p1000_fake_aspirate:
            self._p1000_fake_aspirate = False
            self._p1000.aspirate(self._sample_air_gap, source.top())
            self._p1000.dispense(self._sample_air_gap, source.top())

        # Aspirating from source tube
        with MoveWithSpeed(self._p1000,
                           from_point=source.bottom(self._source_bottom_height_start),
                           to_point=source.bottom(self._source_bottom_height_aspirate),
                           speed=self._sample_vertical_speed, move_close=False):
            self._p1000.aspirate(self._sample_volume)
        self._p1000.air_gap(self._sample_air_gap)

        # Dispensing at the right height
        dest_with_volume.fill(self._sample_volume)
        dest_filled_height = dest_with_volume.height + 10

        with MoveWithSpeed(self._p1000,
                           from_point=dest.bottom(dest_filled_height),
                           to_point=dest.bottom(dest_initial_height),
                           speed=self._sample_vertical_speed, move_close=False):
            self._p1000.dispense(self._sample_volume + self._sample_air_gap)

        self._p1000.air_gap(self._sample_air_gap)
        self.drop(self._p1000)

    def transfer_samples(self, stage: str = "transfer samples"):
        self._p1000.flow_rate.aspirate = self._sample_rate_aspirate
        self._p1000.flow_rate.dispense = self._sample_rate_dispense

        sources_and_dest_list = list(zip(self.samples_source_single, self.samples_destination_single))
        for done_count, (s, d) in enumerate(sources_and_dest_list):
            if self.run_stage("{} {}/{}".format(stage, done_count+1, len(sources_and_dest_list))):
                self.transfer_sample(s, d)

    def body(self):
        self.transfer_proteinase(stage="transfer proteinase")
        self.transfer_samples(stage="transfer samples")

# protocol for loading in Opentrons App or opentrons_simulate
# =====================================
#logging.getLogger(BioerPreparation.__name__).setLevel(logging.INFO)

metadata = {'apiLevel': '2.7'}
station = BioerPreparation(num_samples = 16)

def run(ctx):
    return station.run(ctx)

if __name__ == "__main__":
    BioerPreparation(metadata={'apiLevel':'2.7'}).simulate()
