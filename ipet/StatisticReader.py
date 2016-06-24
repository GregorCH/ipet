# -*- coding: utf-8 -*-
import re
from Editable import Editable
import Misc
import numpy as np
import datetime

class StatisticReader(Editable):
    '''
    base class for all statistic readers - readers should always inherit from this base class for minimal implementation
    effort

    readers only need to overwrite the methods extractStatistic() and perhaps execEndOfProb()
    '''

    name = 'NO_NAME_DEFINED_YET'
    regular_exp = re.compile('')
    datakey = 'NO KEY'
    datatype = float
    lineindex = -1
    # print data#
    problemname = ''
    problemnamelist = []
    numericExpression = re.compile("([+\-]*[\d]+[.\d]*(?:e[+-])?-*[\d]*[kMG]{0,1}|[\-]+)")
    tablenumericExpression = re.compile("([+\-]*[\d]+[.\d]*(?:e[+-])?-*[\d]*[kMG]{0,1}|[\-]+|cutoff)")
    wordExpression = re.compile(r'[^\s]+')
    useStringSplit = False

    sleepAfterReturn = True
    sleep = False

    multipliers = dict(k=1000, M=1e6, G=1e9)

    # the reader might behave differently depending on the solver type, due to the different output
    SOLVERTYPE_SCIP = "SCIP"
    SOLVERTYPE_GUROBI = "GUROBI"
    SOLVERTYPE_CPLEX = "CPLEX"
    SOLVERTYPE_CBC = "CBC"
    SOLVERTYPE_XPRESS = "XPRESS"
    SOLVERTYPE_COUENNE = "Couenne"
    solvertype = SOLVERTYPE_SCIP



    def setProblemName(problemname):
        StatisticReader.problemname = problemname
    setProblemName = staticmethod(setProblemName)

    @staticmethod
    def changeSolverType(newtype):
        StatisticReader.solvertype = newtype

    def setTestRun(self, testrun):
        self.testrun = testrun

    def getSplitLineWithRegexp(self, regular_exp, line, index= -1, startofline=False):
        if startofline == True and not re.match(regular_exp, line):
            return None
        if startofline == False and not re.search(regular_exp, line):
            return None

        if index == -1:
            return line.split()
        else:
            return line.split()[index]

    def getName(self):
        return self.name

    def getWordAtIndex(self, line, index):
        '''
        get the i'th word in a space separated string of words
        '''
        if index < 0 or StatisticReader.useStringSplit:
            try:
                return line.split()[index]
            except:
                return None
        else:
            for idx, word in enumerate(StatisticReader.wordExpression.finditer(line)):
                if idx == index:
                    return word.group()
        return None
    def getNumberAtIndex(self, line, index):
        '''
        get the i'th number from the list of numbers in this line
        '''
        try:
            if index < 0:
                return StatisticReader.numericExpression.findall(line)[self.index]
            else:
                for idx, word in enumerate(StatisticReader.numericExpression.finditer(line)):
                    if idx == index:
                        return word.group()
                else:
                    return None
        except IndexError:
            return None

    def extractStatistic(self, line):
        '''
        overwrite this method for own reader subclasses - make sure that a return statement different from 'None'
        is only accepted once on each instance of the log file
        '''
        try:
            if self.regular_exp.search(line):
                data = None
                try:
                    data = self.datatype(self.getWordAtIndex(line, self.lineindex))
                except ValueError:
                    data = None
                except IndexError:
                    data = None
                except TypeError:
#                  print self.name, " failed data conversion"
                    raise TypeError("Type error during data conversion in line <%s>"%line)
                self.testrun.addData(self.problemname, self.datakey, data)
        except AttributeError:
#          print self.name, " has no such attribute"
            pass

        return None


    def execEndOfProb(self):
        '''
        overwrite this method to implement final behaviour at the end of each problem, such as setting flags
        '''
        return None


    def operateOnLine(self, line):
        self.extractStatistic(line)

    def turnIntoFloat(self, astring):
        '''
        parses strings to floats, keeps track of trailing caracters signifying magnitudes

        Special attention is put to strings of the form, e.g., '900k' where
        the tailing 'k'-character signifies multiplication by 1000.
        '''

        lastelem = astring[-1]
        multiplier = StatisticReader.multipliers.get(lastelem, 1.0)

        return float(astring.rstrip('kMG')) * multiplier

