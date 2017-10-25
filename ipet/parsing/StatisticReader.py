# -*- coding: utf-8 -*-
"""
The MIT License (MIT)

Copyright (c) 2016 Zuse Institute Berlin, www.zib.de

Permissions are granted as stated in the license file you have obtained
with this software. If you find the library useful for your purpose,
please refer to README.md for how to cite IPET.

@author: Gregor Hendel
"""
import re
from ipet.concepts import IpetNode
from ipet.misc import misc
from ipet import Key
import logging

class StatisticReader(IpetNode):
    """
    base class for all statistic readers - readers should always inherit from this base class for minimal implementation
    effort

    readers only need to overwrite the methods extractStatistic() and perhaps execEndOfProb()
    """

    name = 'NO_NAME_DEFINED_YET'
    regular_exp = re.compile('')
    datakey = 'NO KEY'
    datatype = float
    lineindex = -1

    context = Key.CONTEXT_LOGFILE

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

    @staticmethod
    def boolfunction(value):
        """ parses string TRUE or FALSE and returns the boolean value of this expression """
        return True if value == "TRUE" else False

    @staticmethod
    def changeSolverType(newtype):
        StatisticReader.solvertype = newtype

    def setTestRun(self, testrun):
        self.testrun = testrun

    def supportsContext(self, context):
        """
        returns True if the reader supports a given context, otherwise False
        """
        if type(self.context) is int:
            return self.context == context
        else:
            return context in self.context

    def getSplitLineWithRegexp(self, regular_exp, line, index=-1, startofline=False):
        if startofline == True and not re.match(regular_exp, line):
            return None
        if startofline == False and not re.search(regular_exp, line):
            return None

        if index == -1:
            return line.split()
        else:
            return line.split()[index]

    def getName(self):
        """
        returns the name of the StatisticReader
        """
        return self.name

    def extractStatistic(self, line):
        """
        overwrite this method for own reader subclasses
        """
        try:
            if self.regular_exp.search(line):
                data = None
                try:
                    data = self.datatype(misc.getWordAtIndex(line, self.lineindex))
                except ValueError:
                    data = None
                except IndexError:
                    data = None
                except TypeError:
#                  print self.name, " failed data conversion"
                    raise TypeError("Type error during data conversion in line <%s>" % line)
                self.addData(self.datakey, data)
        except AttributeError:
#          print self.name, " has no such attribute"
            pass

    def execEndOfProb(self):
        """
        overwrite this method to implement final behaviour at the end of each problem, such as setting flags
        """
        return None

    def operateOnLine(self, line):
        self.extractStatistic(line)

    def addData(self, datakey, data):
        logging.debug("Reader %s adds data" % (self.getName()))
        self.testrun.addData(datakey, data)

    def turnIntoFloat(self, astring):
        """
        parses strings to floats, keeps track of trailing caracters signifying magnitudes

        Special attention is put to strings of the form, e.g., '900k' where
        the tailing 'k'-character signifies multiplication by 1000.
        """

        lastelem = astring[-1]
        multiplier = StatisticReader.multipliers.get(lastelem, 1.0)

        return float(astring.rstrip('kMG')) * multiplier

######################################################################################
# DERIVED Classes

class MetaDataReader(StatisticReader):
    context = [Key.CONTEXT_METAFILE, Key.CONTEXT_LOGFILE, Key.CONTEXT_ERRFILE]

    metadataexp = re.compile("^@\S{3,}\s+\S+$")
    name = 'MetaDataReader'
    datakey = Key.MetaData

    def extractStatistic(self, line):
        """ Read metadata from specified line

        Parameters
        ----------
        line
            string to be read from. has to have the form
                @attribute datum
        """
        if self.metadataexp.match(line):
#            TODO better to allow more spaces?
            [attr, datum] = line.split('@')[1].split()
            datum = datum.split('\n')[0]
            self.testrun.metadatadict[attr] = datum

class BestSolInfeasibleReader(StatisticReader):
    """
    catches the expression 'best solution is not feasible in original problem'

    @return: False if above expression is found in the log and the best solution is thus not feasible, otherwise True
    """
    name = 'BestSolInfeasibleReader'
    regular_exp = re.compile('best solution is not feasible in original problem')
    datakey = Key.BestSolutionInfeasible

    def extractStatistic(self, line):
        if self.regular_exp.search(line):
            self.addData(self.datakey, True)

