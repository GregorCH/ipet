'''
The MIT License (MIT)

Copyright (c) 2016 Zuse Institute Berlin, www.zib.de

Permissions are granted as stated in the license file you have obtained
with this software. If you find the library useful for your purpose,
please refer to README.md for how to cite IPET.

@author: Gregor Hendel
'''
import ipet.misc as misc
from pandas import DataFrame, notnull
import os
import logging
import json, numpy
from pandas.core.common import indent

try:
    import pickle as pickle
except:
    import pickle

class TestRun:
    '''
    represents the collected data of a particular (set of) log file(s)
    '''
    FILE_EXTENSION = ".trn"
    """ the file extension for saving and loading test runs from """

    def __init__(self, filenames=[]):
        self.inputfromstdin = False
        self.filenames = []
        for filename in filenames:
            self.appendFilename(filename)
        self.data = DataFrame(dtype=object)

        self.datadict = {}
        self.currentinstancedataseries = {}
        self.currentinstanceid = 0
        # FARI1 Do we want to keep this?
        self.instanceset = set()
        # FARI1 Do we still need these?
        self.metadatadict = {}
        """ meta data represent instance-independent data """
        self.parametervalues = {}
        self.defaultparametervalues = {}
        # FARI1 Where and why do we use keyset?
        self.keyset = set()

    def setInputFromStdin(self):
        self.inputfromstdin = True
        self.filenames = [""]

    def appendFilename(self, filename):
        '''
        appends a file name to the list of filenames of this test run
        '''
        filename = os.path.abspath(filename)
        if filename not in self.filenames:
            self.filenames.append(filename)

    #def addData(self, problemid, datakeys, data):
    def addData(self, datakeys, data):
        '''
        add data to problem data under the specified key(s)

        add the current data - readers can use this method to add data, either as a single datakey, or as list,
        where in the latter case it is required that datakeys and data are both lists of the same length

        after data was added, the method problemGetData() can be used for access
        '''

        # check for the right dictionary to store the data
        # FARI1 The following is a pointer or a copy into local variable datadict? -> pointer
        # datadict = self.datadict if probname is not None else self.metadatadict
        # datadict = self.datadict if problemid is not None else self.metadatadict
        
        # FARI2 problemid is not a very sensible info, how to change this for the better?
        logging.debug("TestRun %s receives data Datakey %s, %s to prob" % (self.getName(), repr(datakeys), repr(data)))

        #if problemid not in self.instanceset:
        #    self.instanceset.add(problemid)

        if type(datakeys) is list and type(data) is list:
            for key, datum in zip(datakeys, data):
                #col = datadict.setdefault(key, {})
                #col[problemid] = datum
                self.currentinstancedataseries[key] = datum
        else:
            # col = datadict.setdefault(datakeys, {})
            # col[problemid] = data
            self.currentinstancedataseries[datakeys] = data

    def addParameterValue(self, paramname, paramval):
        '''
        stores the value for a parameter of a given name for this test run
        '''
        self.parametervalues[paramname] = paramval

    def addDefaultParameterValue(self, paramname, defaultval):
        '''
        stores the value for a parameter of a given name for this test run
        '''
        self.defaultparametervalues[paramname] = defaultval

    def getParameterData(self):
        '''
        returns two dictionaries that map parameter names to  their value and default value
        '''
        return (self.parametervalues, self.defaultparametervalues)

    def getLogFile(self, fileextension=".out"):
        for filename in self.filenames:
            if filename.endswith(fileextension):
                return filename
        return None
    
    def getKeySet(self):
        if self.datadict != {}:
            return list(self.datadict.keys())
        else:
            return set(self.data.columns)

    def problemGetData(self, problem, datakey):
        '''
        returns data for a specific datakey, or None, if no such data exists for this (probname, datakey) key pair
        '''
        if not type(problem) is int:
            # FARIDO convert from name to id
            print("FARIFIXME")
        if self.datadict != {}:
            return self.datadict.get(datakey, {}).get(problem, None)
        else:
            try:
                data = self.data.loc[problem, datakey]
            except KeyError:
                data = None
            if type(data) is list or notnull(data):
                return data
            else:
                return None

    def emptyData(self):
        self.data = DataFrame(dtype=object)

    def getData(self):
        """
        returns a data frame object of the acquired data
        """
        return self.data

    def getMetaData(self):
        """
        returns a data frame containing meta data
        """
        return DataFrame(self.metadatadict)

    def initializeNextInstanceCollection(self):
        self.currentinstanceid = self.currentinstanceid + 1

    def finalizeInstanceCollection(self):
        # FARI1 Does this possibly need to be transposed?
        if self.currentinstancedataseries != {}:
            for key in self.currentinstancedataseries.keys():
                self.datadict.setdefault(key, {})[self.currentinstanceid] = self.currentinstancedataseries[key]
            # FARI1 Do we need to clean up after ourselves?
            self.currentinstancedataseries = {} 

    def finishedReadingFile(self):
        self.finalizeInstanceCollection()
        
    def setupForDataCollection(self):
        self.datadict = self.data.to_dict()
        self.data = DataFrame(dtype=object)
        
    # FARI2 rename to setupAfterDataCollection?
    def finalize(self):
        self.data = DataFrame(self.datadict)
        self.datadict = {}

    def hasInstance(self, instancename):
        return instancename in self.instanceset

    def getProblems(self):
        '''
        returns an (unsorted) list of problems
        '''
        if self.datadict != {}:
            return list(self.instanceset)
        else:
            return list(self.data.index.get_values())

    def problemlistGetData(self, problemlist, datakey):
        '''
        returns data for a list of problems
        '''
        if self.datadict != {}:
            # FARIDO Does this still work this way?
            return [self.datadict.get(datakey, {}).get(problemid, None) for problemid in problemlist]
        else:
            # FARIDO Does this still work this way?
            return self.data.loc[problemlist, datakey]

    def deleteProblemData(self, problemid):
        '''
        deletes all data acquired so far for problemid
        '''
        if self.datadict != {}:
            for col in list(self.datadict.keys()):
                try:
                    del self.datadict[col][problemid]
                except KeyError:
                    pass
        else:
            # FARI1 Why 'else'? -> because either data or datadict is empty?
            try:
                self.data.drop(problemid, inplace=True)
            except TypeError:
                # needs to be caught for pandas version < 0.13
                self.data = self.data.drop(problemid)

    def getSettings(self):
        '''
        returns the settings associated with this test run
        '''
        try:
            return self.data['Settings'][0]
        except KeyError:
            # FARI1 wouldn't it be nice to save these somewhere? 
            # FARI this is a problem when we are reading from stdin
            return os.path.basename(self.filenames[0]).split('.')[-2]

    def getVersion(self):
        '''
        returns the version associated with this test run
        '''
        try:
            return self.data['Version'][0]
        except KeyError:
            # FARI1 wouldn't it be nice to save these somewhere?
            # FARI this is a problem when we are reading from stdin
            return os.path.basename(self.filenames[0]).split('.')[3]

    def saveToFile(self, filename):
        try:
            f = open(filename, 'wb')
            pickle.dump(self, f, protocol=2)
            f.close()
        except IOError:
            print("Could not open %s for saving test run" % filename)

    def printToConsole(self):
        #print("DATA ", self.data)
        #print("DATADICT ", self.datadict)
        #print("CURRENTSERIES ", self.currentinstancedataseries)
        #print("DATA INDEX", self.data.index.values)
        #print("DATA COLUMNS", self.data.columns.values)
        print(self.data.iloc[0,:])
        
    def toJson(self):
        # FARI2 do we still need this?
        return self.data.to_json()
        #return json.dumps(self.data.to_dict(), sort_keys=True, indent=4)
        
    @staticmethod
    def loadFromFile(filename):
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

    def getLpSolver(self):
        '''
        returns the LP solver used for this test run
        '''
        try:
            return self.data['LPSolver'][0]
        except KeyError:
            return os.path.basename(self.filenames[0]).split('.')[-4]

    def getSolver(self):
        '''
        returns the LP solver used for this test run
        '''
        try:
            return self.data['Solver'][0] + self.data['GitHash'][0]
        except KeyError:
            return os.path.basename(self.filenames[0]).split('.')[2]

    def getMode(self):
        "get mode (optimized or debug)"
        try:
            return self.data['mode'][0]
        except:
            return os.path.basename(self.filenames[0]).split('.')[-5]

    def getName(self):
        '''
        convenience method to make test run a manageable object
        '''
        return self.getIdentification()
    
    # FARI1 Do we want to refer to the problems by name (better by id?)
    def getProbData(self, problemid):
        try:
            return ",".join("%s: %s"%(key,self.problemGetData(problemid, key)) for key in self.getKeySet())
        except KeyError:
            # FARIDO more sensible output?
            return "<%s> not contained in keys, have only\n%s"%(problemid, ",".join((ind for ind in self.getProblems())))

    def getIdentification(self):
        '''
        return identification string of this test run
        '''
        # FARI1 Is this still the way to do this?
        return os.path.splitext(os.path.basename(self.filenames[0]))[0]

    def getShortIdentification(self, char='_', maxlength= -1):
        '''
        returns a short identification which only includes the settings of this test run
        '''
        return misc.cutString(self.getSettings(), char, maxlength)

    def problemGetOptimalSolution(self, solufileprobname):
        '''
        returns objective of an optimal or a best known solution from solu file, or None, if
        no such data has been acquired
        '''
        try:
            return self.problemGetData(solufileprobname, 'OptVal')
        except KeyError:
            print(self.getIdentification() + " has no solu file value for ", solufileprobname)
            return None

    def problemGetSoluFileStatus(self, solufileprobname):
        '''
        returns 'unkn', 'inf', 'best', 'opt' as solu file status, or None, if no solu file status
        exists for this instance
        '''
        try:
            return self.problemGetData(solufileprobname, 'SoluFileStatus')
        except KeyError:
            print(self.getIdentification() + " has no solu file status for ", solufileprobname)
            return None
        
