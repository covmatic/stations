from opentrons import robot
import os

update_in_simulation = False
test = True

try:
    import system9
except ModuleNotFoundError:
    robot.comment("covid19-system9 is not currently installed")
else:
    robot.comment("currently using covid19-system9 version {}".format(system9.__version__))

if not robot.is_simulating() or update_in_simulation:
    os.system("{} -m pip install --upgrade{} covid19-system9".format(os.sys.executable, " -i https://test.pypi.org/simple/" if test else ""))

robot.comment("restart your OT-2 to apply the changes")
