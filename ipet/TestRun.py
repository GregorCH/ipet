"""
The MIT License (MIT)

Copyright (c) 2016 Zuse Institute Berlin, www.zib.de

Permissions are granted as stated in the license file you have obtained
with this software. If you find the library useful for your purpose,
please refer to README.md for how to cite IPET.

@author: Gregor Hendel
"""
import ipet.misc as misc
from ipet.parsing import Key
from pandas import DataFrame, notnull
import os
import logging

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
        """
        appends a file name to the list of filenames of this test run
        """
        filename = os.path.abspath(filename)
        if filename not in self.filenames:
            self.filenames.append(filename)

    def addDataByName(self, datakeys, data, problem):
        """
        add the current data under the specified dataname - readers can use this method to add data, either as a single datakey, or as list,
        where in the latter case it is required that datakeys and data are both lists of the same length

        after data was added, the method problemGetDataById() can be used for access
        """
        for problemkey, name in self.datadict.setdefault(Key.ProblemName, None):
            if name == problem:
                if type(datakeys) is list and type(data) is list:
                    for key, datum in zip(datakeys, data):
                        self.datadict.setdefault(key, {})[problemkey] = datum
                    else:
                        self.datadict.setdefault(datakeys, {})[problemkey] = data

    def addData(self, datakeys, data, instanceid = None):
        """
        add the current data or to the problem with specified id - readers can use this method to add data, either as a single datakey, or as list,
        where in the latter case it is required that datakeys and data are both lists of the same length

        after data was added, the method problemGetDataById() can be used for access if a instanceid was given
        """
        # check for the right dictionary to store the data
        logging.debug("TestRun %s receives data Datakey %s, %s to prob" % (self.getName(), repr(datakeys), repr(data)))

        if instanceid == None:
            if type(datakeys) is list and type(data) is list:
                for key, datum in zip(datakeys, data):
                    self.currentinstancedataseries[key] = datum
            else:
                self.currentinstancedataseries[datakeys] = data
        else: 
            if type(datakeys) is list and type(data) is list:
                for key, datum in zip(datakeys, data):
                    self.datadict.setdefault(key,{})[instanceid] = datum
            else:
                self.datadict.setdefault(datakeys, {})[instanceid] = data

    def addParameterValue(self, paramname, paramval):
        """
        stores the value for a parameter of a given name for this test run
        """
        self.parametervalues[paramname] = paramval

    def addDefaultParameterValue(self, paramname, defaultval):
        """
        stores the value for a parameter of a given name for this test run
        """
        self.defaultparametervalues[paramname] = defaultval

    def getParameterData(self):
        """
        returns two dictionaries that map parameter names to  their value and default value
        """
        return (self.parametervalues, self.defaultparametervalues)

    def getLogFile(self, fileextension=".out"):
        """
        Returns the name of the logfile
        """
        for filename in self.filenames:
            if filename.endswith(fileextension):
                return filename
        return None
    
    def getKeySet(self):
        """
        Returns a list or set of keys (which are the columns headers of the data) 
        """
        if self.datadict != {}:
            return list(self.datadict.keys())
        else:
            return set(self.data.columns)

    def problemGetDataByName(self, problemname, datakey):
        """
        Returns the data collected for problems with given name
        """
        for key, dat in self.datadict.get("Problemname", None):
            if dat == problemname:
                # FARI1 Is the name unique? What if it is not? Return list?
                return self.problemGetDataById(key, datakey)
        return None

    def problemGetDataById(self, instanceid, datakey):
        """
        returns data for a specific datakey, or None, if no such data exists for this (probname, datakey) key pair
        """
        if self.datadict != {}:
            return self.datadict.get(datakey, {}).get(instanceid, None)
        else:
            try:
                data = self.data.loc[instanceid, datakey]
            except KeyError:
                data = None
            if type(data) is list or notnull(data):
                return data
            else:
                return None

    def emptyData(self):
        """
        Empties data  
        """
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
        """ If any data has been found then it is saved into a new instanceset in datadict
        """
        if self.currentinstancedataseries != {}:
            # Add data collected by solver into currentinstancedataseries, such as primal and dual bound, 
            self.addData(solver.getKeys(), solver.getData())
            
            for key in self.currentinstancedataseries.keys():
                self.datadict.setdefault(key, {})[self.currentinstanceid] = self.currentinstancedataseries[key]
            self.currentinstancedataseries = {} 
            self.currentinstanceid = self.currentinstanceid + 1
            
        
    def finishedReadingFile(self, solver):
        """ in case that the last instancedata has not been saved yet, do it now
        """
        self.finalizeInstanceCollection(solver)
        
    def setupForDataCollection(self):
        """ save data in a python dictionary for easier data collection
        """
        self.datadict = self.data.to_dict()
        self.data = DataFrame(dtype=object)
        
    def setupAfterDataCollection(self):
        """ save data in a pandas dataframe for futher use (i.e. reading and finding data)
        """
        self.data = DataFrame(self.datadict)
        self.datadict = {}

    def hasInstance(self, instanceid):
        """ Returns if there is already data collected for a problem with given id
        """
        return instanceid in range(self.currentinstanceid)

    def getProblems(self):
        """
        returns an (unsorted) list of problems
        """
        return list(range(self.currentinstanceid))
        #if self.datadict != {}:
        #    return list(range(self.currentinstanceid))
        #else:
        #    return list(self.data.index.get_values())

    def problemlistGetData(self, instancelist, datakey):
        """
        returns data for a list of problems
        """
        if self.datadict != {}:
            return [self.datadict.get(datakey, {}).get(instanceid, None) for instanceid in instancelist]
        else:
            return self.data.loc[instancelist, datakey]

    def deleteProblemData(self, instanceid):
        """
        deletes all data acquired so far for instanceid
        """
        if self.datadict != {}:
            for col in list(self.datadict.keys()):
                try:
                    del self.datadict[col][instanceid]
                except KeyError:
                    pass
        else:
            try:
                self.data.drop(instanceid, inplace=True)
            except TypeError:
                # needs to be caught for pandas version < 0.13
                self.data = self.data.drop(instanceid)

    def getSettings(self):
        """
        returns the settings associated with this test run
        """
        try:
            return self.data['Settings'][0]
        except KeyError:
            # FARI1 this is a problem when we are reading from stdin
            return os.path.basename(self.filenames[0]).split('.')[-2]

    def getVersion(self):
        """
        returns the version associated with this test run
        """
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
        """
        returns the LP solver used for this test run
        """
        try:
            return self.data['LPSolver'][0]
        except KeyError:
            return os.path.basename(self.filenames[0]).split('.')[-4]

    def getSolver(self):
        """
        returns the LP solver used for this test run
        """
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
        """
        convenience method to make test run a manageable object
        """
        return self.getIdentification()
    
    def problemGetData(self, instanceid):
        try:
            return ",".join("%s: %s"%(key,self.problemGetDataById(instanceid, key)) for key in self.getKeySet())
        except KeyError:
            return "<%s> not contained in keys, have only\n%s"%(instanceid, ",".join((ind for ind in self.getProblems())))

    def getIdentification(self):
        """
        return identification string of this test run
        """
        # FARI1 Is this still the way to do this? What if we are reading from stdin?
        return os.path.splitext(os.path.basename(self.filenames[0]))[0]

    def getShortIdentification(self, char='_', maxlength= -1):
        """
        returns a short identification which only includes the settings of this test run
        """
        return misc.cutString(self.getSettings(), char, maxlength)

    def problemGetOptimalSolution(self, instanceid):
        """
        returns objective of an optimal or a best known solution from solu file, or None, if
        no such data has been acquired
        """
        try:
            return self.problemGetDataById(instanceid, 'OptVal')
        except KeyError:
            print(self.getIdentification() + " has no solu file value for ", instanceid)
            return None

    def problemGetSoluFileStatus(self, instanceid):
        """  
        returns 'unkn', 'inf', 'best', 'opt' as solu file status, or None, if no solu file status
        exists for this instance
        """
        try:
            return self.problemGetDataById(instanceid, 'SoluFileStatus')
        except KeyError:
            print(self.getIdentification() + " has no solu file status for ", instanceid)
            return None
        
