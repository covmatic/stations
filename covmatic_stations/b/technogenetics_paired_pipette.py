from covmatic_stations.station import instrument_loader
from .technogenetics import StationBTechnogenetics
from ..paired_pipette import TestPaired
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
        TestPaired.setup(self._m300, self._m300r)
        # super(StationBTechnogeneticsPairedPipette, self).body()

        # self.mix_samples()
        self.remove_supernatant(self._starting_vol)

    def mix_samples(self):
        self._m300.flow_rate.aspirate = 94
        self._m300r.flow_rate.aspirate = 94

        with TestPaired(self._magplate, self.mag_samples_m) as tp:
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
        # h_num_trans = self._h_trans/num_trans

        for i, m in enumerate(self.mag_samples_m):
            loc = m.bottom(self._supernatant_removal_height)

            with TestPaired(self._magplate, self.mag_samples_m) as tp:
                tp.pick_up()
                for _ in range(num_trans):
                    tp.move_to(location="target", well_modifier="top(0)")  # we want center() but for now it is not in available commands
                tp.drop_tip()

        #     if self.run_stage("{} {}/{}".format(stage, i + 1, len(self.mag_samples_m))):
        #         self.pick_up(self._m300)
        #         loc = m.bottom(self._supernatant_removal_height)
        #         self._ctx.comment("Supernatant removal: {} transfer with {}ul each.".format(num_trans, vol_per_trans))
        #         for _ in range(num_trans):
        #             # num_trans = num_trans - 1
        #             # aspirate_height = self.h_bottom + (num_trans * h_num_trans) # expecting aspirated height
        #             # ctx.comment('Aspirating at {}'.format(aspirate_height))
        #             if self._m300.current_volume > 0:
        #                 self._m300.dispense(self._m300.current_volume, m.top())
        #             self._m300.move_to(m.center())
        #             self._m300.transfer(vol_per_trans, loc, self._waste, new_tip='never', air_gap=self._supernatant_removal_air_gap)
        #             self._m300.air_gap(self._supernatant_removal_air_gap)
        #
        #         self._ctx.comment("Supernatant removal: last transfer in {} step".format(self._n_bottom))
        #         # dispensing the air gap present in the tip
        #         if self._m300.current_volume > 0:
        #             self._m300.dispense(self._m300.current_volume, m.top())
        #
        #         for j in range(self._n_bottom):
        #             aspirate_height = self._h_bottom - (j)*(self._h_bottom/(self._n_bottom-1)) # expecting aspirated height
        #             self._ctx.comment("Aspirating at {}".format(aspirate_height))
        #             loc = m.bottom(aspirate_height)
        #             self._m300.aspirate(self._supernatant_removal_last_transfer_max_vol/self._n_bottom, loc)
        #
        #         back_step = 0.1
        #         n_back_step = 3
        #         for _ in range(n_back_step):
        #             aspirate_height = aspirate_height + back_step
        #             self._ctx.comment("Moving up at {}".format(aspirate_height))
        #             loc = m.bottom(aspirate_height)
        #             self._m300.move_to(loc)
        #
        #         self._m300.air_gap(self._supernatant_removal_air_gap)
        #         self._m300.dispense(self._m300.current_volume, self._waste)
        #         self._m300.air_gap(self._supernatant_removal_air_gap)
        #         self.drop(self._m300)
        # self._m300.flow_rate.aspirate = self._default_aspiration_rate

if __name__ == "__main__":
    StationBTechnogeneticsPairedPipette(metadata={'apiLevel': '2.3'}).simulate()

