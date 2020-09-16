import logging
from system9.a.technogenetics import StationATechnogenetics24


logging.getLogger(StationATechnogenetics24.__name__).setLevel(logging.INFO)
metadata = {'apiLevel': '2.3'}
station = StationATechnogenetics24(num_samples=96)


def run(ctx):
    return station.run(ctx)
