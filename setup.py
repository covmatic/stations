import setuptools
import codecs
import os.path


with open("README.md", "r") as fh:
    long_description = fh.read()


def read(rel_path):
    here = os.path.abspath(os.path.dirname(__file__))
    with codecs.open(os.path.join(here, rel_path), 'r') as fp:
        return fp.read()


def get_version(rel_path):
    for line in read(rel_path).splitlines():
        if line.startswith('__version__'):
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]
    else:
        raise RuntimeError("Unable to find version string.")


setuptools.setup(
    name="covmatic-stations",
    version=get_version("covmatic_stations/__init__.py"),
    author="Marco Tiraboschi",
    author_email="marco.tiraboschi@unimi.it",
    maintainer="Marco Tiraboschi, Agostino Facotti, Giada Facoetti",
    maintainer_email="marco.tiraboschi@unimi.it, agostino.facotti@gmail.com, giada.facoetti@hotmail.it",
    description="Package for the COVMATIC Opentrons stations",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/covmatic/stations",
    packages=setuptools.find_packages(),
    include_package_data=True,
    setup_requires=[
        'opentrons',
        'wheel',
    ],
    install_requires=[
        'opentrons',
        'cherrypy',
        'requests>=2.26.0',
        'ipaddress',
        'typing-extensions',
        'parse'
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7, <3.9',
)


# Copyright (c) 2020 Covmatic.
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
