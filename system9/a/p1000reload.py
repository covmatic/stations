from .a_reload import StationAReload
from .p1000 import StationAP1000


class StationAP1000Reload(StationAReload, StationAP1000):
    _protocol_description = "station A protocol for COPAN 330C refillable samples."


station_a = StationAP1000Reload(num_samples=96)
metadata = station_a.metadata
run = station_a.run


if __name__ == "__main__":
    from opentrons import simulate  
    station_a.jupyter = True
    run(simulate.get_protocol_api(metadata["apiLevel"]))
