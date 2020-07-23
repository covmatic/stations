import logging
from system9.b.b import StationB


logging.getLogger(StationB.__name__).setLevel(logging.INFO)
metadata = {'apiLevel': '2.3'}
station = StationB(num_samples=96)


def run(ctx):
    return station.run(ctx)
