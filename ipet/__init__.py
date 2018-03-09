# -*- coding: utf-8 -*-
"""
The MIT License (MIT)

Copyright (c) 2018 Zuse Institute Berlin, www.zib.de

Permissions are granted as stated in the license file you have obtained
with this software. If you find the library useful for your purpose,
please refer to README.md for how to cite IPET.

@author: Gregor Hendel
"""
from .Experiment import Experiment
from .TestRun import TestRun
from .version import __version__
from .IPETError import IPETInconsistencyError

__all__ = [ "concepts",
            "evaluation",
            "misc",
            "parsing",
            "validation"
]