class DateTimeReader(StatisticReader):
    """
    reads in the start and finish time from a timestamp in given in Milliseconds

    If found, the corresponding data keys are Datetime_Start and Datetime_End
    """
    name = 'DateTimeReader'  # : the name for this reader
    datetimestartexp = re.compile(r"^@03 ([0-9]+)")  # : the expression for the date time start
    datetimeendexp = re.compile(r"^@04 ([0-9]+)")  # : the expression for the date time after termination
    datetimestartkey = Key.DatetimeStart  # : data key for start of run
    datetimeendkey = Key.DatetimeEnd  # : data key for end of run

    datetimekw = {datetimestartkey:datetimestartexp, datetimeendkey:datetimeendexp}

    def extractStatistic(self, line):
        for key, exp in list(self.datetimekw.items()):
            matched = exp.match(line)
            if matched:
                timestamp = int(matched.groups()[0])
                #time = misc.convertTimeStamp(timestamp)
                self.addData(key, timestamp)
                break

class DualLPTimeReader(StatisticReader):
    """
    reads the dual LP time
    """
    name = 'DualLPTimeReader'
    regular_exp = re.compile('^  dual LP')
    datakey = Key.DualLpTime
    datatype = float
    lineindex = 3

class ErrorFileReader(StatisticReader):
    """
    reads information from error files
    """
    name = "ErrorFileReader"
    regular_exp = re.compile("returned with error code (\d+)")
    datakey = Key.ErrorCode
    context = Key.CONTEXT_ERRFILE

    def extractStatistic(self, line):
        match = self.regular_exp.search(line)
        if match:
            returncode = match.groups()[0]
            self.addData(self.datakey, int(returncode))

class SettingsFileReader(StatisticReader):
    """
    parses settings from a settings file

    parses the type, the default value, the name and the current value for every parameter
    # [type: int, range: [-536870912,536870911], default: 100000]
    nodeselection/bfs/stdpriority = 1000000
    """
    name = "SettingsFileReader"
    regular_exp_name = re.compile("^([\w/]+) = (.+)")
    regular_exp_type = re.compile("^# \[type: (\w+),.*default: ([^\]]+)\]")
    context = Key.CONTEXT_SETFILE

    typemap = {
               "real" : float,
               "char" : str,
               "string" : str,
               "int" : int,
               "bool" : StatisticReader.boolfunction,
               "longint" : int
               }
    """ map from a parameter type to a python standard data type """

    def extractStatistic(self, line):
        match_type = self.regular_exp_type.match(line)
        if match_type:
            self.type = match_type.groups()[0]
            self.default = match_type.groups()[1]
        else:
            match_name = self.regular_exp_name.match(line)
            if match_name:
                name = match_name.groups()[0]
                value = match_name.groups()[1]
                typefunction = self.typemap.get(self.type, str)
                try:
                    self.testrun.addParameterValue(name, typefunction(value))
                    self.testrun.addDefaultParameterValue(name, typefunction(self.default))
                except ValueError:
                    # when an error occurs, just return a string
                    self.testrun.addParameterValue(name, value)
                    self.testrun.addDefaultParameterValue(name, self.default)

class GapReader(StatisticReader):
    """
    reads the primal dual gap at the end of the solving
    """
    name = 'GapReader'
    regular_exp = re.compile('^Gap                :')
    datakey = Key.Gap
    datatype = float
    lineindex = 2

    def extractStatistic(self, line):
        if self.regular_exp.match(line):
            gapasword = misc.getWordAtIndex(line, self.lineindex)

            # if the gap is infinite, no data is passed to the test run
            if gapasword != "infinite":
                gap = self.turnIntoFloat(gapasword)
                self.addData(self.datakey, gap)

class MaxDepthReader(StatisticReader):
    """
    reads the maximum depth
    """
    name = 'MaxDepthReader'
    regular_exp = re.compile('  max depth        :')
    datakey = Key.MaximumDepth
    datatype = int
    lineindex = 3

class NodesReader(StatisticReader):
    """
    reads the total number of solving nodes of the branch and bound search
    """
    name = 'NodesReader'
    regular_exp = re.compile("^  nodes \(total\)    :")
    datakey = Key.Nodes
    datatype = int
    lineindex = 3

