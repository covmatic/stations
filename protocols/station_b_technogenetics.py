import logging
from system9.b.technogenetics import StationBTechnogenetics


logging.getLogger(StationBTechnogenetics.__name__).setLevel(logging.INFO)
metadata = {'apiLevel': '2.3'}
station = StationBTechnogenetics(num_samples=96)


def run(ctx):
    return station.run(ctx)
