import logging
import os
from functools import partial


logging.basicConfig(level=logging.INFO)
source = "./custom_defaults"
dest = os.path.expanduser("~/.opentrons")
logging.info("Installing configuration files in {}".format(dest))
if not os.path.isdir(dest):
    os.mkdir(dest)

for f in filter(os.path.isfile, map(partial(os.path.join, source), os.listdir(source))):
    logging.info(f)
    os.system("cp {} {}".format(f, dest))