class ObjsenseReader(StatisticReader):
    name = 'ObjsenseReader'
    regular_exp = re.compile("^  Objective        : (\w*),")
    datakey = Key.ObjectiveSense
    minimize = 1
    maximize = -1

    def extractStatistic(self, line):
        match = self.regular_exp.match(line)

        if match:
            objsense = self.minimize
            if match.groups()[0] == "maximize":
                objsense = self.maximize

            self.addData(self.datakey, objsense)

class ObjlimitReader(StatisticReader):
    name = "ObjlimitReader"
    regular_exp = re.compile("objective value limit set to")
    datakey = Key.ObjectiveLimit
    datatype = float
    lineindex = 5

class RootNodeFixingsReader(StatisticReader):
    """
    reads the number of variable fixings during root node
    """
    name = 'RootNodeFixingsReader'
    regular_exp = re.compile('^  root node')
    datakey = Key.RootNodeFixings
    datatype = int
    lineindex = 4

class TimeLimitReader(StatisticReader):
    """
    extracts the time limit for a problem
    """
    name = 'TimeLimitReader'
    timelimitreadkeys = {
                   StatisticReader.SOLVERTYPE_SCIP : 'limits/time',
                   StatisticReader.SOLVERTYPE_CPLEX : '@05',
                   StatisticReader.SOLVERTYPE_GUROBI : "@05",
                   StatisticReader.SOLVERTYPE_CBC : "@05",
                   StatisticReader.SOLVERTYPE_XPRESS : "@05",
                   StatisticReader.SOLVERTYPE_COUENNE : "^@05"}

    datakey = Key.TimeLimit

    def extractStatistic(self, line):
        if re.search(self.timelimitreadkeys[StatisticReader.solvertype], line):
            self.addData(self.datakey, float(line.split()[-1]))

class TimeToBestReader(StatisticReader):
    name = 'TimeToBestReader'
    regular_exp = re.compile('  Primal Bound     :')
    datakey = Key.TimeToBestSolution
    datatype = float
    lineindex = 3

    def extractStatistic(self, line):
        if self.regular_exp.match(line):
            try:
                self.addData(self.datakey, float(misc.getNumberAtIndex(line, self.lineindex)))
            except TypeError:
                pass

class TimeToFirstReader(StatisticReader):
    name = 'TimeToFirstReader'
    regular_exp = re.compile('  First Solution   :')
    datakey = Key.TimeToFirstSolution
    datatype = float
    lineindex = 3

    def extractStatistic(self, line):
        if self.regular_exp.match(line):
            try:
                timetofirst = float(misc.getNumberAtIndex(line, self.lineindex))
                self.addData(self.datakey, timetofirst)

            except TypeError:
                pass

class ListReader(StatisticReader):
    """
    reads a list matching a regular expression
    """
    name = "ListReader"

    def __init__(self, regpattern=None, name=None):
        """
        construct a new list reader to parse key-value pairs from a given context

        List readers parse key-value pairs of the form

        (regpattern-match 1) value
        (regpattern-match 2) value
        (regpattern-match 3) value

        The matching regpattern is used as data key

        Parameters:
        -----------

        regpattern : a pattern (regular expression supported) that suitable lines must match

        name : a name for this reader
        """
        if regpattern is None:
            raise ValueError("Error: No 'regpattern' specified for reader %s" % str(name))
        self.regular_exp = re.compile(regpattern)
        self.regpattern = regpattern
        if name is None:
            name = ListReader.name
        self.name = name

    def getEditableAttributes(self):
        return ["name", "regpattern"]

    def set_context(self, contextname):
        self.context = self.contextname2contexts.get(contextname, self.context)

    def getRequiredOptionsByAttribute(self, attr):
        if attr == "context":
            return list(self.contextname2contexts.keys())
        return None

    def getLineData(self, line):
        match = self.regular_exp.match(line)
        if match is not None:
            datakey = match.group(1)
            strval = match.group(2)
            try:
                val = int(strval)
            except ValueError:
                val = float(strval)
            return (datakey, val)
        return None

    def extractStatistic(self, line):
        data = self.getLineData(line)
        if data is not None:
            self.addData(data[0], data[1])
