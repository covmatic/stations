import logging
from typing import Union
from opentrons.protocol_api import InstrumentContext, PairedInstrumentContext


class ParkTipsException(Exception):
    pass

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
            self._tips.append({"tip": pip._last_tip_picked_up_from,
                               "dest_well": dest_well,
                               "has_tip": False})

        if self._has_tip(drop_loc):
            raise ParkTipsException("Drop place already have tip.")

        self._logger.info("Dropping to {}".format(drop_loc))
        pip.drop_tip(drop_loc)
        self._set_tip_present_from_loc(drop_loc)

        self._logger.info("Now tips value is: {}".format(self._tips))

    def _get_data_for_well(self, well):
        for i, data in enumerate(self._tips):
            if data["dest_well"] == well:
                return self._tips[i]
        else:
            return None

    def _get_data_for_tip(self, tip):
        for i, data in enumerate(self._tips):
            if data["tip"] == tip:
                return self._tips[i]
        else:
            return None

    def _get_tip_for_well(self, well):
        data = self._get_data_for_well(well)
        return data["tip"] if data is not None else None

    def reuse_tip(self, pip, dest_well):
        self._logger.info("Reuse tip requested for well {}".format(dest_well))
        tip_loc = self._get_tip_for_well(dest_well)

        assert tip_loc is not None, "Reuse tip requested but no parking present for well {}".format(dest_well)

        if not self._has_tip(tip_loc):
            raise ParkTipsException("Pickup place does not have tip.")

        self._logger.info("Picking up from {}".format(tip_loc))
        self._set_tip_missing_from_loc(tip_loc)
        pip.pick_up_tip(tip_loc)

    def _set_has_tip(self, data):
        self._logger.info("Setting HAS TIP to {}".format(data))
        data["has_tip"] = True

    def _set_no_tip(self, data):
        self._logger.info("Setting NO TIP to {}".format(data))
        data["has_tip"] = False

    def _has_tip(self, tip):
        data = self._get_data_for_tip(tip)
        return data["has_tip"]

    def _set_tip_present_from_loc(self, drop_loc):
        data = self._get_data_for_tip(drop_loc)
        if data is not None:
            self._set_has_tip(data)
        else:
            raise ParkTipsException("tip not found in list: {}".format(drop_loc))

    def _set_tip_missing_from_loc(self, drop_loc):
        data = self._get_data_for_tip(drop_loc)
        if data is not None:
            self._set_no_tip(data)
        else:
            raise ParkTipsException("tip not found in list: {}".format(drop_loc))

    @property
    def tips(self):
        tips = [data["tip"] for data in self._tips]
        self._logger.info("T is: {}".format(tips))
        return tips

