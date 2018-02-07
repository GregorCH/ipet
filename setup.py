#!/usr/bin/env python
"""
The MIT License (MIT)

Copyright (c) 2018 Zuse Institute Berlin, www.zib.de

Permissions are granted as stated in the license file you have obtained
with this software. If you find the library useful for your purpose,
please refer to README.md for how to cite IPET.

@author: Gregor Hendel
"""
from setuptools import setup

with open("ipet/version.py") as f:
    exec(f.read())

try:
    import pypandoc
    long_description = pypandoc.convert('README.md', 'rst')
except(IOError, ImportError):
    long_description = open('README').read()

try:
    from PyQt4.Qt import PYQT_VERSION_STR
    withgui = True
except ImportError:
    withgui = False
    pass


packages = ['ipet', 'ipet.concepts', 'ipet.evaluation', 'ipet.misc', 'ipet.parsing', 'ipet.validation']
if withgui:
    packages.append('ipetgui')

requirementslist = ['requirements.txt']
if withgui:
    requirementslist.append('requirements-gui.txt')

required = []
for r in requirementslist:
    with open(r, 'r') as requirements:
        required.append(requirements.read().splitlines())


kwargs = {
    "name": "ipet",
    "version": str(__version__),
    "packages": ['ipet', 'ipetgui', 'ipet.concepts', 'ipet.evaluation', 'ipet.misc', 'ipet.parsing'],
    "package_data": dict(ipet = ["../images/*.png"]),
    "description": "Interactive Performance Evaluation Tools",
    "long_description": long_description,
    "author": "Gregor Hendel",
    "maintainer": "Gregor Hendel",
    "author_email": "hendel@zib.de",
    "maintainer_email": "hendel@zib.de",
    "install_requires": required,
    "url": "https://github.com/GregorCH/ipet",
    "download_url": "https://github.com/GregorCH/ipet/archive/master.zip",
    "keywords": "Mathematical Optimization solver log benchmark parser",
    "classifiers": [
        "Programming Language :: Python",
        "Topic :: Software Development",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    "scripts": ["scripts/ipet-parse", "scripts/ipet-evaluate", "scripts/ipet-gui"]
}

setup(**kwargs)
