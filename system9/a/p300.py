from .a import StationA


class StationAP300(StationA):
    _protocol_description: str = "station A protocol for BPGenomics samples."


station_a = StationAP300()
metadata = station_a.metadata
run = station_a.run


if __name__ == "__main__":
    from opentrons import simulate    
    run(simulate.get_protocol_api(metadata["apiLevel"]))
