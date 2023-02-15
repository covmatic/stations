import unittest

from covmatic_stations.station import Station

EXPECTED_SAMPLES_1 = [1, 0, 0, 0, 0, 0, 0, 0]
EXPECTED_SAMPLES_8 = [1, 1, 1, 1, 1, 1, 1, 1]
EXPECTED_SAMPLES_9 = [2, 1, 1, 1, 1, 1, 1, 1]
EXPECTED_SAMPLES_10 = [2, 2, 1, 1, 1, 1, 1, 1]
EXPECTED_SAMPLES_64 = [8, 8, 8, 8, 8, 8, 8, 8]
EXPECTED_SAMPLES_95 = [12, 12, 12, 12, 12, 12, 12, 11]
EXPECTED_SAMPLES_96 = [12, 12, 12, 12, 12, 12, 12, 12]

class FakeStation(Station):
    def _tipracks(self) -> dict:
        return {}

class TestSamplesInRow(unittest.TestCase):
    def setUp(self):
        self._s = FakeStation()

    def check_array(self, array):
        for i in range(8):
            self.assertEqual(array[i], self._s.num_samples_in_row(i), "checking row {}".format(i))

    def test_samples_in_row_1(self):
        self._s._num_samples = 1
        self.check_array(EXPECTED_SAMPLES_1)

    def test_samples_in_row_8(self):
        self._s._num_samples = 8
        self.check_array(EXPECTED_SAMPLES_8)

    def test_samples_in_row_9(self):
        self._s._num_samples = 9
        self.check_array(EXPECTED_SAMPLES_9)

    def test_samples_in_row_10(self):
        self._s._num_samples = 10
        self.check_array(EXPECTED_SAMPLES_10)

    def test_samples_in_row_64(self):
        self._s._num_samples = 64
        self.check_array(EXPECTED_SAMPLES_64)

    def test_samples_in_row_95(self):
        self._s._num_samples = 95
        self.check_array(EXPECTED_SAMPLES_95)

    def test_samples_in_row_96(self):
        self._s._num_samples = 96
        self.check_array(EXPECTED_SAMPLES_96)

    def test_samples_row_limit_high(self):
        self._s._num_samples = 96
        with self.assertRaises(Exception):
            self._s.num_samples_in_row(8)

    def test_samples_row_limit_low(self):
        self._s._num_samples = 96
        with self.assertRaises(Exception):
            self._s.num_samples_in_row(-1)

    def test_samples_in_rows_1(self):
        self._s._num_samples = 1
        self.assertEqual(EXPECTED_SAMPLES_1, self._s.num_samples_in_rows)

    def test_samples_in_rows_95(self):
        self._s._num_samples = 95
        self.assertEqual(EXPECTED_SAMPLES_95, self._s.num_samples_in_rows)

    def test_samples_in_rows_96(self):
        self._s._num_samples = 96
        self.assertEqual(EXPECTED_SAMPLES_96, self._s.num_samples_in_rows)