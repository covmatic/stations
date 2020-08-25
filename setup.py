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
    name="covid19-system9",
    version=get_version("system9/__init__.py"),
    author="Marco Tiraboschi",
    author_email="marcotiraboschi@hotmail.it",
    description="Package for the COVID19 System-9 (Calcinate)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/OpenSourceCovidTesting/covid19-system-9",
    packages=setuptools.find_packages(),
    include_package_data=True,
    install_requires=[
        'opentrons',
        'cherrypy',
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)
