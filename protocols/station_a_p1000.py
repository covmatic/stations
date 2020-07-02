import logging
from system9.a.p1000 import StationAP1000


logging.getLogger(StationAP1000.__name__).setLevel(logging.INFO)
metadata = {'apiLevel': '2.3'}
station = StationAP1000(num_samples=15)
metadata = station.metadata


def run(ctx):
    return station.run(ctx)
