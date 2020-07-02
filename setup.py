import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="covid19-system9",
    version="0.0.0.dev",
    author="Marco Tiraboschi",
    author_email="marcotiraboschi@hotmail.it",
    description="Package for the COVID19 System-9 (Calcinate)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/OpenSourceCovidTesting/covid19-system-9",
    packages=setuptools.find_packages(),
    install_requires=[
        'opentrons',
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)
