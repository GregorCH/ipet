from StatisticReader import StatisticReader
import os
import re
from Manager import Manager

class ReaderManager(Manager):
   '''
   acquires test run data. subclasses of manager, because every reader has a unique name
   '''
   problemexpression = re.compile(r'^@01')
   extensions = [".mps", ".cip", ".fzn", ".pip", ".lp"]
   INSTANCE_END_EXPRESSION = re.compile('^=ready=')

   solvertype_recognition={StatisticReader.SOLVERTYPE_SCIP:"SCIP version ",
                           StatisticReader.SOLVERTYPE_GUROBI:"Gurobi Optimizer version",
                           StatisticReader.SOLVERTYPE_CPLEX:"Welcome to IBM(R) ILOG(R) CPLEX(R) Interactive Optimizer",
                           StatisticReader.SOLVERTYPE_XPRESS:"FICO Xpress Optimizer",
                           StatisticReader.SOLVERTYPE_CBC:"Welcome to the CBC MILP Solver",
                           StatisticReader.SOLVERTYPE_COUENNE:" Couenne  --  an Open-Source solver for Mixed Integer Nonlinear Optimization"}

   othersolvers = [solver for solver in solvertype_recognition.keys() if solver != StatisticReader.solvertype]
   def setTestRun(self, testrun):
      self.testrun = testrun
      self.filestrings = testrun.filenames
      for reader in self.getManageables():
         reader.setTestRun(testrun)

   def getNReaders(self):
      return len(self.countManageables())

   def hasReader(self, reader):
      listofnames = [installedreader.getName() for installedreader in self.getManageables()]
      if reader.getName() in listofnames:
         return True
      else:
         return False

   def registerReader(self, reader):
      self.addAndActivate(reader)

   def registerListOfReaders(self, readers):
      for reader in readers:
         self.addAndActivate(reader)

   def updateProblemName(self, line):

      if self.problemexpression.match(line):
         fullname = line.split()[1]
         namewithextension = os.path.basename(fullname);
         namewithextension = os.path.splitext(namewithextension)[0]
         for extension in self.extensions:
            namewithextension = namewithextension.split(extension)[0]
         StatisticReader.setProblemName(namewithextension)
         if namewithextension in self.testrun.getProblems():
            self.testrun.deleteProblemData(namewithextension)

   def endOfInstanceReached(self, line):
      if ReaderManager.INSTANCE_END_EXPRESSION.match(line):
         return True
      else:
         return False

   def checkSolverType(self, line):
      changed = False
      for key in ReaderManager.othersolvers:
         if line.startswith(ReaderManager.solvertype_recognition[key]):
            changed = True
            StatisticReader.changeSolverType(key)
            ReaderManager.othersolvers = [solver for solver in ReaderManager.solvertype_recognition.keys() if solver != StatisticReader.solvertype]
            break
      if changed:
         print "changed solver type to", StatisticReader.solvertype

   def collectData(self):
      assert(self.testrun != None)
      readers = self.getManageables(True)

      for filestring in self.filestrings:
         f = None
         try:
            f = open(filestring, 'r')
         except IOError:
            print 'File', filestring, "doesn't exist!"
            continue


         for line in f:
            self.updateProblemName(line)
            self.checkSolverType(line)
            if self.endOfInstanceReached(line):
               for reader in readers:
                  reader.execEndOfProb()
            else:
               for reader in readers:
                  reader.operateOnLine(line)


         f.close()
      # print("Collection of data finished")
      return 1

