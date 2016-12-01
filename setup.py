#!/usr/bin/env python
from setuptools import setup

with open("ipet/version.py") as f:
    exec(f.read())

try:
    import pypandoc
    long_description = pypandoc.convert('README.md', 'rst')
except(IOError, ImportError):
    long_description = open('README').read()

with open('requirements.txt') as requirements:
    required = requirements.read().splitlines()

kwargs = {
    "name": "ipet",
    "version": str(__version__),
    "packages": ['ipet', 'ipet.concepts', 'ipet.evaluation', 'ipet.gui', 'ipet.misc', 'ipet.parsing', 'qipet'],
    "package_data": dict(ipet=["../images/*.png"]),
    "description": "Interactive Python Evaluation Tools Reader",
    "long_description": long_description,
    "author": "Zuse Institute Berlin",
    "maintainer": "Zuse Institute Berlin",
    "author_email": "lpip-developers@zib.de",
    "maintainer_email": "lpip-developers@zib.de",
    "install_requires": required,
    "url": "https://git.zib.de/integer/ipet",
    "download_url": "https://git.zib.de/integer/ipet/repository/archive.tar.gz?ref={}".format(__version__),
    "keywords": "solver log benchmark parser",
    "classifiers": [
        "Programming Language :: Python",
        "Topic :: Software Development",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ]
}

setup(**kwargs)
