from covmatic_stations.station import instrument_loader
from covmatic_stations.utils import uniform_divide
from .technogenetics import StationBTechnogenetics
from ..paired_pipette import PairedPipette
from opentrons.types import Point
from itertools import repeat
import math

class StationBTechnogeneticsPairedPipette(StationBTechnogenetics):

    def __init__(self, **kwargs):
        super(StationBTechnogeneticsPairedPipette, self).__init__(**kwargs)

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

        # self.mix_samples()
        # self.remove_supernatant(self._starting_vol)
        # self.elute()

    def mix_samples(self):
        self._m300.flow_rate.aspirate = 94
        self._m300r.flow_rate.aspirate = 94

        with PairedPipette(self._magplate, self.mag_samples_m) as tp:
            tp.pick_up()
            tp.mix(self._sample_mix_times, self._sample_mix_vol,
                   locationFrom="target",
                   well_modifier="bottom({})".format(self._sample_mix_height))
            tp.air_gap(self._bind_air_gap)
            tp.drop_tip()

        # for i, m in enumerate(self.mag_samples_m):
        #     if self.run_stage("mix sample {}/{}".format(i + 1, len(self.mag_samples_m))):
        #         self.pick_up(self._m300)
        #         self._m300.mix(self._sample_mix_times, self._sample_mix_vol, m.bottom(self._sample_mix_height))
        #         self._m300.air_gap(self._bind_air_gap)
        #         self.drop(self._m300)


    def remove_supernatant(self, vol: float, stage: str = "remove supernatant"):
        self._m300.flow_rate.aspirate = self._supernatant_removal_aspiration_rate
        self._m300r.flow_rate.aspirate = self._supernatant_removal_aspiration_rate

        num_trans = math.ceil((vol - self._vol_last_trans) / self._bind_max_transfer_vol)
        vol_per_trans = ((vol - self._vol_last_trans) / num_trans) if num_trans else 0

        with PairedPipette(self._magplate, self.mag_samples_m) as tp:
            tp.pick_up()
            # Fake air gap, maybe we can avoid it
            tp.move_to(locationFrom="target", well_modifier="top(0)")
            tp.air_gap(self._supernatant_removal_air_gap)
            for _ in range(num_trans):
                tp.move_to(locationFrom="target", well_modifier="top(0)")  # we want center() but for now it is not in available commands
                tp.dispense(self._supernatant_removal_air_gap)
                tp.aspirate(vol_per_trans, locationFrom="target", well_modifier="bottom({})".format(self._supernatant_removal_height))
                tp.air_gap(self._supernatant_removal_air_gap)
                tp.dispense(vol_per_trans+self._supernatant_removal_air_gap, self._waste)
                tp.air_gap(self._supernatant_removal_air_gap)

            tp.comment("Supernatant removal: last transfer in {} step".format(self._n_bottom))
            tp.dispense(self._supernatant_removal_air_gap, locationFrom="target", well_modifier="top(0)")
            for j in range(self._n_bottom):
                aspirate_height = self._h_bottom - (j) * (self._h_bottom / (self._n_bottom - 1))
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
                        self._waste)
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

        with PairedPipette(self._tempplate, positions, side_locs=side_locs) as tp:
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

        with PairedPipette(self._magplate, locs, pcr_locs=self.pcr_samples_m) as tp:
            tp.pick_up()
            tp.aspirate(self._final_vol, locationFrom="target")
            tp.air_gap(self._elute_air_gap)
            tp.dispense(self._elute_air_gap, locationFrom="pcr_locs", well_modifier="top(0)")
            tp.dispense(self._final_vol, locationFrom="pcr_locs", well_modifier="bottom(0.5)")
            tp.mix(self._final_mix_times, self._final_mix_vol, locationFrom="pcr_locs",
                   well_modifier="bottom({})".format(self._final_mix_height))
            tp.air_gap(self._elute_air_gap)
            tp.drop_tip()

    # def wash(self, vol: float, source, mix_reps: int, wash_name: str = "wash"):
    #     self.logger.info(self.msg_format("wash info", vol, wash_name, mix_reps))
    #     if wash_name == "wash 1":
    #         self._default_aspiration_rate = self._wash_1_mix_aspiration_rate
    #         dispense_rate = self._wash_1_mix_dispense_rate
    #         self._m300.flow_rate.dispense = self._wash_1_mix_dispense_rate
    #         self._m300.flow_rate.aspirate = self._wash_1_mix_aspiration_rate
    #         self._m300r.flow_rate.dispense = self._wash_1_mix_dispense_rate
    #         self._m300r.flow_rate.aspirate = self._wash_1_mix_aspiration_rate
    #     else:
    #         self._default_aspiration_rate = self._wash_2_mix_aspiration_rate
    #         dispense_rate = self._wash_2_mix_dispense_rate
    #         self._m300.flow_rate.dispense = self._wash_2_mix_dispense_rate
    #         self._m300.flow_rate.aspirate = self._wash_2_mix_aspiration_rate
    #         self._m300r.flow_rate.dispense = self._wash_2_mix_dispense_rate
    #         self._m300r.flow_rate.aspirate = self._wash_2_mix_aspiration_rate
    #     self._magdeck.disengage()
    #
    #     num_trans, vol_per_trans = uniform_divide(vol, self._wash_max_transfer_vol)
    #
    #     src = []
    #     for i, m in enumerate(self.mag_samples_m):
    #         src.append(self.wash_getcol(i, len(self.mag_samples_m), source))
    # #
    #     with PairedPipette()
    # self.pick_up(self._m300)
    #             for n in range(num_trans):
    #                 if self._m300.current_volume > 0:
    #                     self._m300.dispense(self._m300.current_volume, src.top())
    #                 self._m300.transfer(vol_per_trans, src, m.top(), air_gap=20, new_tip='never')
    #                 if n < num_trans - 1:  # only air_gap if going back to source
    #                     self._m300.air_gap(self._wash_air_gap)
    #
    #             # Mix
    #             if self._wash_mix_walk:
    #                 a_locs = [m.bottom(self._bottom_headroom_height).move(
    #                     Point(x=2 * (-1 if i % 2 else +1), y=2 * (2 * j / (mix_reps - 1) - 1))) for j in
    #                           range(mix_reps)]
    #                 mix_walk(self._m300, mix_reps, self._wash_mix_vol, a_locs, speed=self._wash_mix_speed,
    #                          logger=self.logger)
    #             else:
    #                 loc = m.bottom(self._bottom_headroom_height).move(Point(x=2 * (-1 if i % 2 else +1)))
    #                 self._m300.mix(mix_reps, self._wash_mix_vol, loc)
    #             self._m300.flow_rate.aspirate = self._default_aspiration_rate
    #             self._m300.flow_rate.dispense = dispense_rate
    #
    #             self._m300.air_gap(self._wash_air_gap)
    #             self.drop(self._m300)
    #
    #     self._magdeck.engage(height=self._magheight)
    #     self.check()
    #     if self.run_stage("{} incubate".format(wash_name)):
    #         self.delay(self._wait_time_wash_on, self.get_msg_format("incubate on magdeck", self.get_msg("on")))
    #     self.remove_supernatant(vol, stage="remove {}".format(wash_name))

    def drop_tip(self, pip):
        self._logger.error("PLEASE DISABLE THIS DEBUG FEATURE!!")
        pip.return_tip()

if __name__ == "__main__":
    StationBTechnogeneticsPairedPipette(metadata={'apiLevel': '2.3'}, num_samples=72).simulate()

