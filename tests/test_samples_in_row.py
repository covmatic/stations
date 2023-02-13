import unittest

from covmatic_stations.station import Station


class FakeStation(Station):
    def _tipracks(self) -> dict:
        return {}

class TestSamplesInRow(unittest.TestCase):
    def setUp(self):
        self._s = FakeStation()

    def test_samples_in_row_1(self):
        self._s._num_samples = 1
        self.assertEqual(1, self._s.get_samples_in_row(0))

    def test_samples_in_row_1_others(self):
        self._s._num_samples = 1
        for i in range(1, 8):
            self.assertEqual(0, self._s.get_samples_in_row(i), "row {}".format(i))
    def test_samples_in_row_8(self):
        self._s._num_samples = 8
        for i in range(8):
            self.assertEqual(1, self._s.get_samples_in_row(i), "row {}".format(i))

    def test_samples_in_row_9(self):
        self._s._num_samples = 9
        self.assertEqual(2, self._s.get_samples_in_row(0))
        for i in range(1, 8):
            self.assertEqual(1, self._s.get_samples_in_row(i), "row {}".format(i))

    def test_samples_in_row_10(self):
        self._s._num_samples = 10
        self.assertEqual(2, self._s.get_samples_in_row(0))
        self.assertEqual(2, self._s.get_samples_in_row(1))
        for i in range(2, 8):
            self.assertEqual(1, self._s.get_samples_in_row(i), "row {}".format(i))

    def test_samples_in_row_64(self):
        self._s._num_samples = 64
        for i in range(8):
            self.assertEqual(8, self._s.get_samples_in_row(i), "row {}".format(i))

    def test_samples_in_row_95(self):
        self._s._num_samples = 95
        for i in range(7):
            self.assertEqual(12, self._s.get_samples_in_row(i), "row {}".format(i))
        self.assertEqual(11, self._s.get_samples_in_row(7))

    def test_samples_in_row_96(self):
        self._s._num_samples = 96
        for i in range(8):
            self.assertEqual(12, self._s.get_samples_in_row(i), "row {}".format(i))

    def test_samples_row_limit_high(self):
        self._s._num_samples = 96
        with self.assertRaises(Exception):
            self._s.get_samples_in_row(8)

    def test_samples_row_limit_low(self):
        self._s._num_samples = 96
        with self.assertRaises(Exception):
            self._s.get_samples_in_row(-1)