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

        # FARI Where do we use keyset?
        self.keyset = set()
        self.datadict = {}
        self.metadatadict = {}
        # FARI Where do we use and what are parametervalues?
        self.parametervalues = {}
        self.defaultparametervalues = {}
        self.instanceset = set()
        """ meta data represent instance-independent data """

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

    def addData(self, probname, datakeys, data):
        '''
        add data to problem data under the specified key(s)

        add the current data - readers can use this method to add data, either as a single datakey, or as list,
        where in the latter case it is required that datakeys and data are both lists of the same length

        after data was added, the method problemGetData() can be used for access
        '''

        # check for the right dictionary to store the data
        # FARI The following is a pointer or a copy into local variable datadict?
        datadict = self.datadict if probname is not None else self.metadatadict
        
        logging.debug("TestRun %s receives data Datakey %s, %s to prob %s" % (self.getName(), repr(datakeys), repr(data), probname))

        if probname not in self.instanceset:
            self.instanceset.add(probname)

        if type(datakeys) is list and type(data) is list:
            for key, datum in zip(datakeys, data):
                col = datadict.setdefault(key, {})
                col[probname] = datum
        else:
            col = datadict.setdefault(datakeys, {})
            col[probname] = data

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

    def problemGetData(self, probname, datakey):
        '''
        returns data for a specific datakey, or None, if no such data exists for this (probname, datakey) key pair
        '''
        if self.datadict != {}:
            return self.datadict.get(datakey, {}).get(probname, None)
        else:
            try:
                data = self.data.loc[probname, datakey]
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

    def setupForDataCollection(self):
        self.datadict = self.data.to_dict()
        self.data = DataFrame(dtype=object)

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
            return [self.datadict.get(datakey, {}).get(probname, None) for probname in problemlist]
        else:
            return self.data.loc[problemlist, datakey]

    def deleteProblemData(self, probname):
        '''
        deletes all data acquired so far for probname
        '''
        if self.datadict != {}:
            for col in list(self.datadict.keys()):
                try:
                    del self.datadict[col][probname]
                except KeyError:
                    pass
        else:
            # FARI Why 'else'?
            try:
                self.data.drop(probname, inplace=True)
            except TypeError:
                # needs to be caught for pandas version < 0.13
                self.data = self.data.drop(probname)

    def getSettings(self):
        '''
        returns the settings associated with this test run
        '''
        # FARI When is this set? Or is this a "fancy" way of setting it directly?
        try:
            return self.data['Settings'][0]
        except KeyError:
            # FARI wouldn't it be nice to save these somewhere?
            return os.path.basename(self.filenames[0]).split('.')[-2]

    def getVersion(self):
        '''
        returns the version associated with this test run
        '''
        try:
            return self.data['Version'][0]
        except KeyError:
            return os.path.basename(self.filenames[0]).split('.')[3]

    def saveToFile(self, filename):
        try:
            f = open(filename, 'wb')
            pickle.dump(self, f, protocol=2)
            # TODO remove
            #print('CHECK DATA', self.data)
            #print('CHECK DATADICT', self.datadict)
            f.close()
        except IOError:
            print("Could not open %s for saving test run" % filename)

    def printToConsole(self):
        print(self.data.ix[0,:])
        
    def toJson(self):
        # FARI do we still need this?
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
    
    def getProbData(self, probname):
        try:
            return ",".join("%s: %s"%(key,self.problemGetData(probname, key)) for key in self.getKeySet())
        except KeyError:
            return "<%s> not contained in keys, have only\n%s"%(probname, ",".join((ind for ind in self.getProblems())))

    def getIdentification(self):
        '''
        return identification string of this test run
        '''
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
        
