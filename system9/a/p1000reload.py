from .a_reload import StationAReload
from .p1000 import StationAP1000


class StationAP1000Reload(StationAReload, StationAP1000):
    _protocol_description = "station A protocol for COPAN 330C refillable samples."


if __name__ == "__main__":
    StationAP1000Reload(num_samples=96, metadata={'apiLevel': '2.3'}).simulate()
