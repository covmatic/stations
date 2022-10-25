import unittest
from covmatic_stations.reagents import ReagentsHelper, Reagent


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


if __name__ == '__main__':
    unittest.main()
