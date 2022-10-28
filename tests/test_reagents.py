import unittest
from covmatic_stations.reagents import ReagentsHelper, Reagent, ReagentException
from opentrons.protocol_api.labware import Well

class InitialTesting(unittest.TestCase):
    def test_reagent_helper_creation(self):
        rh = ReagentsHelper()
        self.assertTrue(rh)

    def test_reagent_creation(self):
        r = Reagent(name="Test")
        self.assertTrue(r)


class ReagentsHelperTesting(unittest.TestCase):
    def setUp(self) -> None:
        self._rh = ReagentsHelper()
        self._r = Reagent(name="Test")

    def test_reagents_list_is_empty(self):
        self.assertEqual(0, len(self._rh._reagents))

    def test_reagent_is_registered(self):
        self._rh.register_reagent(self._r)
        self.assertTrue(len(self._rh._reagents) == 1)

    def test_registered_is_the_same(self):
        self._rh.register_reagent(self._r)
        self.assertTrue(self._rh._reagents[0] == self._r)

    def tearDown(self) -> None:
        pass


class FakeWell(Well):
    def __init__(self):
        pass

    def __repr__(self):
        return "FakeWell"


test_volume = 10


class ReagentTesting(unittest.TestCase):
    def setUp(self) -> None:
        self._r = Reagent(name="Test")

    def test_add_well(self):
        self._r.add_well(FakeWell(), test_volume)

    def test_add_well_check_type(self):
        with self.assertRaises(ReagentException):
            self._r.add_well(10, test_volume)

    def test_well_is_added(self):
        fw = FakeWell()
        self._r.add_well(fw, test_volume)
        self.assertTrue(self._r._tubes.num_tubes == 1)

    def tearDown(self) -> None:
        pass


if __name__ == '__main__':
    unittest.main()
