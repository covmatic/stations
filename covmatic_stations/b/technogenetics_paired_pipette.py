from covmatic_stations.station import instrument_loader
from .technogenetics import StationBTechnogenetics
from ..paired_pipette import PairedPipette
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
        # super(StationBTechnogeneticsPairedPipette, self).body()

        # self.mix_samples()
        self.remove_supernatant(self._starting_vol)

    def mix_samples(self):
        self._m300.flow_rate.aspirate = 94
        self._m300r.flow_rate.aspirate = 94

        with PairedPipette(self._magplate, self.mag_samples_m) as tp:
            tp.pick_up()
            tp.mix(self._sample_mix_times, self._sample_mix_vol,
                   location="target",
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
            tp.move_to(location="target", well_modifier="top(0)")
            tp.air_gap(self._supernatant_removal_air_gap)
            for _ in range(num_trans):
                tp.move_to(location="target", well_modifier="top(0)")  # we want center() but for now it is not in available commands
                tp.dispense(self._supernatant_removal_air_gap)
                tp.aspirate(vol_per_trans, location="target", well_modifier="bottom({})".format(self._supernatant_removal_height))
                tp.air_gap(self._supernatant_removal_air_gap)
                tp.dispense(vol_per_trans+self._supernatant_removal_air_gap, self._waste)
                tp.air_gap(self._supernatant_removal_air_gap)

            tp.comment("Supernatant removal: last transfer in {} step".format(self._n_bottom))
            tp.dispense(self._supernatant_removal_air_gap, location="target", well_modifier="top(0)")
            for j in range(self._n_bottom):
                aspirate_height = self._h_bottom - (j) * (self._h_bottom / (self._n_bottom - 1))
                tp.comment("Aspirating at {}".format(aspirate_height))
                tp.aspirate(self._supernatant_removal_last_transfer_max_vol/self._n_bottom,
                            location="target",
                            well_modifier="bottom({})".format(aspirate_height))

            back_step = 0.1
            n_back_step = 3
            for _ in range(n_back_step):
                aspirate_height = aspirate_height + back_step
                tp.comment("Moving up at {}".format(aspirate_height))
                tp.move_to(location="target", well_modifier="bottom({})".format(aspirate_height))

            tp.air_gap(self._supernatant_removal_air_gap)
            tp.dispense(self._supernatant_removal_last_transfer_max_vol + self._supernatant_removal_air_gap,
                        self._waste)
            tp.air_gap(self._supernatant_removal_air_gap)
            tp.drop_tip()

        self._m300.flow_rate.aspirate = self._default_aspiration_rate
        self._m300r.flow_rate.aspirate = self._default_aspiration_rate

    def drop_tip(self, pip):
        self._logger.error("PLEASE DISABLE THIS DEBUG FEATURE!!")
        pip.return_tip()

if __name__ == "__main__":
    StationBTechnogeneticsPairedPipette(metadata={'apiLevel': '2.3'}, num_samples=64).simulate()

