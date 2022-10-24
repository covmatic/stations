""" Reagent class
    A simple class that should help in reagent use managing liquid parameters (aspirate and dispense speed),
    available volume, refill request
"""
from opentrons.protocol_api.labware import Well
import logging

from covmatic_stations.multi_tube_source import MultiTubeSource

class Reagent:

    # ALLOWED_PIPETTE_PARAMS = ["aspirate_rate", "dispense_rate", "blow_out_rate", "touch_tip"]

    def __init__(self,
                 name: str,
                 volume_overhead: float = 0.05,
                 logger: logging.Logger = logging.getLogger(__name__),
                 **pipette_params
                 ):
        """ Initialize reagent
            @parameter name: name of the reagent
            @parameter volume_overhead: volume percentage present as overhead; it will not be aspirated.
        """
        self._name = name
        self._volume_overhead = volume_overhead
        self._logger = logger
        self._logger.info("Initializing reagent {} with overhead {}".format(self._name, self._volume_overhead))
        self._tubes = MultiTubeSource(name=self._name)
        self._pipette_params = pipette_params
        self._logger.info("Received parameters: {}".format(self._pipette_params))

    def add_well(self, well: Well, volume: float):
        self._logger.info("Received well {} volume {}".format(well, volume))
        assert type(well) != list, "List passed to well argument. You should pass single wells instead"

        self._logger.info("Adding well {} with {}ul to reagent {}".format(well, volume, self._name))
        self._tubes.append_tube_with_vol(well, volume)
        self._logger.info("Now reagent {} contains {}ul in {}".format(self._name, self._tubes.total_vol, self._tubes.locations_str))

    def set_pipette_params(self, **params):
        self._logger.info("Setting parameters: {}".format(params))

