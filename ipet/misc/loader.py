"""
The MIT License (MIT)

Copyright (c) 2016 Zuse Institute Berlin, www.zib.de

Permissions are granted as stated in the license file you have obtained
with this software. If you find the library useful for your purpose,
please refer to README.md for how to cite IPET.

@author: Franziska Schlösser
"""
from ipet.parsing.Solver import Solver
from ipet.parsing import ReaderManager
import os
import inspect
import sys

def loadAdditionalReaders(filenames = []):
    readers = []
    # TODO Test this
    if filenames == []:
        filenames = os.listdir('./') 
        if readersDirExists():
            filenames = filenames + os.listdir(getReadersDir())
    for _file in filenames:
        if _file.endswith(".xml") or _file.endswith(".ipr"):
            try:
                rm = ReaderManager.fromXMLFile(_file)
                readers.append(_file)
            except:
                pass
    return readers

def loadAdditionalSolvers():
    # TODO Test this
    if solversDirExists():
        sys.path.append(getIpetDir())
        # Shut up eclipse! This works
        import solvers
    
        addsolvers = []
        for name, obj in inspect.getmembers(solvers):
            if inspect.isclass(obj) and issubclass(obj, Solver):
                a = getattr(solvers, obj.__name__)()
                addsolvers.append(a)
        return addsolvers
    else:
        return []
    
def getIpetDir():
    return os.path.expanduser("~/.ipet")

def getReadersDir():
    return os.path.expanduser('~/.ipet/readers')
    
def getSolversDir():
    return os.path.expanduser('~/.ipet/solvers')

def dirExists(path):
    return os.path.isdir(path)

def ipetDirExists():
    return dirExists(getIpetDir())

def solversDirExists():
    return dirExists(getSolversDir())

def readersDirExists():
    return dirExists(getReadersDir())
