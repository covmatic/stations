import unittest
from covmatic_stations.a.technogenetics import StationATechnogenetics48, StationATechnogenetics48Saliva
from covmatic_stations.station import Station

expected_slot_for_source_rack = "2"

expected_traceability_order = [
    # Column 1
    # ("A1", "A1")       # From version 1.2.4 the negative-control is not transferred
    ("B1", "B1", expected_slot_for_source_rack),
    ("C1", "C1", expected_slot_for_source_rack),
    ("D1", "D1", expected_slot_for_source_rack),
    ("E1", "E1", expected_slot_for_source_rack),
    ("F1", "F1", expected_slot_for_source_rack),
    ("G1", "G1", expected_slot_for_source_rack),
    ("H1", "H1", expected_slot_for_source_rack),
    # Column 2
    ("A2", "A2", expected_slot_for_source_rack),
    ("B2", "B2", expected_slot_for_source_rack),
    ("C2", "C2", expected_slot_for_source_rack),
    ("D2", "D2", expected_slot_for_source_rack),
    ("E2", "E2", expected_slot_for_source_rack),
    ("F2", "F2", expected_slot_for_source_rack),
    ("G2", "G2", expected_slot_for_source_rack),
    ("H2", "H2", expected_slot_for_source_rack),
    # Column 3
    ("A3", "A3", expected_slot_for_source_rack),
    ("B3", "B3", expected_slot_for_source_rack),
    ("C3", "C3", expected_slot_for_source_rack),
    ("D3", "D3", expected_slot_for_source_rack),
    ("E3", "E3", expected_slot_for_source_rack),
    ("F3", "F3", expected_slot_for_source_rack),
    ("G3", "G3", expected_slot_for_source_rack),
    ("H3", "H3", expected_slot_for_source_rack),
    # Column 4
    ("A4", "A4", expected_slot_for_source_rack),
    ("B4", "B4", expected_slot_for_source_rack),
    ("C4", "C4", expected_slot_for_source_rack),
    ("D4", "D4", expected_slot_for_source_rack),
    ("E4", "E4", expected_slot_for_source_rack),
    ("F4", "F4", expected_slot_for_source_rack),
    ("G4", "G4", expected_slot_for_source_rack),
    ("H4", "H4", expected_slot_for_source_rack),
    # Column 5
    ("A5", "A5", expected_slot_for_source_rack),
    ("B5", "B5", expected_slot_for_source_rack),
    ("C5", "C5", expected_slot_for_source_rack),
    ("D5", "D5", expected_slot_for_source_rack),
    ("E5", "E5", expected_slot_for_source_rack),
    ("F5", "F5", expected_slot_for_source_rack),
    ("G5", "G5", expected_slot_for_source_rack),
    ("H5", "H5", expected_slot_for_source_rack),
    # Column 6
    ("A6", "A6", expected_slot_for_source_rack),
    ("B6", "B6", expected_slot_for_source_rack),
    ("C6", "C6", expected_slot_for_source_rack),
    ("D6", "D6", expected_slot_for_source_rack),
    ("E6", "E6", expected_slot_for_source_rack),
    ("F6", "F6", expected_slot_for_source_rack),
    ("G6", "G6", expected_slot_for_source_rack),
    ("H6", "H6", expected_slot_for_source_rack),
    # Column 7
    ("A1", "A7", expected_slot_for_source_rack),
    ("B1", "B7", expected_slot_for_source_rack),
    ("C1", "C7", expected_slot_for_source_rack),
    ("D1", "D7", expected_slot_for_source_rack),
    ("E1", "E7", expected_slot_for_source_rack),
    ("F1", "F7", expected_slot_for_source_rack),
    ("G1", "G7", expected_slot_for_source_rack),
    ("H1", "H7", expected_slot_for_source_rack),
    # Column 8
    ("A2", "A8", expected_slot_for_source_rack),
    ("B2", "B8", expected_slot_for_source_rack),
    ("C2", "C8", expected_slot_for_source_rack),
    ("D2", "D8", expected_slot_for_source_rack),
    ("E2", "E8", expected_slot_for_source_rack),
    ("F2", "F8", expected_slot_for_source_rack),
    ("G2", "G8", expected_slot_for_source_rack),
    ("H2", "H8", expected_slot_for_source_rack),
    # Column 9
    ("A3", "A9", expected_slot_for_source_rack),
    ("B3", "B9", expected_slot_for_source_rack),
    ("C3", "C9", expected_slot_for_source_rack),
    ("D3", "D9", expected_slot_for_source_rack),
    ("E3", "E9", expected_slot_for_source_rack),
    ("F3", "F9", expected_slot_for_source_rack),
    ("G3", "G9", expected_slot_for_source_rack),
    ("H3", "H9", expected_slot_for_source_rack),
    # Column 10
    ("A4", "A10", expected_slot_for_source_rack),
    ("B4", "B10", expected_slot_for_source_rack),
    ("C4", "C10", expected_slot_for_source_rack),
    ("D4", "D10", expected_slot_for_source_rack),
    ("E4", "E10", expected_slot_for_source_rack),
    ("F4", "F10", expected_slot_for_source_rack),
    ("G4", "G10", expected_slot_for_source_rack),
    ("H4", "H10", expected_slot_for_source_rack),
    # Column 11
    ("A5", "A11", expected_slot_for_source_rack),
    ("B5", "B11", expected_slot_for_source_rack),
    ("C5", "C11", expected_slot_for_source_rack),
    ("D5", "D11", expected_slot_for_source_rack),
    ("E5", "E11", expected_slot_for_source_rack),
    ("F5", "F11", expected_slot_for_source_rack),
    ("G5", "G11", expected_slot_for_source_rack),
    ("H5", "H11", expected_slot_for_source_rack),
    # Column 12
    ("A6", "A12", expected_slot_for_source_rack),
    ("B6", "B12", expected_slot_for_source_rack),
    ("C6", "C12", expected_slot_for_source_rack),
    ("D6", "D12", expected_slot_for_source_rack),
    ("E6", "E12", expected_slot_for_source_rack),
    ("F6", "F12", expected_slot_for_source_rack),
    ("G6", "G12", expected_slot_for_source_rack),
    ("H6", "H12", expected_slot_for_source_rack),
]


