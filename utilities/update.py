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
    os.system("{} -m pip install --upgrade cherrypy typing-extensions requests".format(os.sys.executable))
    os.system("{} -m pip install --upgrade{} covid19-system9".format(os.sys.executable, " -i https://test.pypi.org/simple/" if test else ""))

robot.comment("restart your OT-2 to apply the changes")


# Copyright (c) 2020 Covmatic.
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
