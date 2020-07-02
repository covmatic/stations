import logging
from system9.a.p300 import StationAP300


logging.getLogger(StationAP300.__name__).setLevel(logging.INFO)
metadata = {'apiLevel': '2.3'}
station = StationAP300(num_samples=96)
metadata = station.metadata


def run(ctx):
    return station.run(ctx)
