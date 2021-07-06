import json
from covmatic_stations.station import instrument_loader, labware_loader
from covmatic_stations.utils import uniform_divide
from .technogenetics import StationBTechnogenetics
from ..paired_pipette import PairedPipette
from opentrons.types import Point
from itertools import repeat
import math
import os

class StationBTechnogeneticsPairedPipette(StationBTechnogenetics):

    def __init__(self, **kwargs):
        super(StationBTechnogeneticsPairedPipette, self).__init__(**kwargs)

    @labware_loader(8, "_res12")
    def load_res12(self):
        # re-loading labware to avoid bug on reagent reservoir (see https://github.com/Opentrons/opentrons/issues/7793)
        reservoir_file = os.path.join(os.path.split(__file__)[0], "nest_12_reservoir_15ml_modified.json")
        self.logger.info("Loading reservoir labware from: {}".format(reservoir_file))
        with open(reservoir_file) as labware_file:
            labware_def = json.load(labware_file)
        self._res12 = self._ctx.load_labware_from_definition(labware_def, 5, 'Trough with WashReagents')

    @property
    def wash1(self):
        return self._res12.rows()[0][:6]

    @property
    def wash2(self):
        return self._res12.rows()[0][-6:]

    @property
    def water(self):
        return self._elut12.rows()[0][11]

    @instrument_loader(0, "_m300r")
    def load_m300_right(self):
        self._m300r = self._ctx.load_instrument('p300_multi_gen2', 'right', tip_racks=self._tips300)
        self.logger.info("Loaded right pipette")
        if self._bind_aspiration_rate:
            self._m300r.flow_rate.aspirate = self._bind_aspiration_rate
        if self._bind_dispense_rate:
            self._m300r.flow_rate.dispense = self._bind_dispense_rate
        if self._bind_blowout_rate:
            self._m300r.flow_rate.blow_out = self._bind_blowout_rate

    def body(self):
        PairedPipette.setup(self._m300, self._m300r, self)
        super(StationBTechnogeneticsPairedPipette, self).body()

    def mix_samples(self):
        self._m300.flow_rate.aspirate = 94
        self._m300r.flow_rate.aspirate = 94

        with PairedPipette(self._magplate, self.mag_samples_m, start_at="mix sample") as tp:
            tp.pick_up()
            tp.mix(self._sample_mix_times, self._sample_mix_vol,
                   locationFrom="target",
                   well_modifier="bottom({})".format(self._sample_mix_height))
            tp.air_gap(self._bind_air_gap)
            tp.drop_tip()


    def remove_supernatant(self, vol: float, stage: str = "remove supernatant"):
        self._m300.flow_rate.aspirate = self._supernatant_removal_aspiration_rate
        self._m300r.flow_rate.aspirate = self._supernatant_removal_aspiration_rate

        num_trans = math.ceil((vol - self._vol_last_trans) / self._bind_max_transfer_vol)
        vol_per_trans = ((vol - self._vol_last_trans) / num_trans) if num_trans else 0

        waste_locs = list(repeat(self._waste, len(self.mag_samples_m)))

        with PairedPipette(self._magplate, self.mag_samples_m, waste_locs=waste_locs, start_at=stage) as tp:
            tp.pick_up()
            for i in range(num_trans):
                # tp.move_to()  # we want center() but for now it is not in available commands
                if i > 0:
                    tp.dispense(self._supernatant_removal_air_gap, locationFrom="target", well_modifier="top(0)")
                tp.aspirate(vol_per_trans, locationFrom="target", well_modifier="bottom({})".format(self._supernatant_removal_height))
                tp.air_gap(self._supernatant_removal_air_gap)
                tp.dispense(vol_per_trans+self._supernatant_removal_air_gap, locationFrom="waste_locs")
                tp.air_gap(self._supernatant_removal_air_gap)

            tp.comment("Supernatant removal: last transfer in {} step".format(self._n_bottom))
            tp.dispense(self._supernatant_removal_air_gap, locationFrom="target", well_modifier="top(0)")
            for i in range(self._n_bottom):
                aspirate_height = self._h_bottom - i * (self._h_bottom / (self._n_bottom - 1))
                tp.comment("Aspirating at {}".format(aspirate_height))
                tp.aspirate(self._supernatant_removal_last_transfer_max_vol/self._n_bottom,
                            locationFrom="target",
                            well_modifier="bottom({})".format(aspirate_height))

            back_step = 0.1
            n_back_step = 3
            for _ in range(n_back_step):
                aspirate_height = aspirate_height + back_step
                tp.comment("Moving up at {}".format(aspirate_height))
                tp.move_to(locationFrom="target", well_modifier="bottom({})".format(aspirate_height))

            tp.air_gap(self._supernatant_removal_air_gap)
            tp.dispense(self._supernatant_removal_last_transfer_max_vol + self._supernatant_removal_air_gap,
                        locationFrom="waste_locs")
            tp.air_gap(self._supernatant_removal_air_gap)
            tp.drop_tip()

        self._m300.flow_rate.aspirate = self._default_aspiration_rate
        self._m300r.flow_rate.aspirate = self._default_aspiration_rate

    def elute(self, positions=None, transfer: bool = False, stage: str = "elute"):
        if positions is None:
            positions = self.temp_samples_m
        self._magdeck.disengage()
        self._elute(positions=positions, transfer=transfer, stage=stage)
        self._magdeck.disengage()

    def _elute(self, positions=None, transfer: bool = True, stage: str = "elute"):
        """Resuspend beads in elution"""
        # if positions is None:
        #     positions = self.mag_samples_m
        self._m300.flow_rate.aspirate = self._elute_aspiration_rate

        side_locs = []
        for i, m in enumerate(positions):
            side = 1 if i % 2 == 0 else -1
            side_locs.append(m.bottom(self._bottom_headroom_height).move(Point(x=side * 2)))

        with PairedPipette(self._tempplate, positions, side_locs=side_locs, start_at=stage) as tp:
            tp.pick_up()
            tp.aspirate(self._elution_vol, self.water)
            tp.air_gap(self._elute_air_gap)
            tp.dispense(self._elute_air_gap, locationFrom="target", well_modifier="top(0)")
            tp.dispense(self._elution_vol, locationFrom="side_locs")
            tp.mix(self._elute_mix_times, self._elute_mix_vol, locationFrom="side_locs")
            tp.touch_tip(v_offset=self._touch_tip_height)
            tp.air_gap(self._elute_air_gap)
            tp.drop_tip()

    def final_transfer(self):
        self._m300.flow_rate.aspirate = self._final_transfer_rate_aspirate
        self._m300r.flow_rate.aspirate = self._final_transfer_rate_aspirate
        self._m300.flow_rate.dispense = self._final_transfer_rate_dispense
        self._m300r.flow_rate.dispense = self._final_transfer_rate_dispense

        n = len(list(zip(self.mag_samples_m, self.pcr_samples_m)))

        locs = []
        for i, (m, e) in enumerate(zip(self.mag_samples_m, self.pcr_samples_m)):
            side = -1 if i % 2 == 0 else 1
            locs.append(m.bottom(0.3).move(Point(x=side * 2)))

        with PairedPipette(self._magplate, locs, start_at="final transfer", pcr_locs=self.pcr_samples_m) as tp:
            tp.pick_up()
            tp.aspirate(self._final_vol, locationFrom="target")
            tp.air_gap(self._elute_air_gap)
            tp.dispense(self._elute_air_gap, locationFrom="pcr_locs", well_modifier="top(0)")
            tp.dispense(self._final_vol, locationFrom="pcr_locs", well_modifier="bottom(0.5)")
            tp.mix(self._final_mix_times, self._final_mix_vol, locationFrom="pcr_locs",
                   well_modifier="bottom({})".format(self._final_mix_height))
            tp.air_gap(self._elute_air_gap)
            tp.drop_tip()

    def wash(self, vol: float, source, mix_reps: int, wash_name: str = "wash"):
        self.logger.info(self.msg_format("wash info", vol, wash_name, mix_reps))

        if wash_name == "wash 1":
            dispense_rate = self._wash_1_mix_dispense_rate
            self._m300.flow_rate.dispense = self._wash_1_mix_dispense_rate
            self._m300r.flow_rate.dispense = self._wash_1_mix_dispense_rate
            self._m300.flow_rate.aspirate = self._wash_1_mix_aspiration_rate
            self._m300r.flow_rate.aspirate = self._wash_1_mix_aspiration_rate
        else:
            dispense_rate = self._wash_2_mix_dispense_rate
            self._m300.flow_rate.dispense = self._wash_2_mix_dispense_rate
            self._m300r.flow_rate.dispense = self._wash_2_mix_dispense_rate
            self._m300.flow_rate.aspirate = self._wash_2_mix_aspiration_rate
            self._m300r.flow_rate.aspirate = self._wash_2_mix_aspiration_rate
        self._magdeck.disengage()

        num_trans, vol_per_trans = uniform_divide(vol, self._wash_max_transfer_vol)

        src = []
        mix_locs = []
        wash_locs = []
        wash_locs_index = [0, 0, 1, 1, 4, 4, 5, 5, 2, 2, 3, 3]

        for i, m in enumerate(self.mag_samples_m):
            wash_locs.append(source[wash_locs_index[i]])
            src.append(self.wash_getcol(i, len(self.mag_samples_m), source))
            mix_locs.append(m.bottom(self._bottom_headroom_height).move(Point(x=2 * (-1 if i % 2 else +1))))

        with PairedPipette(self._magplate, self.mag_samples_m,
                           wash_locs=wash_locs,
                           mix_locs=mix_locs,
                           start_at=wash_name) as tp:
            tp.pick_up()
            for n in range(num_trans):
                if n > 0:
                    tp.dispense(self._wash_air_gap, locationFrom="wash_locs", well_modifier="top(0)")
                tp.aspirate(vol_per_trans, locationFrom="wash_locs")
                tp.air_gap(self._wash_air_gap)
                tp.dispense(vol_per_trans+self._wash_air_gap, locationFrom="target", well_modifier="top(0)")
                if n < num_trans-1:
                    tp.air_gap(self._wash_air_gap)

            # Mix
            tp.mix(mix_reps, self._wash_mix_vol, locationFrom="mix_locs")
            tp.air_gap(self._wash_air_gap)
            tp.drop_tip()

        self._magdeck.engage(height=self._magheight)
        self.check()
        if self.run_stage("{} incubate".format(wash_name)):
            self.delay(self._wait_time_wash_on, self.get_msg_format("incubate on magdeck", self.get_msg("on")))
        self.remove_supernatant(vol, stage="remove {}".format(wash_name))

if __name__ == "__main__":
    station = StationBTechnogeneticsPairedPipette(metadata={'apiLevel': '2.3'},
                                                  num_samples=96)
    # logging.getLogger(StationBTechnogeneticsPairedPipette.__name__).setLevel(logging.DEBUG)
    station.simulate()
