#!/usr/bin/env python

from os.path import exists
from setuptools import setup


setup(
    name="marvin",
    version="0.0.1",
    description="marvin",
    url="https://github.com/prefecthq/marvin",
    maintainer="Chris White",
    maintainer_email="chris@prefect.io",
    packages=["marvin"],
    install_requires=list(open("requirements.txt").read().strip().split("\n")),
    entry_points={"console_scripts": ["marvin=marvin.marvin:run"]},
    zip_safe=False,
)
