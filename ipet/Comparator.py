from ReaderManager import ReaderManager
# from StatisticReader import StatisticReader
from TestRun import TestRun
import Misc
from ipet.Observer import Observable
from ipet.IPETMessageStream import Message
import pandas
from ipet.StatisticReader_DualBoundHistoryReader import ParascipDualBoundHistoryReader

try:
    import cPickle as pickle
except:
    import pickle
from Manager import Manager
from StatisticReader_HeurReader import HeurDataReader
from StatisticReader import PrimalBoundReader, DualBoundReader, GapReader, SolvingTimeReader, TimeLimitReader, \
   BestSolFeasReader, MaxDepthReader, LimitReachedReader, NodesReader, RootNodeFixingsReader, \
   TimeToFirstReader, TimeToBestReader, ListReader, ObjsenseReader
from StatisticReader_DualBoundHistoryReader import DualBoundHistoryReader
from StatisticReader_PluginStatisticsReader import PluginStatisticsReader
from StatisticReader_GeneralInformationReader import GeneralInformationReader
from StatisticReader_PrimalBoundHistoryReader import PrimalBoundHistoryReader
from StatisticReader_SoluFileReader import SoluFileReader
from StatisticReader_VariableReader import VariableReader
from IPETFilter import IPETFilter
from Aggregation import Aggregation
from integrals import calcIntegralValue, getProcessPlotData
from pandas import Panel
import pandas as pd
from StatisticReader import DateTimeReader
import os
import sys

