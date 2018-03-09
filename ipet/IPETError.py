"""
The MIT License (MIT)

Copyright (c) 2018 Zuse Institute Berlin, www.zib.de

Permissions are granted as stated in the license file you have obtained
with this software. If you find the library useful for your purpose,
please refer to README.md for how to cite IPET.

@author: Gregor Hendel
@author: Franziska Schlösser
"""


class IPETInconsistencyError(BaseException):

    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return repr(self.msg)
