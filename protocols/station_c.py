import logging
from system9.c.c import StationC


logging.getLogger(StationC.__name__).setLevel(logging.INFO)
metadata = {'apiLevel': '2.3'}
station = StationC(num_samples=96*5)


def run(ctx):
    return station.run(ctx)