######################################################################################
# DERIVED Classes

class BestSolFeasReader(StatisticReader):
    '''
    catches the expression 'best solution is not feasible in original problem'

    @return: False if above expression is found in the log and the best solution is thus not feasible, otherwise True
    '''
    name = 'BestSolFeasReader'
    regular_exp = 'best solution is not feasible in original problem'
    datakey = 'Fail'

    bestsolfailedcheck = False
    def extractStatistic(self, line):
        if re.search(self.regular_exp, line):
            self.bestsolfailedcheck = True

        return None

    def execEndOfProb(self):
        self.testrun.addData(self.problemname, self.datakey, self.bestsolfailedcheck)
        self.bestsolfailedcheck = False



class DateTimeReader(StatisticReader):
    '''
    reads in the start and finish time from a timestamp in given in Milliseconds

    If found, the corresponding data keys are Datetime_Start and Datetime_End
    '''
    name = 'DateTimeReader'  # : the name for this reader
    datetimestartexp = re.compile(r"^@03 ([0-9]+)")  # : the expression for the date time start
    datetimeendexp = re.compile(r"^@04 ([0-9]+)")  # : the expression for the date time after termination
    datetimestartdatakey = 'Datetime_Start'  # : data key for start of run
    datetimeendkey = 'Datetime_End'  # : data key for end of run

    datetimekw = {datetimestartdatakey:datetimestartexp, datetimeendkey:datetimeendexp}

    def extractStatistic(self, line):
        for key, exp in self.datetimekw.items():
            matched = exp.match(line)
            if matched:
                timestamp = long(matched.groups()[0])
                time = datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
                self.testrun.addData(self.problemname, key, time)
                break

class DualLPTimeReader(StatisticReader):
    '''
    reads the dual LP time
    '''
    name = 'DualLPTimeReader'
    regular_exp = re.compile('^  dual LP')
    datakey = 'duallptime'
    datatype = float
    lineindex = 3

class DualBoundReader(StatisticReader):
    '''
    returns the reported dual bound at the end of the solve
    '''
    name = 'DualBoundReader'
    dualboundpatterns = {StatisticReader.SOLVERTYPE_SCIP : "^Dual Bound         :",
                         StatisticReader.SOLVERTYPE_GUROBI : '^Best objective',
                         StatisticReader.SOLVERTYPE_CPLEX : '(^Current MIP best bound =|^MIP - Integer optimal)',
                         StatisticReader.SOLVERTYPE_COUENNE : '^Lower Bound:'}
    dualboundlineindices = {StatisticReader.SOLVERTYPE_SCIP :-1,
                            StatisticReader.SOLVERTYPE_CPLEX : 5,
                            StatisticReader.SOLVERTYPE_GUROBI : 5,
                            StatisticReader.SOLVERTYPE_COUENNE : 2}
    datakey = 'DualBound'

    def extractStatistic(self, line):
        if re.match(self.dualboundpatterns[StatisticReader.solvertype], line):
            index = self.dualboundlineindices[StatisticReader.solvertype]
            if re.search('^MIP - Integer optimal', line):
                assert StatisticReader.solvertype == StatisticReader.SOLVERTYPE_CPLEX
                index = -1
            db = self.getWordAtIndex(line, index)
            db = db.strip(',');
            try:
                db = float(db)
                if abs(db) != Misc.FLOAT_INFINITY:
                    self.testrun.addData(self.problemname, self.datakey, db)
            except ValueError:
                pass
#               print line

