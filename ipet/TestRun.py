"""
The MIT License (MIT)

Copyright (c) 2016 Zuse Institute Berlin, www.zib.de

Permissions are granted as stated in the license file you have obtained
with this software. If you find the library useful for your purpose,
please refer to README.md for how to cite IPET.

@author: Gregor Hendel
"""
from ipet import Key
from ipet import misc
from pandas import DataFrame, notnull
from ipet.parsing import StatisticReader
import os, sys
import logging
import pandas as pd
#from lib2to3.fixes.fix_input import context
#from matplotlib.tests import test_lines

try:
    import pickle as pickle
except:
    import pickle

class TestRun:
    """
    represents the collected data of a particular (set of) log file(s)
    """
    FILE_EXTENSION = ".trn"
    """ the file extension for saving and loading test runs from """

    def __init__(self, filenames = []):
        self.inputfromstdin = False
        self.filenames = []
        for filename in filenames:
            self.appendFilename(filename)
        self.data = DataFrame(dtype = object)

        self.datadict = {}
        self.currentproblemdata = {}
        self.currentproblemid = 0
        """ meta data represent problem-independent data """
        self.metadatadict = {}
        self.parametervalues = {}
        self.defaultparametervalues = {}
        self.keyset = set()
        
        self.currentfileiterator = None
        self.currentfile = None
        self.consumedStdinput = []

    def __iter__(self):
        if(self.currentfile != ""):
            with open(self.currentfile, "r") as f:
                for line in enumerate(f):
                    yield line
        else: 
            for line in enumerate(self.consumedStdinput):
                yield line
            for line in enumerate(sys.stdin, len(self.consumedStdinput)):
                yield line

    def iterationPrepare(self):
        filenames = sorted(self.filenames, key = lambda x:misc.sortingKeyContext(misc.filenameGetContext(x)))
        self.currentfileiterator = iter(filenames)
        
    def iterationNextFile(self):
        try:
            self.currentfile = next(self.currentfileiterator)
            return True
        except StopIteration:
            return False
    
    def iterationAddConsumedStdinput(self, consumedlines):
        if self.currentfile == "":
            for line in consumedlines:
                self.consumedStdinput.append(line)
    
    def iterationCleanUp(self):
        self.currentfileiterator = None
        
    def iterationGetCurrentFile(self):
        return self.currentfile

    def setInputFromStdin(self):
        self.filenames.append("")

    def appendFilename(self, filename):
        # TODO test this
        """Append a file name to the list of filenames of this test run
        """
        filename = os.path.abspath(filename)
        if filename not in self.filenames:
            self.filenames.append(filename)
        else:
            return
        
        extension = misc.filenameGetContext(filename)
        if extension in [Key.CONTEXT_ERRFILE, Key.CONTEXT_LOGFILE]:
            metafile = os.path.splitext(filename)[0]+".meta"

            if os.path.isfile(metafile) and (metafile not in self.filenames):
                self.filenames.append(metafile)
        
    def addDataByName(self, datakeys, data, problem):
        """Add the current data under the specified dataname

        Readers can use this method to add data, either as a single datakey, or as list,
        where in the latter case it is required that datakeys and data are both lists of the same length

        after data was added, the method getProblemDataById() can be used for access
        """
        for problemid, name in self.datadict.setdefault(Key.ProblemName, {}).items():
            if name == problem:
                self.addDataById(datakeys, data, problemid)

    def addData(self, datakey, data):
        """Add data to current problem

        readers can use this method to add data, either as a single datakey, or as list,
        where in the latter case it is required that datakeys and data are both lists of the same length
        """
        logging.debug("TestRun %s receives data Datakey %s, %s" % (self.getName(), repr(datakey), repr(data)))

        if type(datakey) is list and type(data) is list:
            for key, datum in zip(datakey, data):
                self.currentproblemdata[key] = datum
        else:
            self.currentproblemdata[datakey] = data

    def getCurrentProblemData(self, datakey : str = None):
        """Return current problem data, either entirely or for specified data key
        """
        if datakey is None:
            return self.currentproblemdata
        else:
            return self.currentproblemdata.get(datakey)

    def addDataById(self, datakeys, data, problemid):
        """Add the data or to the specified problem

        readers can use this method to add data, either as a single datakey, or as list,
        where in the latter case it is required that datakeys and data are both lists of the same length

        after data was added, the method getProblemDataById() can be used for access if a problemid was given
        """
        # check for the right dictionary to store the data
        logging.debug("TestRun %s receives data Datakey %s, %s to problem %s" % (self.getName(), repr(datakeys), repr(data), problemid))

        if type(datakeys) is list and type(data) is list:
            for key, datum in zip(datakeys, data):
                self.datadict.setdefault(key, {})[problemid] = datum
        else:
            self.datadict.setdefault(datakeys, {})[problemid] = data

    def addParameterValue(self, paramname, paramval):
        """Store the value for a parameter of a given name for this test run
        """
        self.parametervalues[paramname] = paramval

    def addDefaultParameterValue(self, paramname, defaultval):
        """Store the value for a parameter of a given name for this test run
        """
        self.defaultparametervalues[paramname] = defaultval

    def getParameterData(self):
        """Return two dictionaries that map parameter names to  their value and default value
        """
        return (self.parametervalues, self.defaultparametervalues)

    def getLogFile(self, fileextension = ".out"):
        """Returns the name of the logfile
        """
        for filename in self.filenames:
            if filename.endswith(fileextension):
                return filename
        return None

    def getKeySet(self):
        """Return a list or set of keys (which are the columns headers of the data)
        """
        if self.datadict != {}:
            return list(self.datadict.keys())
        else:
            return set(self.data.columns)

    def emptyData(self):
        """Empty all data of current testrun
        """
        self.data = DataFrame(dtype = object)

    def getMetaData(self):
        """Return a data frame containing meta data
        """
        return self.metadatadict

    def finalizeCurrentCollection(self, solver):
        """ Any data of the current problem is saved as a new row in datadict
        """
        if self.currentproblemdata != {}:
            # Add data collected by solver into currentproblemdata, such as primal and dual bound,
            self.addData(*solver.getData())
            for key in self.metadatadict.keys():
                self.addData(key, self.metadatadict[key])

            for key in self.currentproblemdata.keys():
                self.datadict.setdefault(key, {})[self.currentproblemid] = self.currentproblemdata[key]
            self.currentproblemdata = {}
            self.currentproblemid = self.currentproblemid + 1

    def finishedReadingFile(self, solver):
        """ Save data of current problem
        """
        self.finalizeCurrentCollection(solver)

    def setupForDataCollection(self):
        """ Save data in a python dictionary for easier data collection
        """
        self.datadict = self.data.to_dict()
        self.data = DataFrame(dtype = object)

    def setupAfterDataCollection(self):
        """ Save data in a pandas dataframe for futher use (i.e. reading and finding data)
        """
        self.data = DataFrame(self.datadict)
        self.datadict = {}

    def hasProblemName(self, problemname):
        """ Return if already collected data for a problem with given name
        """
        if self.datadict != {}:
            return problemname in self.datadict.get(Key.ProblemName, {}).values()
        else:
            if Key.ProblemName in self.data.keys():
                for name in self.data[Key.ProblemName]:
                    if problemname == name:
                        return True
            return False

    def hasProblemId(self, problemid):
        """ Returns if there is already data collected for a problem with given id
        """
        return problemid in range(self.currentproblemid)

    def getProblemIds(self):
        """ Return a list of problemids
        """
        return list(range(self.currentproblemid))

    def getProblemNames(self):
        """ Return an (unsorted) list of problemnames
        """
        if self.datadict != {}:
            return list(self.datadict.get(Key.ProblemName, []))
        else:
            if Key.ProblemName in self.data.columns:
                return list(self.data[Key.ProblemName])
            else:
                return []

    def getProblemDataByName(self, problemname, datakey):
        """Return the data collected for problems with given name
        """
        collecteddata = []
        if self.datadict != {}:
            for key, dat in self.datadict.get("ProblemName", None):
                if dat == problemname:
                    collecteddata.append(self.getProblemDataById(key, datakey))
        else:
            collecteddata = list(self.data[self.data[Key.ProblemName] == problemname].loc[:, datakey])
        try:
            return collecteddata[0]
        except IndexError:
            return None

    def getProblemDataById(self, problemid, datakey = None):
        """Return data for a specific datakey, or None, if no such data exists for this (probname, datakey) key pair
        """
        if datakey is None:
            try:
                return ",".join("%s: %s" % (key, self.getProblemDataById(problemid, key)) for key in self.getKeySet())
            except KeyError:
                return "<%s> not contained in keys, have only\n%s" % \
                    (problemid, ",".join((ind for ind in self.getProblemIds())))
        else:
            if self.datadict != {}:
                return self.datadict.get(datakey, {}).get(problemid, None)
            else:
                try:
                    data = self.data.loc[problemid, datakey]
                except KeyError:
                    data = None
                if type(data) is list or notnull(data):
                    return data
                else:
                    return None

    def getProblemsDataById(self, problemids, datakey):
        """ Return data for a list of problems
        """
        if self.datadict != {}:
            return [self.datadict.get(datakey, {}).get(id, None) for id in problemids]
        else:
            return self.data.loc[problemids, datakey]

    def deleteProblemDataById(self, problemid):
        """ Delete all data acquired so far for problemid
        """
        if self.datadict != {}:
            for key in list(self.datadict.keys()):
                try:
                    del self.datadict[key][problemid]
                except KeyError:
                    pass
        else:
            try:
                self.data.drop(problemid, inplace = True)
            except TypeError:
                # needs to be caught for pandas version < 0.13
                self.data = self.data.drop(problemid)

    def saveToFile(self, filename):
        """ Dump the pickled instance of itself into a .trn-file
        """
        try:
            f = open(filename, 'wb')
            pickle.dump(self, f, protocol = 2)
            f.close()
        except IOError:
            print("Could not open %s for saving test run" % filename)

    def emptyCurrentProblemData(self):
        """ Empty data of currently read problem
        """
        return self.currentproblemdata == {}

    def printToConsole(self, formatstr = "{idx}: {d}"):
        """ Print data to console
        """
        for idx, d in self.data.iterrows():
