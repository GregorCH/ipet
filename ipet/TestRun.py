import Misc
from StatisticReader import SolvingTimeReader, TimeLimitReader, PrimalBoundReader, TimeToBestReader, DualBoundReader, \
   BestSolFeasReader

from Editable import Editable
from pandas import DataFrame, notnull
import os
try:
    import cPickle as pickle
except:
    import pickle

class TestRun(Editable):
    '''
    represents the collected data of a particular (set of) log file(s)
    '''
    FILE_EXTENSION = ".trn"  # : the file extension for saving and loading test runs from
    def __init__(self, filenames=[]):
        self.filenames = []
        for filename in filenames:
            self.appendFilename(filename)
        self.data = DataFrame(dtype=object)


        self.keyset = set()
        self.datadict = {}


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

        if type(datakeys) is list and type(data) is list:
            for key, datum in zip(datakeys, data):
                col = self.datadict.setdefault(key, {})
                col[probname] = datum
        else:
            col = self.datadict.setdefault(datakeys, {})
            col[probname] = data

    def getKeySet(self):
        if self.datadict != {}:
            return self.datadict.keys()
        else:
            return set(self.data.columns)

    def problemGetData(self, probname, datakey):
        '''
        returns data for a specific datakey, or None, if no such data exists for this (probname, datakey) key pair
        '''
        if self.datadict != {}:
            return self.datadict.get(datakey, {}).get(probname, None)
        else:
            data = self.data.loc[probname, datakey]
            if type(data) is list or notnull(data):
                return data
            else:
                return None

    def emptyData(self):
        self.data = DataFrame(dtype=object)

    def setupForDataCollection(self):
        self.datadict = self.data.to_dict()
        self.data = DataFrame(dtype=object)

    def finalize(self):
        self.data = DataFrame(self.datadict)
        self.datadict = {}

    def getProblems(self):
        '''
        returns an (unsorted) list of problems
        '''
        if self.datadict != {}:
            return list(set([problem for col in self.datadict.keys() for problem in self.datadict[col].keys()]))
        else:
            return self.data.index

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
        deletes all data aquired so far for probname
        '''
        if self.datadict != {}:
            for col in self.datadict.keys():
                try:
                    del self.datadict[col][probname]
                except KeyError:
                    pass
        else:
            try:
                self.data.drop(probname, inplace=True)
            except TypeError:
                # needs to be caught for pandas version < 0.13
                self.data = self.data.drop(probname)

    def getSettings(self):
        '''
        returns the settings associated with this test run
        '''
        try:
            return self.data['Settings'][0]
        except KeyError:
            return self.filenames[0].split('.')[-2]

    def getVersion(self):
        '''
        returns the version associated with this test run
        '''
        try:
            return self.data['Version'][0]
        except KeyError:
            print self.filenames
            return self.filenames[0].split('.')[3]


    def saveToFile(self, filename):
        try:
            f = open(filename, 'w')
        except IOError:
            print "Could not open %s for saving test run" % filename

        pickle.dump(self, f, protocol=0)
        f.close()

    @staticmethod
    def loadFromFile(filename):
        try:
            f = open(filename, 'r')
        except IOError:
            print "Could not open %s for loading test run" % filename
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
            return self.filenames[0].split('.')[4]

    def getSolver(self):
        '''
        returns the LP solver used for this test run
        '''
        try:
            return self.data['Solver'][0]
        except KeyError:
            return self.filenames[0].split('.')[4]

    def getName(self):
        '''
        convenience method to make test run a manageable object
        '''
        return self.getIdentification()

    def getIdentification(self):
        '''
        return identification string of this test run
        '''
        return self.getSolver() + '(' + self.getVersion() + ')' + self.getLpSolver() + ':' + self.getSettings()

    def getShortIdentification(self, char='_', maxlength= -1):
        '''
        returns a short identification which only includes the settings of this test run
        '''
        return Misc.cutString(self.getSettings(), char, maxlength)


    def problemGetOptimalSolution(self, solufileprobname):
        '''
        returns objective of an optimal or a best known solution from solu file, or None, if
        no such data has been acquired
        '''
        try:
            return self.problemGetData(solufileprobname, 'OptVal')
        except KeyError:
            print self.getIdentification() + " has no solu file value for ", solufileprobname
            return None

    def problemGetSoluFileStatus(self, solufileprobname):
        '''
        returns 'unkn', 'inf', 'best', 'opt' as solu file status, or None, if no solu file status
        exists for this instance
        '''
        try:
            return self.problemGetData(solufileprobname, 'SoluFileStatus')
        except KeyError:
            print self.getIdentification() + " has no solu file status for ", solufileprobname
            return None


    def problemCheckFail(self, probname):
        '''
        returns 0 if testrun has not failed on that instance
                1 if solu file solution lies outside the interval [min(pb,db)-reltol, max(pb,db) + reltol]
                2 if solution was reported although the instance is known to be infeasible
                3 if best reported solution was not feasible for problem
        '''
        optsol = self.problemGetOptimalSolution(probname)
        solustatus = self.problemGetSoluFileStatus(probname)
        pb = self.problemGetData(probname, PrimalBoundReader.datakey)
        db = self.problemGetData(probname, DualBoundReader.datakey)
        if solustatus == 'opt' and pb is not None and db is not None:
            reltol = 1e-5 * max(abs(pb), 1.0)
            leftbound = min(pb, db) - reltol
            rightbound = max(pb, db) + reltol
            if optsol < leftbound or optsol > rightbound:
                return 1
        elif solustatus == 'inf':
            if pb is not None:
                return 2
        if self.problemGetData(probname, BestSolFeasReader.datakey) == True:
            return 3
        return 0
