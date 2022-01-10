from .station import Station, labware_loader, instrument_loader


class ParkTest(Station):
    def __init__(self,
                 num_samples: int = 16,
                 ** kwargs):

        assert num_samples <= 16, "Protocol must be used with 16 or less samples"

        super(ParkTest, self).__init__(
            num_samples=num_samples,
            ** kwargs)

    @labware_loader(0, "_tips20")
    def load_tips20(self):
        self._tips20 = [self._ctx.load_labware('opentrons_96_filtertiprack_20ul', slot, '20ul filter tiprack')
                                for slot in ['10']]


    @instrument_loader(0, "_m20")
    def load_m20(self):
        self._m20 = self._ctx.load_instrument('p20_single_gen2', 'left', tip_racks=self._tips20)


    def _tipracks(self) -> dict:
        return {"_tips20": "_m20"}

    def body(self):
        self.pick_up(self._m20)
        self._m20.aspirate(10)
        self.park_tip(self._m20, None)
        self.reuse_tip(self._m20, None)
        self.drop(self._m20)
        print(self._park_manager.tips)
        # self.reuse_
        # self.drop(self._m20)


if __name__ == "__main__":
    ParkTest(metadata={'apiLevel':'2.7'}).simulate()