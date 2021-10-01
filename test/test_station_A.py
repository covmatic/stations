import unittest
from ..a.technogenetics import StationATechnogenetics48


class MyTestCase(unittest.TestCase):
    def test_something(self):
        StationATechnogenetics48(num_samples=96, metadata={'apiLevel': '2.7'}).simulate()
        self.assertEqual(True, False)


if __name__ == '__main__':
    unittest.main()
