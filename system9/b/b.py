from ..station import Station, labware_loader, instrument_loader
from opentrons.protocol_api import ProtocolContext


_metadata = {
    'protocolName': 'Version 1 S9 Station B BP Purebase (400µl sample input)',
    'author': 'Nick <ndiehl@opentrons.com',
    'apiLevel': '2.3'
}


class StationB(Station):
    def __init__(
        self,
        bind_aspiration_rate: float = 50,
        bind_max_transfer_vol: float = 180,
        default_aspiration_rate: float = 150,
        elute_aspiration_rate: float = 50,
        elution_vol: float = 40,
        metadata: dict = _metadata,
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
        :param metadata: protocol metadata
        :param num_samples: The number of samples that will be loaded on the station B
        :param park: Whether to park or not
        :param skip_delay: If True, pause instead of delay.
        :param supernatant_removal_aspiration_rate: Aspiration flow rate when removing the supernatant in uL/s
        :param starting_vol: Sample volume at start (volume coming from Station A) 
        :param tip_rack: If True, try and load previous tiprack log from the JSON file
        """
        self._bind_aspiration_rate = bind_aspiration_rate
        self._bind_max_transfer_vol = bind_max_transfer_vol
        self._default_aspiration_rate = default_aspiration_rate
        self._elute_aspiration_rate = elute_aspiration_rate
        self._elution_vol = elution_vol
        self.metadata = metadata
        self._num_samples = num_samples
        self._park = park
        self._skip_delay = skip_delay
        self._supernatant_removal_aspiration_rate = supernatant_removal_aspiration_rate
        self._starting_vol = starting_vol
        self._tip_rack = tip_rack


station_b = StationB()
metadata = station_b.metadata
run = station_b.run


if __name__ == "__main__":
    from opentrons import simulate    
    run(simulate.get_protocol_api(metadata["apiLevel"]))
