from opentrons import robot
import os

test = True

if not robot.is_simulating():
    os.system("{} -m pip install --upgrade{} covid19-system9".format(os.sys.executable, " -i https://test.pypi.org/simple/" if test else ""))
