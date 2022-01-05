import logging
from typing import Union
from opentrons.protocol_api import InstrumentContext, PairedInstrumentContext


class ParkTipsManager:

    def __init__(self, logger = logging.getLogger(__name__)):
        self._logger = logger
        self._tips = []

    # def load_available_tips(self, tips_available_for_parking):
    #     self._tips = tips_available_for_parking
    #     self._logger.info("Park tips initiated with {} tips.".format(len(self._tips)))

    def park_tip(self, pip: InstrumentContext, dest_well):
        self._logger.info("Park requested for pipette {} and well {}".format(pip, dest_well))

        drop_loc = self._get_tip_for_well(dest_well)

        if drop_loc is None:
            drop_loc = pip._last_tip_picked_up_from
            self._logger.info("dest well not found, adding")
            self._tips.append((pip._last_tip_picked_up_from, dest_well))

        self._logger.info("Dropping to {}".format(drop_loc))
        pip.drop_tip(drop_loc)

        self._logger.info("Now tips value is: {}".format(self._tips))

    def _get_tip_for_well(self, well):
        for t, d in self._tips:
            if d == well:
                return t
        else:
            return None

    def reuse_tip(self, pip, dest_well):
        self._logger.info("Reuse tip requested for well {}".format(dest_well))
        tip_loc = self._get_tip_for_well(dest_well)

        assert tip_loc is not None, "Reuse tip requested but no parking present for well {}".format(dest_well)

        self._logger.info("Picking up from {}".format(tip_loc))
        pip.pick_up_tip(tip_loc)

    @property
    def tips(self):
        return self._tips

