import unittest
from covmatic_stations.a.technogenetics import StationATechnogenetics48

traceability_order = [
    # Column 1
    # ("A1", "A1")       # From version 1.2.4 the negative-control is not transferred
    ("B1", "B1"),
    ("C1", "C1"),
    ("D1", "D1"),
    ("E1", "E1"),
    ("F1", "F1"),
    ("G1", "G1"),
    ("H1", "H1"),
    # Column 2
    ("A2", "A2"),
    ("B2", "B2"),
    ("C2", "C2"),
    ("D2", "D2"),
    ("E2", "E2"),
    ("F2", "F2"),
    ("G2", "G2"),
    ("H2", "H2"),
    # Column 3
    ("A3", "A3"),
    ("B3", "B3"),
    ("C3", "C3"),
    ("D3", "D3"),
    ("E3", "E3"),
    ("F3", "F3"),
    ("G3", "G3"),
    ("H3", "H3"),
    # Column 4
    ("A4", "A4"),
    ("B4", "B4"),
    ("C4", "C4"),
    ("D4", "D4"),
    ("E4", "E4"),
    ("F4", "F4"),
    ("G4", "G4"),
    ("H4", "H4"),
    # Column 5
    ("A5", "A5"),
    ("B5", "B5"),
    ("C5", "C5"),
    ("D5", "D5"),
    ("E5", "E5"),
    ("F5", "F5"),
    ("G5", "G5"),
    ("H5", "H5"),
    # Column 6
    ("A6", "A6"),
    ("B6", "B6"),
    ("C6", "C6"),
    ("D6", "D6"),
    ("E6", "E6"),
    ("F6", "F6"),
    ("G6", "G6"),
    ("H6", "H6"),
    # Column 7
    ("A1", "A7"),
    ("B1", "B7"),
    ("C1", "C7"),
    ("D1", "D7"),
    ("E1", "E7"),
    ("F1", "F7"),
    ("G1", "G7"),
    ("H1", "H7"),
    # Column 8
    ("A2", "A8"),
    ("B2", "B8"),
    ("C2", "C8"),
    ("D2", "D8"),
    ("E2", "E8"),
    ("F2", "F8"),
    ("G2", "G8"),
    ("H2", "H8"),
    # Column 9
    ("A3", "A9"),
    ("B3", "B9"),
    ("C3", "C9"),
    ("D3", "D9"),
    ("E3", "E9"),
    ("F3", "F9"),
    ("G3", "G9"),
    ("H3", "H9"),
    # Column 10
    ("A4", "A10"),
    ("B4", "B10"),
    ("C4", "C10"),
    ("D4", "D10"),
    ("E4", "E10"),
    ("F4", "F10"),
    ("G4", "G10"),
    ("H4", "H10"),
    # Column 11
    ("A5", "A11"),
    ("B5", "B11"),
    ("C5", "C11"),
    ("D5", "D11"),
    ("E5", "E11"),
    ("F5", "F11"),
    ("G5", "G11"),
    ("H5", "H11"),
    # Column 12
    ("A6", "A12"),
    ("B6", "B12"),
    ("C6", "C12"),
    ("D6", "D12"),
    ("E6", "E12"),
    ("F6", "F12"),
    ("G6", "G12"),
    ("H6", "H12"),
]


class TestSuite(unittest.TestCase):
    def test_transfer_sample_order(self):
        # Extending the class to intercept the transfer_sample call
        class FakeStationATechnogenetics48(StationATechnogenetics48):
            def __init__(self, *args, **kwargs):
                super(FakeStationATechnogenetics48, self).__init__(*args, **kwargs)
                self._test_sample_index = 0

            # Fake transfer sample function.
            # Each call we check the order is the one expected
            def transfer_sample(self, source, dest):
                expected_source_well_name, expected_dest_well_name = traceability_order[self._test_sample_index]
                assert expected_source_well_name == source.well_name, \
                    "Got source {}; expecting {}".format(source.well_name, expected_source_well_name)
                assert expected_dest_well_name == dest.well_name, \
                    "Got dest {}; expecting {}".format(dest.well_name, expected_dest_well_name)
                self._test_sample_index += 1

        FakeStationATechnogenetics48(num_samples=96, metadata={'apiLevel': '2.7'}).simulate()


if __name__ == '__main__':
    unittest.main()
