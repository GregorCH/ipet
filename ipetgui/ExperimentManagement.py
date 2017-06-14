"""
The MIT License (MIT)

Copyright (c) 2016 Zuse Institute Berlin, www.zib.de

Permissions are granted as stated in the license file you have obtained
with this software. If you find the library useful for your purpose,
please refer to README.md for how to cite IPET.

@author: Gregor Hendel
"""
from ipet import Experiment

_experiment = None

def resetExperiment():
    global _experiment
    _experiment = Experiment()
    
def setExperiment(experiment):
    global _experiment
    _experiment = experiment

def getExperiment():
    if _experiment is None:
        resetExperiment()
    return _experiment

def addReaders(readermanager):
    for reader in readermanager.getManageables():
        try:
            _experiment.readermanager.registerReader(reader)
        except:
            pass
        
def addOutputFiles(outputfiles):
    for outputfile in outputfiles:
        getExperiment().addOutputFile(outputfile)

if __name__ == "__main__":
    
    getExperiment().addOutputFile("../test/check.short.scip-3.1.0.1.linux.x86_64.gnu.dbg.spx.opt85.testmode.out")
    getExperiment().collectData()