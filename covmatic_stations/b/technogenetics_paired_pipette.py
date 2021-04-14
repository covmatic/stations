from covmatic_stations.station import instrument_loader
from .technogenetics import StationBTechnogenetics
from ..paired_pipette import TestPaired

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

        self.mix_samples()

    def mix_samples(self):
        self._m300.flow_rate.aspirate = 94
        self._m300r.flow_rate.aspirate = 94

        with TestPaired(self._magplate, self.mag_samples_m) as tp:
            tp.pick_up()
            tp.mix(self._sample_mix_times, self._sample_mix_vol,
                   location="target",
                   well_modifier="bottom({})".format(self._sample_mix_height))
            tp.drop_tip()

        # for i, m in enumerate(self.mag_samples_m):
        #     if self.run_stage("mix sample {}/{}".format(i + 1, len(self.mag_samples_m))):
        #         self.pick_up(self._m300)
        #         self._m300.mix(self._sample_mix_times, self._sample_mix_vol, m.bottom(self._sample_mix_height))
        #         self._m300.air_gap(self._bind_air_gap)
        #         self.drop(self._m300)


if __name__ == "__main__":
    StationBTechnogeneticsPairedPipette(metadata={'apiLevel': '2.3'}).simulate()

