from ipet.parsing.ReaderManager import ReaderManager
# from StatisticReader import StatisticReader
from TestRun import TestRun
from ipet import misc
from ipet.concepts.Observer import Observable
import pandas

try:
    import cPickle as pickle
except:
    import pickle
from ipet.concepts.Manager import Manager

from ipet.parsing import PrimalBoundReader, DualBoundReader, ErrorFileReader, \
    BestSolInfeasibleReader, LimitReachedReader, ObjlimitReader, \
    ObjsenseReader

from ipet.evaluation import IPETFilter
from ipet.evaluation.Aggregation import Aggregation
from ipet.misc.integrals import calcIntegralValue, getProcessPlotData
from pandas import Panel
import pandas as pd
import os
import sys

class Experiment(Observable):
    '''
    manages the collection of all log (.out) and .solu file data

    '''

    datakey_gap = 'SoluFileGap'

    def __init__(self, files=[], listofreaders=[]):
        self.testrunmanager = Manager()
        self.datakeymanager = Manager()


        self.readermanager = ReaderManager()
        self.readermanager.registerDefaultReaders()
        #self.filtermanager = Manager()
        #self.installSomeFilters()
        self.installAggregations()
        self.solufiles = []
        self.externaldata = None
        self.basename2testrun = {}

        for filename in files:
            self.addOutputFile(filename)

    def addOutputFile(self, filename, testrun=None):
        """
        adds an output file to a testrun or create a new testrun object with the specified filename

        the filename should be an out, error, or settings file
        """
        filebasename = os.path.splitext(os.path.basename(filename))[0]
        fileextension = os.path.splitext(filename)[-1]

        if fileextension == TestRun.FILE_EXTENSION:
            try:
                testrun = TestRun.loadFromFile(filename)
            except IOError, e:
                sys.stderr.write(" Loading testrun from file %s caused an exception\n%s\n" % (filename, e))
                return
        elif testrun is None:
            testrun = self.basename2testrun.setdefault(filebasename, TestRun())

        if fileextension != TestRun.FILE_EXTENSION:
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
        remove a testrun object from the experiment
        '''
        self.testrunmanager.deleteManageable(testrun)

    def addReader(self, reader):
        '''
        add a reader to the experiments reader manager
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
        get a specific manager of the experiment manager set. if managedclass is 'Testrun' or 'testrun',
        this will return the testrun manager object of this experiment
        '''
        lowerclass = managedclass.lower()
        if hasattr(self, lowerclass + 'manager'):
            return getattr(self, lowerclass + 'manager')

    def getManagers(self):
        '''
        returns a dictionary of all managers of this experiment object
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
                            gap = misc.getGap(val, optval, True)
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
                infinite = (pb == misc.FLOAT_INFINITY or pb == -misc.FLOAT_INFINITY)
                sense = 0
                if pb < db:
                    sense = 1
                else: sense = -1

                if not infinite and misc.getGap(pb, db, True) <= 1e-5:
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
            return misc.getGap(float(pb), float(optsol))
        else:
            return misc.FLOAT_INFINITY

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
        populate the aggregation manager of this Experiment instance

        Aggregations map numeric vectors to single numbers.
        '''
        self.aggregationmanager = Manager()
        for aggstring in ['min', 'max', 'mean', 'size']:
            self.aggregationmanager.addAndActivate(Aggregation(aggstring))
        for shift in [10.0, 100.0, 1000.0]:
            agg = Aggregation('shmean', shiftby=shift)
            agg.set_name("shifted geom. (%d)"%shift)
            self.aggregationmanager.addAndActivate(agg)

    def isPrimalBoundBetter(self, testrun, probname):
        """
        returns True if the primal bound for the given problem exceeds the best known solution value
        """
        pb = testrun.problemGetData(probname, PrimalBoundReader.datakey)
        objsense = testrun.problemGetData(probname, ObjsenseReader.datakey)
        optval = testrun.problemGetData(probname, "OptVal")

        if pb is None:
            return False

        reltol = 1e-5 * max(abs(pb), 1.0)

        if objsense == ObjsenseReader.minimize and optval - pb > reltol:
            return True
        elif objsense == ObjsenseReader.maximize and pb - optval > reltol:
            return True
        return False

    def isDualBoundBetter(self, testrun, probname):
        """
        returns True if the dual bound for the given problem exceeds the best known solution value
        """
        db = testrun.problemGetData(probname, DualBoundReader.datakey)
        pb = testrun.problemGetData(probname, PrimalBoundReader.datakey)

        if db is None:
            return False

        objsense = testrun.problemGetData(probname, ObjsenseReader.datakey)
        optval = testrun.problemGetData(probname, "OptVal")

        if pb is not None:
            reltol = 1e-5 * max(abs(pb), 1.0)
        else:
            reltol = 1e-5 * max(abs(optval), 1.0)

        if objsense == ObjsenseReader.minimize and db - optval > reltol:
            return True
        elif objsense == ObjsenseReader.maximize and optval - db > reltol:
            return True
        return False

    def determineStatusForOptProblem(self, testrun, probname):
        """
        determine status for a problem for which we know the optimal solution value
        """
        pb = testrun.problemGetData(probname, PrimalBoundReader.datakey)
        db = testrun.problemGetData(probname, DualBoundReader.datakey)
        limitreached = testrun.problemGetData(probname, LimitReachedReader.datakey)
        objlimitreached = (limitreached == "objectiveLimit")
        optval = testrun.problemGetData(probname, "OptVal")
        objsense = testrun.problemGetData(probname, ObjsenseReader.datakey)
        solfound = True if pb is not None else False

        # the run failed because the primal or dual bound were better than the known optimal solution value
        if solfound and (self.isPrimalBoundBetter(testrun, probname) or self.isDualBoundBetter(testrun, probname)):
            testrun.addData(probname, 'Status', "fail (objective value)")

        # the run finished correctly if an objective limit was given and the solver reported infeasibility
        elif not solfound and objlimitreached:
            objlimit = testrun.problemGetData(probname, ObjlimitReader.datakey)
            reltol = 1e-5 * max(abs(optval), 1.0)

            if (objsense == ObjsenseReader.minimize and optval - objlimit >= -reltol) or \
                  (objsense == ObjsenseReader.maximize and objlimit - optval >= -reltol):
                testrun.addData(probname, 'Status', "ok")
            else:
                testrun.addData(probname, 'Status', "fail (objective value)")
        # the solver reached a limit
        elif limitreached:
            testrun.addData(probname, 'Status', limitreached.lower())

        # the solver reached
        elif (db is None or misc.getGap(pb, db) < 1e-4) and not self.isPrimalBoundBetter(testrun, probname):
            testrun.addData(probname, 'Status', "ok")
        else:
            testrun.addData(probname, 'Status', "fail")

    def determineStatusForBestProblem(self, testrun, probname):
        """
        determine status for a problem for which we only know a best solution value
        """
        pb = testrun.problemGetData(probname, PrimalBoundReader.datakey)
        db = testrun.problemGetData(probname, DualBoundReader.datakey)
        limitreached = testrun.problemGetData(probname, LimitReachedReader.datakey)

        # we failed because dual bound is higher than the known value of a primal bound
        if self.isDualBoundBetter(testrun, probname):
            testrun.addData(probname, 'Status', "fail (dual bound)")

        # solving reached a limit
        elif limitreached:
            testrun.addData(probname, 'Status', limitreached.lower())
            if self.isPrimalBoundBetter(testrun, probname):
                testrun.addData(probname, 'Status', "better")

        # primal and dual bound converged
        elif misc.getGap(pb, db) < 1e-4:
            testrun.addData(probname, 'Status', "solved not verified")
        else:
            testrun.addData(probname, 'Status', "fail")

    def determineStatusForUnknProblem(self, testrun, probname):
        """
        determine status for a problem for which we don't know anything about the feasibility or optimality
        """
        pb = testrun.problemGetData(probname, PrimalBoundReader.datakey)
        db = testrun.problemGetData(probname, DualBoundReader.datakey)
        limitreached = testrun.problemGetData(probname, LimitReachedReader.datakey)

        if limitreached:
            testrun.addData(probname, 'Status', limitreached.lower())

            if pb is not None:
                testrun.addData(probname, 'Status', "better")
        elif misc.getGap(pb, db) < 1e-4:
            testrun.addData(probname, 'Status', "solved not verified")
        else:
            testrun.addData(probname, 'Status', "unknown")

    def determineStatusForInfProblem(self, testrun, probname):
        """
        determine status for a problem for which we know it's infeasible
        """
        pb = testrun.problemGetData(probname, PrimalBoundReader.datakey)
        solfound = True if pb is not None else False

        # no solution was found
        if not solfound:
            limitreached = testrun.problemGetData(probname, LimitReachedReader.datakey)
            if limitreached in ['TimeLimit', 'MemoryLimit', 'NodeLimit']:
                testrun.addData(probname, 'Status', limitreached.lower())
            else:
                testrun.addData(probname, 'Status', "ok")
        # a solution was found, that's not good
        else:
            testrun.addData(probname, 'Status', "fail (solution on infeasible instance)")


    def checkProblemStatus(self):
        '''
        checks a problem solving status

        checks whether the solver's return status matches the information about the instances
        '''
        for testrun in self.testrunmanager.getManageables():
            for probname in testrun.getProblems():
                solustatus = testrun.problemGetSoluFileStatus(probname)
                errcode = testrun.problemGetData(probname, ErrorFileReader.datakey)

                # an error code means that the instance aborted
                if errcode is not None:
                    testrun.addData(probname, 'Status', "fail (abort)")

                # if the best solution was not feasible in the original problem, it's a fail
                elif testrun.problemGetData(probname, BestSolInfeasibleReader.datakey) == True:
                    testrun.addData(probname, 'Status', "fail (solution infeasible)")

                # go through the possible solution statuses and determine the Status of the run accordingly
                elif solustatus == 'opt':
                    self.determineStatusForOptProblem(testrun, probname)
                elif solustatus == "best":
                    self.determineStatusForBestProblem(testrun, probname)
                elif solustatus == "inf":
                    self.determineStatusForInfProblem(testrun, probname)
                else:
                    self.determineStatusForUnknProblem(testrun, probname)

    def saveToFile(self, filename):
        '''
           save the experiment instance to a file specified by 'filename'.
           Save comprises testruns and their collected data as well as custom built readers.

           @note: works for any file extension, preferred extension is '.cmp'
        '''

        print "Saving Data"
        if not filename.endswith(".cmp"):
            print "Preferred file extension for experiment instances is '.cmp'"

        try:
            f = open(filename, "wb")
        except IOError:
            print "Could not open file named", filename
            return
        pickle.dump(self, f, protocol=2)

        f.close()
        print "Experiment saved to file", filename

    @staticmethod
    def loadFromFile(filename):
        '''
        loads a experiment instance from the file specified by filename. This should work for all files
        generated by the saveToFile command.

        @return: a Experiment instance, or None if errors occured
        '''
        try:
            f = open(filename, "rb")
        except IOError:
            print "Could not open file named", filename
            return
#      try:
        comp = pickle.load(f)
#      except:
#         print "Error occurred : Could not load experiment instance"
#         comp = None
        f.close()

        if not isinstance(comp, Experiment):
            print "the loaded data is not a experiment instance!"
            return None
        else:
            return comp

    def getDataPanel(self, onlyactive=False):
        """
        returns a pandas Data Panel of testrun data
        creates a panel from testrun data, using the testrun settings as key
        set onlyactive to True to only get active testruns as defined by the testrun manager
        """
        trdatadict = {tr.getSettings():tr.data for tr in self.testrunmanager.getManageables(onlyactive)}
        return Panel(trdatadict)
