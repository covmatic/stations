import unittest
from .common_stations import STATIONS


class FakeDelayPauseStation:
    # Extending the class to intercept the transfer_sample call
    def __init__(self, **kwargs):
        print("FakeSampleTransfer INIT!!!")
        super().__init__(**kwargs)
        self._test_pause_call = 0
        self._test_delay_call = 0

    def pause(self, *args, **kwargs):
        self._test_pause_call += 1

    def delay(self, *args, **kwargs):
        self._test_delay_call += 1


class TestSuite(unittest.TestCase):
    def test_stations_fake_start_at_goes_in_error(self):
        for S in STATIONS:
            print("Creating subclass for {}".format(S))

            class FakeStation(FakeDelayPauseStation, S):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)

            fs = FakeStation(num_samples=96, metadata={'apiLevel': '2.7'}, start_at="fake start at")
            try:
                fs.simulate()
            except Exception:
                pass
            else:
                assert False, "{} Exception should have been thrown here.".format(S)

    def test_stations_pause_and_delay_are_inside_start_at(self):
        # We use here a fake star at to go through the protocol.
        for S in STATIONS:
            print("Creating subclass for {}".format(S))

            class FakeStation(FakeDelayPauseStation, S):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)

            fs = FakeStation(num_samples=96, metadata={'apiLevel': '2.7'}, start_at="fake start at")
            try:
                fs.simulate()
            except Exception:
                # we should be at the end of the protocol
                pass
            else:
                assert False, "Exception should have been thrown here."
            # Checking
            assert fs._test_pause_call == 0, \
                "{}: Pause command is called outside start_at; count: {}\n".format(S, fs._test_pause_call)
            assert fs._test_delay_call == 0, \
                "{}: Delay command is called outside start_at; count: {}".format(S, fs._test_delay_call)


if __name__ == '__main__':
    unittest.main()
