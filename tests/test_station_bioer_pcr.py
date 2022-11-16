import unittest
from covmatic_stations.bioer.Bioer_full_dw import BioerPreparationToPcr
from covmatic_stations.station import Station


class FakeSampleTransfer:
    # Extending the class to intercept the transfer_sample call
    def __init__(self, expected_total_samples, **kwargs):
        print("FakeSampleTransfer INIT!!!")
        super().__init__(**kwargs)
        self._test_sample_index = 0
        self._expected_total_samples = expected_total_samples

    # Fake transfer sample function.
    # Each call we check the order is as expected
    def transfer_elute(self, source, dest, pipette):
        print("Transferring {} samples from {} to {}".format(pipette.channels, source, dest))
        self._test_sample_index += pipette.channels

    def execute_test(self):
        self.simulate()
        assert self._test_sample_index > 0, "transfer_sample never called!"
        assert self._test_sample_index == self._expected_total_samples, \
            "Wrong number of samples transferred: expected {} got {}".format(self._expected_total_samples, self._test_sample_index)


# Extending the class to intercept the transfer_sample call
class FakeStation(FakeSampleTransfer, BioerPreparationToPcr):
    def __init__(self, num_samples, expected_total_samples, *args, **kwargs):
        super().__init__(expected_total_samples=expected_total_samples, num_samples=num_samples, *args, **kwargs)


class TestSuite(unittest.TestCase):
    def test_transfer_full_plate(self):
        FakeStation(num_samples=94, expected_total_samples=94, metadata={'apiLevel': '2.7'}).execute_test()

    def test_transfer_full_plate_96(self):
        FakeStation(num_samples=96, expected_total_samples=94, metadata={'apiLevel': '2.7'}).execute_test()

    def test_transfer_half_plate(self):
        FakeStation(num_samples=48, expected_total_samples=48, metadata={'apiLevel': '2.7'}).execute_test()

    def test_transfer_full_column(self):
        FakeStation(num_samples=80, expected_total_samples=80, metadata={'apiLevel': '2.7'}).execute_test()

    def test_transfer_incomplete_control_column_use_single_pipette(self):
        FakeStation(num_samples=93, expected_total_samples=93, metadata={'apiLevel': '2.7'}).execute_test()

    def test_transfer_incomplete_column_use_multi_pipette(self):
        FakeStation(num_samples=81, expected_total_samples=88, metadata={'apiLevel': '2.7'}).execute_test()

    # def test_transfer_sample_order_saliva(self):
    #     # Extending the class to intercept the transfer_sample call
    #     class FakeStationATechnogenetics48Saliva(FakeSampleTransfer, StationATechnogenetics48Saliva):
    #         def __init__(self, *args, **kwargs):
    #             super().__init__(traceability_order=expected_traceability_order, *args, **kwargs)
    #
    #     FakeStationATechnogenetics48Saliva(num_samples=96, metadata={'apiLevel': '2.7'}).execute_test()


if __name__ == '__main__':
    unittest.main()