class GapReader(StatisticReader):
    '''
    reads the primal dual gap at the end of the solving
    '''
    name = 'GapReader'
    regular_exp = re.compile('^Gap                :')
    datakey = 'Gap'
    datatype = float
    lineindex = 2

    def extractStatistic(self, line):
        if self.regular_exp.match(line):
            gapasword = self.getWordAtIndex(line, self.lineindex)

            # if the gap is infinite, no data is passed to the test run
            if gapasword != "infinite":
                gap = self.turnIntoFloat(gapasword)
                self.testrun.addData(self.problemname, self.datakey, gap)


class LimitReachedReader(StatisticReader):
    '''
    reads if memory limit was hit
    '''
    name = 'LimitReachedReader'

    regular_exp = re.compile(r'\[(.*) (reached|interrupt)\]')
    lineexpression = re.compile(r'^SCIP Status        :')
    datakey = 'LimitReached'

    def extractStatistic(self, line):
        if self.lineexpression.match(line):
            match = self.regular_exp.search(line)
            if match is not None:
                stringexpression = match.groups()[0]
                limit = "".join((part.capitalize() for part in stringexpression.split()))
                self.testrun.addData(self.problemname, self.datakey, limit)

class MaxDepthReader(StatisticReader):
    '''
    reads the maximum depth
    '''
    name = 'MaxDepthReader'
    regular_exp = re.compile('  max depth        :')
    datakey = 'MaxDepth'
    datatype = int
    lineindex = 3

class NodesReader(StatisticReader):
    '''
    reads the total number of solving nodes of the branch and bound search
    '''
    name = 'NodesReader'
    regular_exp = re.compile("^  nodes \(total\)    :")
    datakey = 'Nodes'
    datatype = int
    lineindex = 3

class ObjsenseReader(StatisticReader):
    name = 'ObjsenseReader'
    regular_exp = re.compile("^  Objective sense  : (\w*)")
    datakey = "Objsense"
    minimize = 1
    maximize = -1

    def extractStatistic(self, line):
        match = self.regular_exp.match(line)

        if match:
            objsense = self.minimize
            if match.groups()[0] == "maximize":
                objsense = self.maximize

            self.testrun.addData(self.problemname, self.datakey, objsense)





class PrimalBoundReader(StatisticReader):
    '''
    reads the primal bound at the end of the solve
    '''
    name = 'PrimalBoundReader'
    primalboundpatterns = {StatisticReader.SOLVERTYPE_SCIP: '^Primal Bound       :',
                           StatisticReader.SOLVERTYPE_CPLEX : '^MIP -.*Objective = ',
                           StatisticReader.SOLVERTYPE_GUROBI : '^Best objective ',
                           StatisticReader.SOLVERTYPE_COUENNE : "^Upper bound:"}
    primalboundlineindices = {StatisticReader.SOLVERTYPE_SCIP: 3,
                              StatisticReader.SOLVERTYPE_CPLEX :-1,
                              StatisticReader.SOLVERTYPE_GUROBI : 2,
                              StatisticReader.SOLVERTYPE_COUENNE : 2}
    datakey = 'PrimalBound'

    def extractStatistic(self, line):
        if re.search(self.primalboundpatterns[StatisticReader.solvertype], line):
            pb = self.getWordAtIndex(line, self.primalboundlineindices[StatisticReader.solvertype])
            pb = pb.strip(',')
            if pb != '-':
                pb = float(pb)
                if abs(pb) != Misc.FLOAT_INFINITY:
                    self.testrun.addData(self.problemname, self.datakey, pb)


class RootNodeFixingsReader(StatisticReader):
    '''
    reads the number of variable fixings during root node
    '''
    name = 'RootNodeFixingsReader'
    regular_exp = re.compile('^  root node')
    datakey = 'RootNodeFixs'
    datatype = int
    lineindex = 4