class FakeSampleTransfer:
    # Extending the class to intercept the transfer_sample call
    def __init__(self, traceability_order, **kwargs):
        print("FakeSampleTransfer INIT!!!")
        super().__init__(**kwargs)
        self._test_sample_index = 0
        self._traceability_order = traceability_order

    # Fake transfer sample function.
    # Each call we check the order is as expected
    def transfer_sample(self, source, dest):
        expected_source_well_name, expected_dest_well_name, expected_slot = self._traceability_order[
            self._test_sample_index]
        assert expected_source_well_name == source.well_name, \
            "Got source {}; expecting {}".format(source.well_name, expected_source_well_name)
        assert expected_dest_well_name == dest.well_name, \
            "Got dest {}; expecting {}".format(dest.well_name, expected_dest_well_name)
        assert expected_slot == source.parent.parent,\
            "Got source slot {}; expecting {}".format(source.parent.parent, expected_slot)
        self._test_sample_index += 1

    def execute_test(self):
        self.simulate()
        assert self._test_sample_index > 0, "transfer_sample never called!"


class TestSuite(unittest.TestCase):
    def test_transfer_sample_order(self):
        # Extending the class to intercept the transfer_sample call
        class FakeStationATechnogenetics48(FakeSampleTransfer, StationATechnogenetics48):
            def __init__(self, *args, **kwargs):
                super().__init__(traceability_order=expected_traceability_order, *args, **kwargs)

        FakeStationATechnogenetics48(num_samples=96, metadata={'apiLevel': '2.7'}).execute_test()

    def test_transfer_sample_order_saliva(self):
        # Extending the class to intercept the transfer_sample call
        class FakeStationATechnogenetics48Saliva(FakeSampleTransfer, StationATechnogenetics48Saliva):
            def __init__(self, *args, **kwargs):
                super().__init__(traceability_order=expected_traceability_order, *args, **kwargs)

        FakeStationATechnogenetics48Saliva(num_samples=96, metadata={'apiLevel': '2.7'}).execute_test()

if __name__ == '__main__':
    unittest.main()
