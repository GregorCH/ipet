from ReaderManager import ReaderManager
# from StatisticReader import StatisticReader
from TestRun import TestRun
import Misc

import pickle
from Manager import Manager
from StatisticReader_HeurReader import HeurDataReader
from StatisticReader import PrimalBoundReader, DualBoundReader, SolvingTimeReader, TimeLimitReader, \
   BestSolFeasReader, MaxDepthReader, LimitReachedReader, NodesReader, RootNodeFixingsReader, \
   TimeToFirstReader, TimeToBestReader
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

class Comparator:
   '''
   manages the collection of all log (.out) and .solu file data

   '''

   datakey_gap = 'SoluFileGap'

   EXCLUDE_REASON_TIMEOUT = 'timout'
   EXCLUDE_REASON_INFEASIBLE = 'infeasible'
   EXCLUDE_REASON_ZEROSOLUTION = 'zerosolution'
   EXCLUDE_REASON_NOOPTIMALSOLUTIONKNOWN = 'nooptsolution'
   INFINITY = 1e09
   COMP_SIGN_LE = 1
   COMP_SIGN_GE = -1

   def __listelementsdiffer(self, listname):
      for listitem in listname:
         if listname.count(listitem) > 1:
            return False
      else:
         return True

   def __init__(self, files=[], listofreaders=[]):
      self.testrunmanager = Manager()
      self.datakeymanager = Manager()

      for filename in files:
         self.addLogFile(filename)

      self.readermanager = ReaderManager()
      self.filtermanager = Manager()
      self.installSomeFilters()
      self.installAllReaders()
      self.installSomeAggregations()

   def addLogFile(self, filename, testrun=None):
      '''
      adds a log file to a testrun or create a new testrun object with the specified filename
      '''
      if testrun is None:
         testrun = TestRun()
      testrun.appendFilename(filename)
      if testrun not in self.testrunmanager.getManageables():
         self.testrunmanager.addAndActivate(testrun)

   def addSoluFile(self, solufilename):
      '''
      associate a solu file with all testruns
      '''
      for testrun in self.testrunmanager.getManageables():
         if not solufilename in testrun.filenames:
            testrun.appendFilename(solufilename)

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

   def setTestRun(self, testrun):
      '''
      set the testrun for the data collector
      '''
      self.readermanager.setTestRun(testrun)

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

   def collectData(self):
      '''
      iterate over log files and solu file and collect data via installed readers
      '''
      for testrun in self.testrunmanager.getManageables():
         self.setTestRun(testrun)
         self.readermanager.collectData()

      self.makeProbNameList()
      self.calculateIntegrals()
      self.checkProblemStatus()

      for testrun in self.testrunmanager.getManageables():
         testrun.finalize()


      print 'Checking problem status'
      # post processing steps: things like primal integrals depend on several, independent data
      self.updateDatakeys()

   def getDatakeys(self):
      return self.datakeymanager.getAllRepresentations()

   def calculateIntegrals(self):
      '''
      calculates and stores primal and dual integral values for every problem under 'PrimalIntegral' and 'DualIntegral'
      '''
      dualargs = dict(historytouse='dualboundhistory', boundkey='DualBound')
      for testrun in self.testrunmanager.getManageables():
         for probname in self.probnamelist:
            processplotdata = getProcessPlotData(testrun, probname, testrun.problemGetData(probname, 'OptVal'))
            testrun.addData(probname, 'PrimalIntegral', calcIntegralValue(processplotdata))

            processplotdata = getProcessPlotData(testrun, probname, testrun.problemGetData(probname, 'OptVal'), **dualargs)
            testrun.addData(probname, 'DualIntegral', calcIntegralValue(processplotdata))

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


   def excludeProb(self, probname, excludereasons=[]):
      '''
      filter problems based on certain reasons
      '''
      for testrun in self.testrunmanager.getManageables():
         if Comparator.EXCLUDE_REASON_TIMEOUT in excludereasons:
            if testrun.timeLimitHit(probname):
               return True
         elif Comparator.EXCLUDE_REASON_NOOPTIMALSOLUTIONKNOWN in excludereasons:
            if testrun.problemGetSoluFileStatus(probname) != 'opt':
               return True
         elif Comparator.EXCLUDE_REASON_ZEROSOLUTION in excludereasons:
            if testrun.problemGetOptimalSolution(probname) == 0:
               return True
         elif Comparator.EXCLUDE_REASON_INFEASIBLE in excludereasons:
            if testrun.problemGetSoluFileStatus(probname) == 'inf':
               return True
      else:
         return False

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
      filter1 = IPETFilter('Nodes', '1', '>=')
      filter2 = IPETFilter('Status', 'ok', '==')
      filter3 = IPETFilter('SolvingTime', '0.0', '>=')
      for filters in [filter1, filter2, filter3]:
         self.filtermanager.addAndActivate(filters)

   def installSomeAggregations(self):
      self.aggregationmanager = Manager()
      for aggstring in Aggregation.possibleaggregations:
         self.aggregationmanager.addAndActivate(Aggregation(aggstring))

   def checkProblemStatus(self):
      '''
      checks a problem solving status
      '''
      for testrun in self.testrunmanager.getManageables():
         for probname in testrun.getProblems():
            optsol = testrun.problemGetOptimalSolution(probname)
            solustatus = testrun.problemGetSoluFileStatus(probname)
            pb = testrun.problemGetData(probname, PrimalBoundReader.datakey)
            db = testrun.problemGetData(probname, DualBoundReader.datakey)
            time = testrun.problemGetData(probname, SolvingTimeReader.datakey)
            timelimit = testrun.problemGetData(probname, TimeLimitReader.datakey)
            status = 'ok'
            probgap = Misc.getGap(pb, db)
            if probgap > 1e+4 and solustatus in ['opt', 'best', 'feas'] and testrun.problemGetData(probname, LimitReachedReader.datakey) is None:
               status = 'fail'
            elif testrun.problemCheckFail(probname) > 0:
               status = 'fail'
            elif testrun.problemGetData(probname, LimitReachedReader.datakey) is not None:
               status = testrun.problemGetData(probname, LimitReachedReader.datakey)

            if time is None:
               status = 'abort'

            if solustatus is None:
               status = 'unknown'


            testrun.addData(probname, 'Status', status)

   def installAllReaders(self):
      '''
      installs the whole set of available readers
      '''
      self.readermanager.registerListOfReaders([
#                 ConsTimePropReader(),
                 BestSolFeasReader(),
                 DualBoundReader(),
                 DualBoundHistoryReader(),
                 GeneralInformationReader(),
                 HeurDataReader(),
                 MaxDepthReader(),
                 LimitReachedReader(),
                 NodesReader(),
                 PluginStatisticsReader(),
                 PrimalBoundHistoryReader(),
                 PrimalBoundReader(),
                 VariableReader(),
                 RootNodeFixingsReader(),
                 SolvingTimeReader(),
                 SoluFileReader(),
                 TimeLimitReader(),
                 TimeToFirstReader(),
                 TimeToBestReader()
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
         f = open(filename, "w")
      except IOError:
         print "Could not open file named", filename
         return
      pickle.dump(self, f)

      f.close()
      print "Comparator saved to file", filename

   def loadFromFile(self, filename):
      '''
      loads a comparator instance from the file specified by filename. This should work for all files
      generated by the saveToFile command.

      @return: a Comparator instance, or None if errors occured
      '''
      try:
         f = open(filename, "r")
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