class SolvingTimeReader(StatisticReader):
    '''
    reads the overall solving time
    '''
    name = 'SolvingTimeReader'
    datakey = 'SolvingTime'

    solvingtimereadkeys = {
       StatisticReader.SOLVERTYPE_SCIP : "^Solving Time \(sec\) :",
       StatisticReader.SOLVERTYPE_CPLEX : "Solution time =",
       StatisticReader.SOLVERTYPE_GUROBI : "Explored ",
       StatisticReader.SOLVERTYPE_CBC : "Coin:Total time \(CPU seconds\):",
       StatisticReader.SOLVERTYPE_XPRESS : " *** Search ",
       StatisticReader.SOLVERTYPE_COUENNE : "^Total time:"
    }

    solvingtimelineindex = {
       StatisticReader.SOLVERTYPE_SCIP :-1,
       StatisticReader.SOLVERTYPE_CPLEX : 3,
       StatisticReader.SOLVERTYPE_GUROBI :-2,
       StatisticReader.SOLVERTYPE_CBC : 4,
       StatisticReader.SOLVERTYPE_XPRESS : 5,
       StatisticReader.SOLVERTYPE_COUENNE : 2
    }

    def extractStatistic(self, line):
#       print self.solvingtimereadkeys[StatisticReader.solvertype]
        if re.search(self.solvingtimereadkeys[StatisticReader.solvertype], line):
            solvingtime = self.getWordAtIndex(line, self.solvingtimelineindex[StatisticReader.solvertype])
            solvingtime = solvingtime[:solvingtime.find('s')]
            self.testrun.addData(self.problemname, self.datakey, float(solvingtime))

class TimeLimitReader(StatisticReader):
    '''
    extracts the time limit for an instance
    '''
    name = 'TimeLimitReader'
    timelimitreadkeys = {
                   StatisticReader.SOLVERTYPE_SCIP : '(SCIP> limits/time =|SCIP> set limits time)',
                   StatisticReader.SOLVERTYPE_CPLEX : 'CPLEX> New value for time limit in seconds',
                   StatisticReader.SOLVERTYPE_GUROBI : "Changed value of parameter TimeLimit to",
                   StatisticReader.SOLVERTYPE_CBC : "Coin:seconds has value",
                   StatisticReader.SOLVERTYPE_XPRESS : " @05",
                   StatisticReader.SOLVERTYPE_COUENNE : "^@05"}

    datakey = 'TimeLimit'

    def extractStatistic(self, line):
        if re.search(self.timelimitreadkeys[StatisticReader.solvertype], line):
            self.testrun.addData(self.problemname, self.datakey, float(line.split()[-1]))

class TimeToBestReader(StatisticReader):
    name = 'TimeToBestReader'
    regular_exp = re.compile('  Primal Bound     :')
    datakey = 'TimeToBest'
    datatype = float
    lineindex = 3

    def extractStatistic(self, line):
        if self.regular_exp.match(line):
            try:
                self.testrun.addData(self.problemname, self.datakey, float(self.getNumberAtIndex(line, self.lineindex)))
            except TypeError:
                pass

class TimeToFirstReader(StatisticReader):
    name = 'TimeToFirstReader'
    regular_exp = re.compile('  First Solution   :')
    datakey = 'TimeToFirst'
    datatype = float
    lineindex = 3

    def extractStatistic(self, line):
        if self.regular_exp.match(line):
            try:
                timetofirst = float(self.getNumberAtIndex(line, self.lineindex))
                self.testrun.addData(self.problemname, self.datakey, timetofirst)

            except TypeError:
                pass

class ListReader(StatisticReader):
    '''
    reads a list matching a regular expression
    '''
    name = "ListReader"

    def __init__(self, regpattern=None, name=None):
        if regpattern is None:
            raise ValueError("Error: No 'regpattern' specified for reader %s"%str(name))
        self.regular_exp = re.compile(regpattern)
        self.regpattern = regpattern
        if name is None:
            name = ListReader.name
        self.name = name

    def extractStatistic(self, line):
        match = self.regular_exp.match(line)
        if match is not None:
            datakey = match.group(0)
            strval = self.getNumberAtIndex(line, 0)
            try:
                val = int(strval)
            except ValueError:
                val = float(strval)
            self.testrun.addData(self.problemname, datakey, val)


    def getEditableAttributes(self):
        return ['name', 'regpattern']





