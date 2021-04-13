"""
The MIT License (MIT)

Copyright (c) 2018 Zuse Institute Berlin, www.zib.de

Permissions are granted as stated in the license file you have obtained
with this software. If you find the library useful for your purpose,
please refer to README.md for how to cite IPET.

@author: Gregor Hendel
"""
from ipet import misc, Key
from .TestRun import TestRun
from ipet.concepts.Manager import Manager
from ipet.misc.integrals import calcIntegralValue, getProcessPlotData
from ipet.parsing.ReaderManager import ReaderManager

import pandas as pd
import pickle
import os
import sys
import logging
from ipet.validation import Validation

logger = logging.getLogger(__name__)

class Experiment:
    """
    an Experiment represents a collection of TestRun objects and the routines for parsing
    """
    DEFAULT_GAPTOL = 1e-4
    DEFAULT_VALIDATEDUAL = False

    def __init__(self, files = [], listofreaders = [], gaptol = DEFAULT_GAPTOL, validatedual = DEFAULT_VALIDATEDUAL):
        self.datakeymanager = Manager()

        self.readermanager = ReaderManager()
        self.readermanager.registerDefaultReaders()
        self.testruns = []
        self.externaldata = None
        self.basename2testrun = {}
        self.probnamelist = []
        self.validation = Validation(solufilename = None, tol = gaptol)

        for filename in files:
            self.addOutputFile(filename)

        self.gaptol = gaptol
        self.validatedual = validatedual
        self.joineddata = None

    def set_gaptol(self, gaptol : float):
        """
        Set the relative gap tolerance for the solver validation
        """
        self.gaptol = gaptol

    def set_validatedual(self, validatedual : bool):
        """Enable or disable validation of the primal dual gap
        """
        self.validatedual = validatedual

    # def addOutputFile(self, filename, testrun = None): # testrun parameter is unused
    def addOutputFile(self, filename):
        """ Add an output file for a testrun or create a new testrun object with the specified filename

        this method handles all types of feasible file types for an experiment, either preparsed
        TestRun files or raw solver output files or .solu files with additional information.

        If a file with an unrecognized file extension is passed to this method, a ValueError is raised.

        For a list of allowed file extensions, see ipet.parsing.ReaderManager.
        """

        filebasename, fileextension = os.path.splitext(filename)

        if not fileextension in [TestRun.FILE_EXTENSION] + self.readermanager.getFileExtensions():
            raise ValueError("Experiment cannot handle extension '%s' of file '%s'" % (fileextension, filename))

        if fileextension == TestRun.FILE_EXTENSION:
            try:
                testrun = TestRun.loadFromFile(filename)
            except IOError as e:
                sys.stderr.write(" Loading testrun from file %s caused an exception\n%s\n" % (filename, e))
                return
        else:  # if testrun is None:
            testrun = self.basename2testrun.setdefault(filebasename, TestRun())

        if fileextension != TestRun.FILE_EXTENSION:
            testrun.appendFilename(filename)

        if testrun not in self.getTestRuns():
            self.testruns.append(testrun)

        self.updateDatakeys()

    def addStdinput(self):
        """ Add stdin as input (for piping from terminal)
        """
        # TODO how to handle misbehaving input?
        testrun = TestRun()
        testrun.setInputFromStdin()
        self.testruns.append(testrun)
        self.updateDatakeys()

    def addSoluFile(self, solufilename):
        """ Associate a solu file with all testruns
        """
        self.validation = Validation(solufilename, self.gaptol)

    def removeTestrun(self, testrun):
        """ Remove a testrun object from the experiment
        """
        self.testruns.remove(testrun)

    def addReader(self, reader):
        """ Add a reader to the experiments reader manager
        """
        self.readermanager.registerReader(reader)

    def hasReader(self, reader):
        """ Return True if reader is already present
        """
        return self.readermanager.hasReader(reader)

    def getProblemNames(self):
        """ Return the list of problem Names
        """
        return self.probnamelist

    def getTestRuns(self):
        """ Returns all TestRuns
        """
        return self.testruns

    def getReaderManager(self):
        """ Return the Readermanager
        """
        return self.readermanager

    def updateDatakeys(self):
        """ Union of all data keys over all instances
        """
        keyset = set()
        for testrun in self.getTestRuns():
            for key in testrun.getKeySet():
                keyset.add(key)
        for key in keyset:
            try:
                self.datakeymanager.addManageable(key)
            except KeyError:
                pass
        if self.externaldata is not None:
            for key in self.externaldata.columns:
                try:
                    self.datakeymanager.addManageable(key)
                except KeyError:
                    pass

    def makeProbNameList(self):
        """ Return a list of names of problems that have been run
        """
        problemset = set()
        for testrun in self.getTestRuns():
            for problem in testrun.getProblemNames():
                problemset.add(problem)
        self.probnamelist = sorted(list(problemset))

    def addExternalDataFile(self, filename):
        """ Add a filename pointing to an external file, eg a solu file with additional information
        """
        try:
            self.externaldata = pd.read_table(filename, sep = " *", engine = 'python', header = 1, skipinitialspace = True)
            self.updateDatakeys()
            logger.debug("Experiment read external data file %s" % filename)
            logger.debug("%s" % self.externaldata.head(5))
        except:
            raise ValueError("Error reading file name %s" % filename)

    def collectData(self):
        """ Iterate over log files and solu file and collect data via installed readers
        """
        testruns = self.getTestRuns()

        for testrun in testruns:
            self.readermanager.setTestRun(testrun)
            testrun.setupForDataCollection()
            testrun.setValidation(self.validation)
            self.readermanager.collectData()

        # TODO Is this calculated only for validation?
        self.makeProbNameList()
        self.calculateGaps()
        self.calculateIntegrals()

        for testrun in testruns:
            testrun.setupAfterDataCollection()

        # post processing steps: things like primal integrals depend on several, independent data
        self.updateDatakeys()
        self.joineddata = None

    def getDatakeys(self):
        return self.datakeymanager.getAllRepresentations()

    def concatenateData(self):
        """ Concatenate data over all run TestRuns
        """
        self.data = pd.concat([tr.data for tr in self.getTestRuns()])

    def calculateGaps(self):
        """ Calculate and store primal and dual gap
        """

        # use validation reference bounds for storing primal and dual gaps
        if self.validation is None:
            return

        for testrun in self.getTestRuns():
            for problemid in testrun.getProblemIds():

                optval = self.validation.getReferencePb(testrun.getProblemDataById(problemid, Key.ProblemName))
                if optval is not None:
                    for key in [Key.PrimalBound, Key.DualBound]:
                        val = testrun.getProblemDataById(problemid, key)
                        if val is not None:
                            gap = misc.getGap(val, optval, True)
                            # subtract 'Bound' and add 'Gap' from Key
                            thename = key[:-5] + "Gap"
                            testrun.addDataById(thename, gap, problemid)

    def getJoinedData(self):
        """ Concatenate the testrun data (possibly joined with external data)

        this may result in nonunique index, the data is simply concatenated
        """
        if self.joineddata is not None:
            return self.joineddata

        datalist = []
        for tr in self.getTestRuns():
            trdata = tr.data
            if self.externaldata is not None:
                # Suggestion:
                # trdata = trdata.join(self.externaldata, on=Key.ProblemName, suffixes = ("", "_ext"))
                trdata = trdata.merge(self.externaldata, left_index = True, right_index = True, how = "left", suffixes = ("", "_ext"))
            datalist.append(trdata)

        # return pd.concat(datalist, sort=True).infer_objects() # in later pandas versions this needs a sort argument
        self.joineddata = pd.concat(datalist).infer_objects()

        return self.joineddata

    def calculateIntegrals(self,scale=False, lim=(None,None)):
        """ Calculate and store primal and dual integral values

        ... for every problem under 'PrimalIntegral' and 'DualIntegral'
        """
        dualargs = dict(historytouse = Key.DualBoundHistory, xaftersolvekey = Key.DualBound)

        if self.validation is None:
            return

        for testrun in self.getTestRuns():

            # go through problems and calculate both primal and dual integrals
            for problemid in testrun.getProblemIds():
                problemname = testrun.getProblemDataById(problemid, Key.ProblemName)
                processplotdata = getProcessPlotData(testrun, problemid, reference = self.validation.getReferencePb(problemname),scale=scale, lim=lim)

                # check for well defined data (may not exist sometimes)
                if processplotdata:
                    try:
                        testrun.addDataById(Key.PrimalIntegral, calcIntegralValue(processplotdata), problemid)
                        logger.debug("Computed primal integral %.1f for problem %s, data %s" % (testrun.getProblemDataById(problemid, 'PrimalIntegral'), problemid, repr(processplotdata)))
                    except AssertionError:
                        logger.error("Error for primal bound on problem %s, list: %s" % (problemid, processplotdata))

                processplotdata = getProcessPlotData(testrun, problemid, reference = self.validation.getReferenceDb(problemname), scale=scale, lim=lim, **dualargs)
                # check for well defined data (may not exist sometimes)
                if processplotdata:
                    try:
                        testrun.addDataById(Key.DualIntegral, calcIntegralValue(processplotdata, pwlinear = True), problemid)
                        logger.debug("Computed dual integral %.1f for problem %s, data %s" % (testrun.getProblemDataById(problemid, 'DualIntegral'), problemid, repr(processplotdata)))
                    except AssertionError:
                        logger.error("Error for dual bound on problem %s, list: %s " % (problemid, processplotdata))



    def printToConsole(self, formatstr = "{idx} {d}"):
        for tr in self.testruns:
            tr.printToConsole(formatstr)

    def saveToFile(self, filename):
        """ Save the experiment instance to a file specified by 'filename'.

        Save comprises testruns and their collected data as well as custom built readers.
        @note: works for any file extension, preferred extension is '.cmp'
        """
        if not filename.endswith(".cmp"):
            print("Preferred file extension for experiment instances is '.cmp'")

        try:
            f = open(filename, "wb")
        except IOError:
            print("Could not open file named", filename)
            return
        pickle.dump(self, f, protocol = 2)

        f.close()

    @staticmethod
    def loadFromFile(filename):
        """ Load an experiment instance from the file specified by filename.

        This should work for all files generated by the saveToFile command.
        @return: a Experiment instance, or None if errors occured
        """
        try:
            f = open(filename, "rb")
        except IOError:
            print("Could not open file named", filename)
            return
        comp = pickle.load(f)
        f.close()

        if not isinstance(comp, Experiment):
            print("the loaded data is not a experiment instance!")
            return None
        else:
            return comp

    def getDataPanel(self, onlyactive = False):
        """ Return a pandas Data Panel of testrun data

        Create a panel from testrun data, using the testrun settings as key
        Set onlyactive to True to only get active testruns as defined by the testrun manager
        """
        trdatadict = {tr.getSettings():tr.data for tr in self.getTestRuns(onlyactive)}
        return pd.Panel(trdatadict)
