import logging
from system9.a.p1000reload import StationAP1000Reload


logging.getLogger(StationAP1000Reload.__name__).setLevel(logging.INFO)
metadata = {'apiLevel': '2.3'}
station = StationAP1000Reload(num_samples=96)


def run(ctx):
    return station.run(ctx)