class Comparator(Observable):
    '''
    manages the collection of all log (.out) and .solu file data

    '''

    datakey_gap = 'SoluFileGap'

    def __init__(self, files=[], listofreaders=[]):
        self.testrunmanager = Manager()
        self.datakeymanager = Manager()

        for filename in files:
            self.addLogFile(filename)

        self.readermanager = ReaderManager()
        #self.filtermanager = Manager()
        #self.installSomeFilters()
        self.installAllReaders()
        self.installAggregations()
        self.solufiles = []
        self.externaldata = None

    def addLogFile(self, filename, testrun=None):
        '''
        adds a log file to a testrun or create a new testrun object with the specified filename
        '''
        if os.path.splitext(filename)[-1] == TestRun.FILE_EXTENSION:
            try:
                testrun = TestRun.loadFromFile(filename)
            except IOError, e:
                sys.stderr.write(" Loading testrun from file %s caused an exception\n%s\n" % (filename, e))
                return
        elif testrun is None:
            testrun = TestRun()
        if os.path.splitext(filename)[-1] != TestRun.FILE_EXTENSION:
            testrun.appendFilename(filename)

        if testrun not in self.testrunmanager.getManageables():
            self.testrunmanager.addAndActivate(testrun)

        self.updateDatakeys()

    def addSoluFile(self, solufilename):
        '''
        associate a solu file with all testruns
        '''
        if solufilename not in self.solufiles:
            self.solufiles.append(solufilename)

    def removeTestrun(self, testrun):
        '''
        remove a testrun object from the comparator
        '''
        self.testrunmanager.deleteManageable(testrun)

    def addReader(self, reader):
        '''
        add a reader to the comparators reader manager
        '''
        self.readermanager.registerReader(reader)

    def hasReader(self, reader):
        '''
        return True if reader is already present
        '''
        return self.readermanager.hasReader(reader)

    def getProblems(self):
        '''
        returns the list of problem names
        '''
        return self.probnamelist

    def updateDatakeys(self):
        '''
        union of all data keys over all instances
        '''
        keyset = set()
        for testrun in self.testrunmanager.getManageables():
            for key in testrun.getKeySet():
                keyset.add(key)
        for key in keyset:
            try:
                self.datakeymanager.addManageable(key)
            except KeyError:
                pass

    def makeProbNameList(self):
        problemset = set()
        for testrun in self.testrunmanager.getManageables():
            for problem in testrun.getProblems():
                problemset.add(problem)

        self.probnamelist = list(problemset)

    def getManager(self, managedclass):
        '''
        get a specific manager of the comparator manager set. if managedclass is 'Testrun' or 'testrun',
        this will return the testrun manager object of this comparator
        '''
        lowerclass = managedclass.lower()
        if hasattr(self, lowerclass + 'manager'):
            return getattr(self, lowerclass + 'manager')

    def getManagers(self):
        '''
        returns a dictionary of all managers of this comparator object
        '''
        managernames = [name for name in dir(self) if name.endswith('manager')]
        return {name:getattr(self, name) for name in managernames}

    def addExternalDataFile(self, filename):
        '''
        add a filename pointing to an external file, eg a solu file with additional information
        '''
        try:
            self.externaldata = pd.read_table(filename, sep = " *", engine = 'python', header = 1, skipinitialspace = True)
        except:
            raise ValueError("Error reading file name %s"%filename)


    def collectData(self):
        '''
        iterate over log files and solu file and collect data via installed readers
        '''

        # add solu file to testrun if it's not yet done
        testruns = self.testrunmanager.getManageables()
        for testrun in testruns:
            for solufilename in self.solufiles:
                testrun.appendFilename(solufilename)

        for testrun in testruns:
            self.readermanager.setTestRun(testrun)
            testrun.setupForDataCollection()
            self.readermanager.collectData()

        self.makeProbNameList()
        self.calculateGaps()
        self.calculateIntegrals()
        self.checkProblemStatus()

        for testrun in testruns:
            testrun.finalize()

        for tr in testruns:
            self.testrunmanager.reinsertManageable(tr)


        print 'Checking problem status'
        # post processing steps: things like primal integrals depend on several, independent data
        self.updateDatakeys()

    def getDatakeys(self):
        return self.datakeymanager.getAllRepresentations()

    def concatenateData(self):
        self.data = pandas.concat([tr.data for tr in self.testrunmanager.getManageables()])

    def calculateGaps(self):
        '''
        calculate and store primal and dual gap
        '''
        for testrun in self.testrunmanager.getManageables():
            for probname in self.probnamelist:

                optval = testrun.problemGetData(probname, "OptVal")
                if optval is not None:
                    for key in ["PrimalBound", "DualBound"]:
                        val = testrun.problemGetData(probname, key)
                        if val is not None:
                            gap = Misc.getGap(val, optval, True)
                            # subtract 'Bound' and add 'Gap' from Key
                            thename = key[:-5] + "Gap"
                            testrun.addData(probname, thename, gap)



    def getJoinedData(self):
        '''
        concatenate the testrun data (possibly joined with external data)

        '''
        datalist = []
        for tr in self.testrunmanager.getManageables():
            trdata = tr.data
            if self.externaldata is not None:
                trdata = trdata.merge(self.externaldata, left_index = True, right_index = True, how = "left", suffixes = ("", "_ext"))
            datalist.append(trdata)

        return pd.concat(datalist)



    def calculateIntegrals(self):
        '''
        calculates and stores primal and dual integral values for every problem under 'PrimalIntegral' and 'DualIntegral'
        '''
        dualargs = dict(historytouse='dualboundhistory', boundkey='DualBound')
        for testrun in self.testrunmanager.getManageables():

            # go through problems and calculate both primal and dual integrals
            for probname in self.probnamelist:
                processplotdata = getProcessPlotData(testrun, probname)

                #check for well defined data (may not exist sometimes)

                if processplotdata:
                    try:
                        testrun.addData(probname, 'PrimalIntegral', calcIntegralValue(processplotdata))
                    except AssertionError, e:
                        print e
                        print "Error for primal bound on problem %s, list: "%(probname)
                        print testrun.getProbData(probname)
                processplotdata = getProcessPlotData(testrun, probname, **dualargs)
                # check for well defined data (may not exist sometimes)
                if processplotdata:
                    try:
                        testrun.addData(probname, 'DualIntegral', calcIntegralValue(processplotdata, pwlinear=True))
                    except AssertionError, e:
                        print e
                        print "Error for dual bound on problem %s, list: "%(probname), processplotdata
                        print testrun.getProbData(probname)

    def writeSolufile(self):
        '''
        write a solu file based on the parsed results
        '''
        # ## collect data
        solufiledata = {}
        for testrun in self.testrunmanager.getManageables():
            for probname in testrun.getProblems():
                pb = testrun.problemGetData(probname, PrimalBoundReader.datakey)
                db = testrun.problemGetData(probname, DualBoundReader.datakey)
                if pb is None or db is None:
                    continue
                status = '=unkn='
                infinite = (pb == Misc.FLOAT_INFINITY or pb == -Misc.FLOAT_INFINITY)
                sense = 0
                if pb < db:
                    sense = 1
                else: sense = -1

                if not infinite and Misc.getGap(pb, db, True) <= 1e-5:
                    status = '=opt='
                elif not infinite:
                    status = '=best='
                elif pb == db:
                    status = '=inf='

                currentsolufileentry = solufiledata.get(probname)
                if currentsolufileentry == None:
                    solufiledata[probname] = (status, pb)
                else:
                    solustatus, solupb = currentsolufileentry
                    if solustatus == '=best=':
                        assert sense != 0
                        if not infinite and sense * (solupb - pb) < 0 or status == '=opt=':
                            solufiledata[probname] = (status, pb)
                    elif solustatus == '=unkn=':
                        solufiledata[probname] = (status, pb)

        # # write solufiledata to file
        newsolufilename = 'newsolufile.solu'
        f = open(newsolufilename, 'w')
        for prob in sorted(solufiledata.keys(), reverse=False):
            solustatus, solupb = solufiledata.get(prob)
            f.write("%s %s" % (solustatus, prob))
            if solustatus in ['=best=', '=opt=']:
                f.write(" %g" % solupb)
            f.write("\n")

        f.close()


    def testrunGetProbGapToOpt(self, testrun, probname):
        optsol = testrun.problemGetOptimalSolution(probname)
        status = testrun.problemGetSoluFileStatus(probname)
        pb = testrun.problemGetData(probname, PrimalBoundReader.datakey)
        if status == 'opt' or status == 'best':
            return Misc.getGap(float(pb), float(optsol))
        else:
            return Misc.FLOAT_INFINITY

    def checkForFails(self):
        '''
        all testruns and instances go through fail check.

        returns a dictionary to contain all instances which failed
        '''
        faildict = {}
        for testrun in self.testrunmanager.getManageables():
            for probname in self.probnamelist:
                if testrun.problemCheckFail(probname) > 0:
                    faildict.setdefault(testrun.getIdentification(), []).append(probname)
        return faildict

    def installSomeFilters(self):
        filter1 = IPETFilter('Nodes', '1', 'ge')
        filter2 = IPETFilter('Status', 'ok', 'eq')
        filter3 = IPETFilter('SolvingTime', '0.0', 'ge')
        for filters in [filter1, filter2, filter3]:
            self.filtermanager.addAndActivate(filters)

    def installAggregations(self):
        '''
        populate the aggregation manager of this Comparator instance

        Aggregations map numeric vectors to single numbers.
        '''
        self.aggregationmanager = Manager()
        for aggstring in ['min', 'max', 'mean', 'size']:
            self.aggregationmanager.addAndActivate(Aggregation(aggstring))
        for shift in [10.0, 100.0, 1000.0]:
            agg = Aggregation('shmean', shiftby=shift)
            agg.set_name("shifted geom. (%d)"%shift)
            self.aggregationmanager.addAndActivate(agg)

    def checkProblemStatus(self):
        '''
        checks a problem solving status
        '''
        for testrun in self.testrunmanager.getManageables():
            for probname in testrun.getProblems():
                solustatus = testrun.problemGetSoluFileStatus(probname)
                pb = testrun.problemGetData(probname, PrimalBoundReader.datakey)
                db = testrun.problemGetData(probname, DualBoundReader.datakey)
                time = testrun.problemGetData(probname, SolvingTimeReader.datakey)
                status = 'ok'
                if solustatus is None:
                    status = 'unknown'

                probgap = Misc.getGap(pb, db)
                if probgap > 1e-4 and solustatus in ['opt', 'best', 'feas'] and testrun.problemGetData(probname, LimitReachedReader.datakey) is None:
                    status = 'fail'
                elif testrun.problemCheckFail(probname) > 0:
                    status = 'fail'
                elif testrun.problemGetData(probname, LimitReachedReader.datakey) is not None:
                    status = testrun.problemGetData(probname, LimitReachedReader.datakey).lower()

                if time is None:
                    status = 'abort'

                testrun.addData(probname, 'Status', status)

    def installAllReaders(self):
        '''
        installs the whole set of available readers
        '''
        self.readermanager.registerListOfReaders([
 #                 ConsTimePropReader(),
                  BestSolFeasReader(),
                  DateTimeReader(),
                  DualBoundReader(),
                  DualBoundHistoryReader(),
                  ParascipDualBoundHistoryReader(),
                  GapReader(),
                  GeneralInformationReader(),
                  HeurDataReader(),
                  MaxDepthReader(),
                  LimitReachedReader(),
                  NodesReader(),
                  ObjsenseReader(),
                  PluginStatisticsReader(),
                  PrimalBoundHistoryReader(),
                  PrimalBoundReader(),
                  VariableReader(),
                  RootNodeFixingsReader(),
                  SolvingTimeReader(),
                  SoluFileReader(),
                  TimeLimitReader(),
                  TimeToFirstReader(),
                  TimeToBestReader(),
                  ])

    def saveToFile(self, filename):
        '''
           save the comparator instance to a file specified by 'filename'.
           Save comprises testruns and their collected data as well as custom built readers.

           @note: works for any file extension, preferred extension is '.cmp'
        '''

        print "Saving Data"
        if not filename.endswith(".cmp"):
            print "Preferred file extension for comparator instances is '.cmp'"

        try:
            f = open(filename, "wb")
        except IOError:
            print "Could not open file named", filename
            return
        pickle.dump(self, f, protocol=2)

        f.close()
        print "Comparator saved to file", filename

    @staticmethod
    def loadFromFile(filename):
        '''
        loads a comparator instance from the file specified by filename. This should work for all files
        generated by the saveToFile command.

        @return: a Comparator instance, or None if errors occured
        '''
        try:
            f = open(filename, "rb")
        except IOError:
            print "Could not open file named", filename
            return
#      try:
        comp = pickle.load(f)
#      except:
#         print "Error occurred : Could not load comparator instance"
#         comp = None
        f.close()

        if not isinstance(comp, Comparator):
            print "the loaded data is not a comparator instance!"
            return None
        else:
            return comp

    def getDataPanel(self, onlyactive=False):
        '''
        returns a pandas Data Panel of testrun data
        creates a panel from testrun data, using the testrun settings as key
        set onlyactive to True to only get active testruns as defined by the testrun manager
        '''
        trdatadict = {tr.getSettings():tr.data for tr in self.testrunmanager.getManageables(onlyactive)}
        return Panel(trdatadict)
