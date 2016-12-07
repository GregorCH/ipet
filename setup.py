#!/usr/bin/env python
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

    
packages = ['ipet', 'ipet.concepts', 'ipet.evaluation', 'ipet.misc', 'ipet.parsing']
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
    "packages": ['ipet',  'ipetgui', 'ipet.concepts', 'ipet.evaluation', 'ipet.misc', 'ipet.parsing'],
    "package_data": dict(ipet=["../images/*.png"]),
    "description": "Interactive Performance Evaluation Tools",
    "long_description": long_description,
    "author": "Gregor Hendel",
    "maintainer": "Gregor Hendel",
    "author_email": "hendel@zib.de",
    "maintainer_email": "hendel@zib.de",
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
