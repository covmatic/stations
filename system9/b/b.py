from ..station import Station, labware_loader, instrument_loader
from opentrons.protocol_api import ProtocolContext
from typing import Optional
import logging


class StationB(Station):
    _protocol_description = "station B protocol"
    
    def __init__(
        self,
        bind_aspiration_rate: float = 50,
        bind_max_transfer_vol: float = 180,
        default_aspiration_rate: float = 150,
        elute_aspiration_rate: float = 50,
        elution_vol: float = 40,
        jupyter: bool = True,
        logger: Optional[logging.getLoggerClass()] = None,
        metadata: Optional[dict] = None,
        num_samples: int = 96,
        park: bool = True,
        skip_delay: bool = False,
        supernatant_removal_aspiration_rate: float = 25,
        starting_vol: float = 380,
        tip_rack: bool = False,
    ):
        """ Build a :py:class:`.StationB`.
        :param bind_aspiration_rate: Aspiration flow rate when aspirating bind beads in uL/s
        :param bind_max_transfer_vol: Maximum volume transferred of bind beads
        :param default_aspiration_rate: Default aspiration flow rate in uL/s
        :param elute_aspiration_rate: Aspiration flow rate when aspirating elution buffer in uL/s
        :param elution_vol: The volume of elution buffer to aspirate in uL
        :param logger: logger object. If not specified, the default logger is used that logs through the ProtocolContext comment method
        :param metadata: protocol metadata
        :param num_samples: The number of samples that will be loaded on the station B
        :param park: Whether to park or not
        :param skip_delay: If True, pause instead of delay.
        :param supernatant_removal_aspiration_rate: Aspiration flow rate when removing the supernatant in uL/s
        :param starting_vol: Sample volume at start (volume coming from Station A) 
        :param tip_rack: If True, try and load previous tiprack log from the JSON file
        """
        super(StationB, self).__init__(
            jupyter=jupyter,
            logger=logger,
            metadata=metadata,
        )
        self._bind_aspiration_rate = bind_aspiration_rate
        self._bind_max_transfer_vol = bind_max_transfer_vol
        self._default_aspiration_rate = default_aspiration_rate
        self._elute_aspiration_rate = elute_aspiration_rate
        self._elution_vol = elution_vol
        self._num_samples = num_samples
        self._park = park
        self._skip_delay = skip_delay
        self._supernatant_removal_aspiration_rate = supernatant_removal_aspiration_rate
        self._starting_vol = starting_vol
        self._tip_rack = tip_rack
    
    def delay(self, mins: float, msg: str):
        msg = "{} for {} minutes".format(msg, mins)
        if self._skip_delay:
            self.logger.info("{}. Pausing for skipping delay. Please resume".format(msg))
            self._ctx.pause()
        else:
            self.logger.info(msg)
            self._ctx.delay(minutes=mins)
    
    def run(self, ctx: ProtocolContext):
        super(StationB, self).run(ctx)


if __name__ == "__main__":
    StationB(metadata={'apiLevel': '2.3'}).simulate()
