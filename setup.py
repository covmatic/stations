import logging
import os
from functools import partial


logging.basicConfig(level=logging.INFO)

# Configuration
source = "./custom_defaults"
dest = os.path.expanduser("~/.opentrons")
logging.info("Installing configuration files in {}".format(dest))


def install():
    if not os.path.isdir(dest):
        os.mkdir(dest)
    for f in filter(os.path.isfile, map(partial(os.path.join, source), os.listdir(source))):
        logging.info("'{}'".format(f))
        os.system("cp '{}' '{}'".format(f, dest))


install()

# Labware
source = "./custom_labware"
dest = os.path.expanduser("~/.opentrons/labware/v2/custom_definitions/")
logging.info("Installing custom labware files in {}".format(dest))
install()
