'''
Created on 23.09.2016

@author: bzfhende
'''
from ipet import Experiment

experiment = Experiment()

def resetExperiment():
    global experiment
    experiment = Experiment()

def getExperiment():
    if experiment is None:
        resetExperiment()
    return experiment

def addReaders(readermanager):
    for reader in readermanager.getManageables():
        try:
            experiment.readermanager.registerReader(reader)
        except:
            pass
        
def addOutputFiles(outputfiles):
    for outputfile in outputfiles:
        experiment.addOutputFile(outputfile)

