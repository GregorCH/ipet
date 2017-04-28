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
import pandas as pd
import os
import logging
from ipet.Experiment import Experiment

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
        self.metadatadict = {}
        """ meta data represent instance-independent data """
        self.parametervalues = {}
        self.defaultparametervalues = {}
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

    def addDataByName(self, datakeys, data, problem):
        for problemkey, name in self.datadict.setdefault('Problemname', None):
            if name == problem: 
                if type(datakeys) is list and type(data) is list:
                    for key, datum in zip(datakeys, data):
                        self.datadict.setdefault(key, {})[problemkey] = datum
                    else:
                        self.datadict.setdefault(datakeys, {})[problemkey] = data

    def addData(self, datakeys, data, problem=None):
        '''
        add data to problem data under the specified key(s)

        add the current data - readers can use this method to add data, either as a single datakey, or as list,
        where in the latter case it is required that datakeys and data are both lists of the same length

        after data was added, the method problemGetDataById() can be used for access
        '''
        # check for the right dictionary to store the data
        logging.debug("TestRun %s receives data Datakey %s, %s to prob" % (self.getName(), repr(datakeys), repr(data)))

        if problem == None:
            if type(datakeys) is list and type(data) is list:
                for key, datum in zip(datakeys, data):
                    self.currentinstancedataseries[key] = datum
            else:
                self.currentinstancedataseries[datakeys] = data
        else: 
            if type(datakeys) is list and type(data) is list:
                for key, datum in zip(datakeys, data):
                    self.datadict.setdefault(key,{})[problem] = datum
            else:
                self.datadict.setdefault(datakeys, {})[problem] = data

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

    def problemGetDataByName(self, problemname, datakey):
        for key, dat in self.datadict.get("Problemname", None):
            if dat == problemname:
                # FARI1 Is the name unique? What if it is not? Return list?
                return self.problemGetDataById(key, datakey)
        return None

    def problemGetDataById(self, problemid, datakey):
        '''
        returns data for a specific datakey, or None, if no such data exists for this (probname, datakey) key pair
        '''
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

    def emptyData(self):
        self.data = DataFrame(dtype=object)

    def getData(self):
        """
        Return a data frame object of the acquired data
        """
        return self.data

    def getMetaData(self):
        """
        Return a data frame containing meta data
        """
        return DataFrame(self.metadatadict)

    def finalizeInstanceCollection(self, solver):
        if self.currentinstancedataseries != {}:
            # Add data collected by solver into currentinstancedataseries, such as primal and dual bound, 
            self.addData(solver.getKeys(), solver.getData())
            
            for key in self.currentinstancedataseries.keys():
                self.datadict.setdefault(key, {})[self.currentinstanceid] = self.currentinstancedataseries[key]
            self.currentinstancedataseries = {} 
            self.currentinstanceid = self.currentinstanceid + 1
            
        
    def finishedReadingFile(self):
        self.finalizeInstanceCollection()
        
    def setupForDataCollection(self):
        self.datadict = self.data.to_dict()
        self.data = DataFrame(dtype=object)
        
    def setupAfterDataCollection(self):
        self.data = DataFrame(self.datadict)
        self.datadict = {}

    def hasInstance(self, problemid):
        return problemid in range(self.currentinstanceid)

    def getProblems(self):
        '''
        returns an (unsorted) list of problems
        '''
        return list(range(self.currentinstanceid))
        #if self.datadict != {}:
        #    return list(range(self.currentinstanceid))
        #else:
        #    return list(self.data.index.get_values())

    def problemlistGetData(self, problemlist, datakey):
        '''
        returns data for a list of problems
        '''
        if self.datadict != {}:
            return [self.datadict.get(datakey, {}).get(problemid, None) for problemid in problemlist]
        else:
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
            # FARI1 this is a problem when we are reading from stdin
            return os.path.basename(self.filenames[0]).split('.')[-2]

    def getVersion(self):
        '''
        returns the version associated with this test run
        '''
        try:
            return self.data['Version'][0]
        except KeyError:
            # FARI1 this is a problem when we are reading from stdin
            return os.path.basename(self.filenames[0]).split('.')[3]

    def saveToFile(self, filename):
        try:
            f = open(filename, 'wb')
            pickle.dump(self, f, protocol=2)
            f.close()
        except IOError:
            print("Could not open %s for saving test run" % filename)

    def instanceDataEmpty(self):
        return self.currentinstancedataseries == {}

    def printToConsole(self):
        #pd.set_option('display.max_rows', len(self.data.iloc[0,:]))
        
        #print("DATA ", self.data)
        #print("DATADICT ", self.datadict)
        #print("CURRENTSERIES ", self.currentinstancedataseries)
        #print("DATA INDEX", self.data.index.values)
        #print("DATA COLUMNS", self.data.columns.values)
        #print(self.data.iloc[:,:])
        print(self.data.iloc[0,:])
        
        #pd.reset_option('display.max_rows')
        pass
        
    def toJson(self):
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
    
    def problemGetData(self, problemid):
        try:
            return ",".join("%s: %s"%(key,self.problemGetDataById(problemid, key)) for key in self.getKeySet())
        except KeyError:
            return "<%s> not contained in keys, have only\n%s"%(problemid, ",".join((ind for ind in self.getProblems())))

    def getIdentification(self):
        '''
        return identification string of this test run
        '''
        # FARI1 Is this still the way to do this? What if we are reading from stdin?
        return os.path.splitext(os.path.basename(self.filenames[0]))[0]

    def getShortIdentification(self, char='_', maxlength= -1):
        '''
        returns a short identification which only includes the settings of this test run
        '''
        return misc.cutString(self.getSettings(), char, maxlength)

    def problemGetOptimalSolution(self, problemid):
        '''
        returns objective of an optimal or a best known solution from solu file, or None, if
        no such data has been acquired
        '''
        try:
            return self.problemGetDataById(problemid, 'OptVal')
        except KeyError:
            print(self.getIdentification() + " has no solu file value for ", problemid)
            return None

    def problemGetSoluFileStatus(self, problemid):
        '''  
        returns 'unkn', 'inf', 'best', 'opt' as solu file status, or None, if no solu file status
        exists for this instance
        '''
        try:
            return self.problemGetDataById(problemid, 'SoluFileStatus')
        except KeyError:
            print(self.getIdentification() + " has no solu file status for ", problemid)
            return None
        
