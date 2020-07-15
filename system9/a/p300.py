from .a import StationA


class StationAP300(StationA):
    _protocol_description: str = "station A protocol for BPGenomics samples."


if __name__ == "__main__":
    StationAP300(metadata={'apiLevel': '2.3'}).simulate()