#            pd.set_option('display.max_rows', len(d))
            print(formatstr.format(d = d, idx = idx))
#            pd.reset_option('display.max_rows')

    def toJson(self):
        """ Return the data-object in json
        """
        return self.data.to_json()

    @staticmethod
    def loadFromFile(filename):
        """ Loads a .trn-File containing a particular instance of TestRun
        """
        try:
            if filename.endswith(".gz"):
                import gzip
                f = gzip.open(filename, 'rb')
            else:
                f = open(filename, 'rb')
        except IOError:
            print("Could not open %s for loading test run" % filename)
            return None
        testrun = pickle.load(f)
        f.close()
        return testrun

    def getData(self, datakey = None):
        """Return a data frame object of the acquired data
        """
        return self.data
            
    def getCurrentLogfilename(self):
        """ Return the name of the current logfile 
        """
        return os.path.basename(self.filenames[0])

    def getSettings(self):
        """ Return the settings associated with this test run
        """
        try:
            return self.data['Settings'][0]
        except KeyError:
            return os.path.basename(self.filenames[0]).split('.')[-2]
#
    def getName(self):
        """ Convenience method to make test run a manageable object
        """
        return self.getIdentification()

    def getIdentification(self):
        """ Return identification string of this test run
        """
        # TODO Is this still the way to do this? What if we are reading from stdin?
        return os.path.splitext(os.path.basename(self.filenames[0]))[0]
    
    def problemGetOptimalSolution(self, problemid):
        """ Return objective of an optimal or a best known solution

        ... from solu file, or None, if no such data has been acquired
        """
        try:
            return self.getProblemDataById(problemid, 'OptVal')
        except KeyError:
#            print(self.getIdentification() + " has no solu file value for ", problemid)
            return None

    def problemGetSoluFileStatus(self, problemid):
        """ Return 'unkn', 'inf', 'best', 'opt'

        ... as solu file status, or None, if no solu file status
        exists for this problem
        """
        try:
            return self.getProblemDataById(problemid, 'SoluFileStatus')
        except KeyError:
#            print(self.getIdentification() + " has no solu file status for ", problemid)
            return None

