import logging


__version__ = "0.0.4.dev1"


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(name)-12s %(levelname)-8s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logging.getLogger("opentrons").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.WARNING)
