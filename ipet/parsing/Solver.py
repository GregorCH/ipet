
import re
import os
from ipet import Key
from ipet.misc import misc
from operator import itemgetter
from builtins import int, str
import logging
from numpy import char

class Solver():
    """ The solver-class acts as Reader for solver-specific data.

    After being fed the out-file line by line to readLine(line)
    the solver can return the collected data via getData().
    When reading multiple runs, the solver has to be reset via reset().

    This class has to be inherited by a SpecificSolver-class and
    should not be used as it is.
    """

    DEFAULT = None
    solverId = "defaultSolver"
    recognition_expr = None
    primalbound_expr = None
    dualbound_expr = None
    solvingtime_expr = None
    version_expr = None
    nodes_expr = None
    violbound_expr = None
    violint_expr = None
    viollp_expr = None
    violcons_expr = None

    solverstatusmap = {}

    objsensemap = {}

    def __init__(self,
                 solverId = None,
                 recognition_pattern = None,
                 primalbound_pattern = None,
                 dualbound_pattern = None,
                 solvingtime_pattern = None,
                 version_pattern = None,
                 solverstatusmap = None,
                 nodes_pattern = None,
                 violbound_pattern = None,
                 violint_pattern = None,
                 viollp_pattern = None,
                 violcons_pattern = None,
                 objsensemap = None):

        if solverId is not None:
            self.solverId = solverId

        if not recognition_pattern is None:
            self.recognition_expr = re.compile(recognition_pattern)
        if not primalbound_pattern is None:
            self.primalbound_expr = re.compile(primalbound_pattern)
        if not dualbound_pattern is None:
            self.dualbound_expr = re.compile(dualbound_pattern)
        if not solvingtime_pattern is None:
            self.solvingtime_expr = re.compile(solvingtime_pattern)
        if not version_pattern is None:
            self.version_expr = re.compile(version_pattern)
        if nodes_pattern is not None:
            self.nodes_expr = re.compile(nodes_pattern)
        if violbound_pattern is not None:
            self.violbound_expr = re.compile(violbound_pattern)
        if violint_pattern is not None:
            self.violint_expr = re.compile(violint_pattern)
        if viollp_pattern is not None:
            self.viollp_expr = re.compile(viollp_pattern)
        if violcons_pattern is not None:
            self.violcons_expr = re.compile(violcons_pattern)
        if objsensemap is not None:
            self.objsensemap = objsensemap


        if solverstatusmap is not None:
            self.solverstatusmap = solverstatusmap
        self.solverstatusses = sorted(self.solverstatusmap.items(), key = itemgetter(1))

        # compile the solver status patterns
        self.solverstatusses = [(re.compile(pattern), status) for pattern, status in self.solverstatusses]


        self.data = {}
        self.reset()

    def extractStatus(self, line : str):
        """ Check if the line matches one of the solverstatusmap patterns.

        If the one of the patterns matches, the data will be added data as Key.SolverStatus.
        """
        for expr, status in self.solverstatusses:
            if expr.match(line):
                self.addData(Key.SolverStatus, status)
                # break in order to prevent parsing a weaker status
                break

    def extractVersion(self, line : str):
        """ Extract the version of the solver-software.

        If the versionpattern matches, the version will be added to data as Key.Version.
        """
        self.extractByExpression(line, self.version_expr, Key.Version, str)

    def extractSolvingTime(self, line : str):
        """ Read the overall solving time given by the solver.

        If the solvingpatterns matches, the version will be added to data as Key.SolvingTime.
        """
        self.extractByExpression(line, self.solvingtime_expr, Key.SolvingTime)

    def extractDualbound(self, line : str):
        """Return the reported dual bound (at the end of the solver-output)
        """
        self.extractByExpression(line, self.dualbound_expr, Key.DualBound)

    def extractPrimalbound(self, line : str):
        """Read the primal bound (at the end of the solver-output)
        """
        self.extractByExpression(line, self.primalbound_expr, Key.PrimalBound)

    def extractViolbound(self, line : str):
        """Read the bound violation (at the end of the solver-output)
        """
        self.extractByExpression(line, self.violbound_expr, Key.ViolationBds)

    def extractViolint(self, line : str):
        """Read the integrality violation (at the end of the solver-output)
        """
        self.extractByExpression(line, self.violint_expr, Key.ViolationInt)

    def extractViollp(self, line : str):
        """Read the LP violation (at the end of the solver-output)
        """
        self.extractByExpression(line, self.viollp_expr, Key.ViolationLP)

    def extractViolcons(self, line : str):
        """Read the constraint violation (at the end of the solver-output)
        """
        self.extractByExpression(line, self.violcons_expr, Key.ViolationCons)

    def extractNodes(self, line : str):
        """Read the number of branch and bound nodes
        """
        self.extractByExpression(line, self.nodes_expr, Key.Nodes, int)

    def extractObjsense(self, line : str):
        """Read objective sense of the problem as understood by the solver
        """
        for pattern, sense in self.objsensemap.items():
            if re.match(pattern, line):
                self.addData(Key.ObjectiveSense, sense)

    def extractByExpression(self, line : str, expr, key : str, datatype : type = float) -> None:
        """
        Search for regular expression 'expr' and store a possible match under the given 'key'.

        Parameters
        ----------
        line
            a line of solver output
        expr
            regular expression with (at least) one group
        key
            data key to store datum after a match
        datatype
            data type for the datum, default : float
        """
        if expr is None:
            return

        m = expr.match(line)
        if m is not None:
            try:
                d = datatype(m.groups()[0])
                self.addData(key, d)
            except:
                pass

    def addData(self, key, datum):
        """Add data to local data-dictionary

        Parameters
        ----------
        key
            string (or int or float) that acts as key for datum in data dictionary
        datum
            the datum which shoul dbe saved
        """
        self.data[key] = datum

    def deleteData(self, key : str):
        """Delete data from local data dictionary
        """
        if key in self.data:
            del self.data[key]


    def addHistoryData(self, key, timestr : str, boundstr : str):
        """Add data to local historydata dictionary.

        Parameters
        ----------
        timestr
            string containing time
        boundstr
            string containing bound that should be saved
        """
        try:
            time = float(timestr)
            bound = float(boundstr)
        except:
            return
        history = self.data.setdefault(key, [])
        # only append newly found bounds

        logging.debug("pointinTime %s, bound %s, key %s \n" % (timestr, boundstr, key))
        if history == [] or history[-1][1] != bound:
            if(key == Key.PrimalBoundHistory):
                history.append((time, bound))
            elif (key == Key.DualBoundHistory) and (history == [] or history[-1][0] != time):
                history.append((time, bound))
            elif (key == Key.DualBoundHistory and history[-1][0] == time):
                history.pop(-1)
                history.append((time, bound))

    def readLine(self, line : str):
        """Read solver-specific data from that lin

        Parameters
        ----------
        line
            a line of solver output that the information shall be read frome
        """
        self.extractElementaryInformation(line)
        self.extractOptionalInformation(line)
        self.extractGeneralInformation(line)

    def extractElementaryInformation(self, line : str):
        """Read Data that is needed for validation

        Parameters
        ----------
        line
            a line of solver output that the information shall be read from
        """
        self.extractPrimalbound(line)
        self.extractDualbound(line)
        self.extractSolvingTime(line)
        self.extractNodes(line)
        self.extractViolbound(line)
        self.extractViolint(line)
        self.extractViollp(line)
        self.extractViolcons(line)
        self.extractVersion(line)
        self.extractStatus(line)
        self.extractHistory(line)
        self.extractObjsense(line)

    def extractHistory(self, line):
        """ Extract the sequence of primal and dual bounds.

        Parameters
        ----------
        line
            a line of solver output that the information shall be read from
        """
        self.extractPrimalboundHistory(line)
        self.extractDualboundHistory(line)

    def extractPrimalboundHistory(self, line : str):
        """ Extract the sequence of primal bounds.

        Parameters
        ----------
        line
            a line of solver output that the information shall be read from
        Method has to be overwritten.
        """
        pass

    def extractDualboundHistory(self, line : str):
        """ Extract the sequence of dual bounds.

        Parameters
        ----------
        line
            a line of solver output that the information shall be read from
        Method should be overwritten.
        """
        pass

    # This method should be overwritten by subclasses
    def extractOptionalInformation(self, line : str):
        """Read optional data

        Parameters
        ----------
        line
            a line of solver output that the information shall be read from
        """
        pass

    def extractGeneralInformation(self, line : str):
        """Read general data

        Parameters
        ----------
        line
            a line of solver output that the information shall be read from
        """
        pass

    def reset(self):
        """Reset all Data except the solverId
        """
        self.data = {}
        self.addData(Key.Solver, self.solverId)
        self.addData(Key.SolverStatus, Key.SolverStatusCodes.Crashed)
        #        TODO how does the historydata work ?
        self.data.setdefault(Key.PrimalBoundHistory, [])
        self.data.setdefault(Key.DualBoundHistory, [])

    def recognizeOutput(self, line : str) -> bool:
        """ decide if line was created by the current solver

        Parameters
        ----------
        line
            a line of solver output that the information shall be read from
        """
        return self.recognition_expr.match(line) != None

    def getData(self, datakey = None):
        """Return data stored under datakey

        Or return collected data as a tuple of two generators
        """
        if datakey is None:
            return map(list, zip(*self.data.items()))
        else:
            return self.data.get(datakey)

    def getName(self) -> str:
        """ Return the name of current solver instance
        """
        return self.solverId

    def isSolverInstance(self, filecontext : str) -> bool:
        """ Decide if filecontext is (solver specific) logfile or errorfile.
        """
        return filecontext in [Key.CONTEXT_ERRFILE, Key.CONTEXT_LOGFILE]

    # Helper for primalboundhistory-reading
    def readBoundAndTime(self, line : str, boundidx : int, timeidx : float, timestripchars : char = "", cutidx : int = -1):
        """ Read and save bound and time

        Parameters
        ----------
        line
            a line of solver output that the information shall be read from
        """
        splitline = line.split()
        primalbound = line[:cutidx].split()[boundidx]
        pointInTime = splitline[timeidx].strip(timestripchars)
        self.addHistoryData(Key.PrimalBoundHistory, pointInTime, primalbound)

    def readBoundAndTimeDual(self, line: str, boundidx: int, timeidx: float, timestripchars: char = "", cutidx: int = -1):
        """ Read and save bound and time

        Parameters
         ----------
        line
         a line of solver output that the information shall be read from
        """
        splitline = line.split()
        dualbound = line[:cutidx].split()[boundidx]
        pointInTime = splitline[timeidx].strip(timestripchars)
        self.addHistoryData(Key.DualBoundHistory, pointInTime, dualbound)

###############################################################
##################### DERIVED Classes #########################
###############################################################

class SCIPSolver(Solver):

    solverId = "SCIP"
    recognition_expr = re.compile("^SCIP version ")
    primalbound_expr = re.compile("^Primal Bound       : (\S+)")
    dualbound_expr = re.compile("^Dual Bound         : (\S+)")
    solvingtime_expr = re.compile("^Solving Time \(sec\) : (\S+)")
    version_expr = re.compile("SCIP version (\S+)")
    limitreached_expr = re.compile("((?:^SCIP Status        :)|(?:\[(?:.*) (reached|interrupt)\]))")
    nodes_expr = re.compile("  nodes \(total\)    : *(\d+) \(")
    extrasol_expr = re.compile("^feasible solution found .* after (.*) seconds, objective value (\S*)")
    soplexgithash_expr = re.compile("^  SoPlex .+\[GitHash: (\S+)\]")
    violbound_expr = re.compile("^  bounds           : \S+ (\S+)$")
    violint_expr = re.compile("^  integrality      : (\S+)")
    viollp_expr = re.compile("^  LP rows          : \S+ (\S+)$")
    violcons_expr = re.compile("^  constraints      : \S+ (\S+)$")

    # variables needed for primal bound history
    primalboundhistory_exp = re.compile('^\s+time\s+\| .* \|\s+primalbound\s+\|\s+gap')
    heurdispcharexp = re.compile('^[^ \d]')
    """ all lines starting with a non-whitespace and non-digit character """

    shorttablecheckexp = re.compile('s\|')
    firstsolexp = re.compile('^  First Solution   :')

    # variables needed for dual bound history
    regular_exp = re.compile('\|')  # compile the regular expression to speed up reader

    solverstatusmap = {
        "no problem exists" : Key.SolverStatusCodes.Readerror,
        "SCIP Status        : problem is solved \[optimal solution found\]":Key.SolverStatusCodes.Optimal,
        "SCIP Status        : problem is solved \[infeasible\]": Key.SolverStatusCodes.Infeasible,
        "SCIP Status        : problem is solved \[infeasible or unbounded\]": Key.SolverStatusCodes.InfOrUnbounded,
        "SCIP Status        : solving was interrupted \[time limit reached\]" : Key.SolverStatusCodes.TimeLimit,
        "SCIP Status        : solving was interrupted \[memory limit reached\]" : Key.SolverStatusCodes.MemoryLimit,
        "SCIP Status        : solving was interrupted \[node limit reached\]" : Key.SolverStatusCodes.NodeLimit,
        "SCIP Status        : solving was interrupted \[gap limit reached\]" : Key.SolverStatusCodes.GapLimit,
        "SCIP Status        : solving was interrupted" : Key.SolverStatusCodes.Interrupted,
    }

    def __init__(self, **kw):
        super(SCIPSolver, self).__init__(**kw)

    def reset(self):
        """ reset stored data
        """
        Solver.reset(self)
        # variables needed for dual bound history
        self.lastdualbound = misc.FLOAT_INFINITY
        self.lasttime = -1
        self.dualboundindex = -1

    def extractPrimalboundHistory(self, line : str):
        """ Extract the sequence of primal bounds
        """

        #
        # check if an additional line is printed for a feasible solution before presolving
        #
        extrasolmatch = self.extrasol_expr.match(line)
        if extrasolmatch:
            pointInTime, PrimalBound = extrasolmatch.groups()
            # store newly found (time, primal bound) tuple if it differs from the last primal bound
            self.addHistoryData(Key.PrimalBoundHistory, pointInTime, PrimalBound)
            return
        elif not self.isTableLine(line):
            return

        # history reader should be in a table. check if a display char indicates a new primal bound
        if self.heurdispcharexp.match(line):

            allmatches = misc.numericExpression.findall(line[:line.rindex("|")])

            if len(allmatches) == 0:
                return

            pointInTime = allmatches[0]
            PrimalBound = allmatches[-1]
            # in the case of ugscip, we reacted on a disp char, so no problem at all.
            self.addHistoryData(Key.PrimalBoundHistory, pointInTime, PrimalBound)


    def extractDualboundHistory(self, line : str):
        """ Extract the sequence of dual bounds
        """
        timeindex = 0

        if not self.isTableLine(line):
            return

        try:
            # TODO This works, why is eclipse complaining?
            lineelems = misc.tablenumericExpression.findall(line)
            # parse time and dual bound from the table
            time = lineelems[timeindex]
            dualbound = lineelems[self.dualboundindex]

            # store newly found (time, dual bound) tuple if it differs from the last dual bound
            self.addHistoryData(Key.DualBoundHistory, time, dualbound)

        except ValueError:
            return None
        except IndexError:
            return None

    def isTableLine(self, line : str) -> bool:
        """ decide if line is a data line of the table
        """
        if self.primalboundhistory_exp.match(line):
            columnheaders = list(map(str.strip, line.split('|')))
            self.dualboundindex = columnheaders.index('dualbound')
            return True
        elif self.shorttablecheckexp.search(line):
            return True
        return False

    def extractMoreData(self, line : str):
        """Handle more than just the version
        """
        for keyword in ["mode", "LP solver", "GitHash"]:
            data = re.search(r"SCIP.*\[%s: ([\w .-]+)\]" % keyword, line)
            if data:
                self.addData(keyword if keyword != "LP solver" else "LPSolver", data.groups()[0])
        soplexhashmatch = self.soplexgithash_expr.match(line)
        if soplexhashmatch:
            self.addData("SpxGitHash", soplexhashmatch.groups()[0])

    def extractPath(self, line : str):
        """Extract the path info
        """
        if line.startswith('loaded parameter file'):
            absolutesettingspath = line[len('loaded parameter file '):].strip('<>')
            self.addData(Key.SettingsPathAbsolute, absolutesettingspath)
            settings = os.path.basename(absolutesettingspath)
            settings = os.path.splitext(settings)[0]

    def extractOptionalInformation(self, line : str):
        """Extract the path info
        """
        self.extractPath(line)
        self.extractMoreData(line)

class FiberSCIPSolver(SCIPSolver):
    """Reads data from FiberSCIP output, that ressembles SCIP output a lot, except for the table.
    """
    solverId = "FiberSCIP"
    recognition_expr = re.compile("^The following solver is parallelized by UG")
    primalbound_expr = re.compile("^  Primal Bound     : (\S+)")
    dualbound_expr = re.compile("^  Dual Bound       : (\S+)")
    solvingtime_expr = re.compile("^Total Time         : (\S+)")
    version_expr = re.compile("^The following solver is parallelized by UG version (\S+)")
    nodes_expr = re.compile("  nodes \(total\)    : *(\d+)")

    # variables needed for primal bound history
    heurdispcharexp = re.compile('^\* ')
    """ all lines starting with a single (!!!) asterisk. UG sometimes prints double asterisks """

    ugtableexp = re.compile('^\s+Time\s+Nodes')

    solverstatusmap = {
        "SCIP Status        : problem is solved" : Key.SolverStatusCodes.Optimal,
        "SCIP Status        : solving was interrupted \[ hard time limit reached \]" : Key.SolverStatusCodes.TimeLimit,
    }

    def __init__(self, **kw):
        super(FiberSCIPSolver, self).__init__(**kw)


    def isTableLine(self, line : str) -> bool:
        if self.ugtableexp.match(line):
            return True
        elif self.heurdispcharexp.match(line):
            return True
        return False

    def extractPrimalboundHistory(self, line : str):
        """ Extract the sequence of primal bounds
        """

        if not self.isTableLine(line):
            return

        # history reader should be in a table. check if a display char indicates a new primal bound
        if self.heurdispcharexp.match(line):
            allmatches = misc.numericExpression.findall(line)[:5]

            if len(allmatches) == 0:
                return

            pointInTime = allmatches[0]
            PrimalBound = allmatches[-1]
            # in the case of ugscip, we reacted on a disp char, so no problem at all.
            self.addHistoryData(Key.PrimalBoundHistory, pointInTime, PrimalBound)

    def extractDualboundHistory(self, line : str):
        """Do not read a dual bound history, override method in SCIP solver

        There is no simple way to distinguish UG table lines from other output unless the primal bound changes.
        """
        pass

class GurobiSolver(Solver):

    solverId = "GUROBI"
    recognition_expr = re.compile("Gurobi Optimizer version")
    primalbound_expr = re.compile("^(?:Best|Optimal) objective ([^\s,]*)")
    dualbound_expr = re.compile("^(?:Best objective \S+, best bound|Optimal objective) ([^\s,]+),*")
    solvingtime_expr = re.compile("^(?:Explored \d* nodes .* in|Solved in .* iterations and) (\S*) seconds")
    version_expr = re.compile("Gurobi Optimizer version (\S+)")
    nodes_expr = re.compile("Explored (\d+) nodes")

    solverstatusmap = {"(Optimal solution found|Solved with barrier)" : Key.SolverStatusCodes.Optimal,
                       "Model is infeasible" : Key.SolverStatusCodes.Infeasible,
                        "Time limit reached" : Key.SolverStatusCodes.TimeLimit,
                        "^(ERROR 10001|Out of memory)" : Key.SolverStatusCodes.MemoryLimit,
#                       "" : Key.SolverStatusCodes.NodeLimit,
#                       "" : Key.SolverStatusCodes.Interrupted
                        "^ERROR 10003" : Key.SolverStatusCodes.Readerror,
                        "^Model is unbounded" : Key.SolverStatusCodes.Unbounded
                       }

    # variables needed for bound history
    inTable = False
    gurobiextralist = []

    def __init__(self, **kw):
        super(GurobiSolver, self).__init__(**kw)

    def extractPrimalboundHistory(self, line : str):
        """ Extract the sequence of primal bounds
        """
        if "Found heuristic solution" in line:
            self.gurobiextralist.append(line.split()[-1])
        if "Expl Unexpl |  Obj  Depth" in line:
            self.inTable = True
        elif self.inTable and line.endswith("s\n") and self.gurobiextralist != []:
            pointInTime = line.split()[-1].strip("s")
            self.addHistoryData(Key.PrimalBoundHistory, pointInTime, self.gurobiextralist[-1])
            self.gurobiextralist = []
        elif self.inTable and line.startswith("H") or line.startswith("*"):
            self.readBoundAndTime(line, -5, -1, timestripchars = "s")

        elif "Cutting planes:" in line and self.inTable:
            self.inTable = False
        elif self.gurobiextralist != [] and "Explored " in line:
            pointInTime = line.split()[-2]
            self.addHistoryData(Key.PrimalBoundHistory, pointInTime, self.gurobiextralist[-1])
            self.gurobiextralist = []
        if "Explored " in line and "simplex iterations" in line:
            self.inTable = False
        return None

    def extractDualboundHistory(self, line : str):
        """ Extract the sequence of dual bounds
        """
        if "Expl Unexpl |  Obj  Depth" in line:
            self.inTable = True
        elif self.inTable and line.endswith("s\n"):
            self.readBoundAndTimeDual(line, -4, -1, timestripchars = "s")

        elif "Cutting planes:" in line and self.inTable:
            self.inTable = False
        if "Explored " in line and "simplex iterations" in line:
            self.inTable = False
        if self.gurobiextralist != [] and "Explored " in line:
            pointInTime = line.split()[-2]
            self.addHistoryData(Key.DualBoundHistory, pointInTime, self.gurobiextralist[-1])
            self.gurobiextralist = []
        return None

    def extractOptionalInformation(self, line : str):
        if "Explored " in line and "simplex iterations" in line:
            nnodes = line.split()[1]
            self.addData('Nodes', int(nnodes))
        return None

class CplexSolver(Solver):

    solverId = "CPLEX"
    recognition_expr = re.compile("^Welcome to IBM\(R\) ILOG\(R\) CPLEX\(R\) Interactive Optimizer")
    primalbound_expr = re.compile("^MIP -.*Objective =\s*(\S+)")
    dualbound_expr = re.compile("^(?:Current MIP best bound|^MIP - Integer optimal solution:  Objective) =\s*(\S+)")
    solvingtime_expr = re.compile("Solution time =\s*(\S+)")
    version_expr = re.compile("^Welcome to IBM\(R\) ILOG\(R\) CPLEX\(R\) Interactive Optimizer (\S+)")
    nodes_expr = re.compile("Solution time = .* sec\.  Iterations = \d+  Nodes = (\S+)")


    elapsedtime_expr = re.compile("^Elapsed time = .+ sec. \(.* ticks, tree = .* MB, solutions = \d+\)")

    solverstatusmap = {"MIP - Integer optimal" : Key.SolverStatusCodes.Optimal,
                       "MIP - Integer infeasible." : Key.SolverStatusCodes.Infeasible,
                       "MIP - Time limit exceeded" : Key.SolverStatusCodes.TimeLimit,
                       "MIP - Integer unbounded" : Key.SolverStatusCodes.Unbounded,
                       "CPLEX Error  1001: Out of memory\." : Key.SolverStatusCodes.MemoryLimit,
                       "No file read\." : Key.SolverStatusCodes.Readerror,

                       #                       "" : Key.SolverStatusCodes.NodeLimit,
                       #                       "" : Key.SolverStatusCodes.Interrupted
                       }

    objsensemap = {
        "^CPLEX> Problem is a minimization problem" : Key.ObjectiveSenseCode.MINIMIZE,
        "^CPLEX> Problem is a maximization problem" : Key.ObjectiveSenseCode.MAXIMIZE,
        }

    # variables needed for primal bound history extraction
    easyCPLEX = False
    lastelapsedtime = 0.0
    nnodessincelastelapsedtime = 0
    lastnnodes = 0
    cpxprimals = []
    inTable = False

    def __init__(self, **kw):
        super(CplexSolver, self).__init__(**kw)

    def extractOptionalInformation(self, line):
        """Extract the settings
        """
        self.extractSettings(line)

    def extractSettings(self, line):
        """Extract the settings
        """
        if "CPLEX> Non-default parameters written to file" in line:
            self.addData(Key.Settings, line.split('.')[-3])

    # TODO DualBoundHistory
    def extractPrimalboundHistory(self, line : str):
        """ Extract the sequence of primal bounds
        """
        if self.easyCPLEX and "Found incumbent of value" in line:
            splitline = line.split()
            self.readBoundAndTime(line, splitline.index("Found") + 4, splitline.index("Found") + 6)
        elif not self.easyCPLEX:
            if "Welcome to IBM(R) ILOG(R) CPLEX(R)" in line:
                self.lastelapsedtime = 0.0
                self.nnodessincelastelapsedtime = 0
                self.lastnnodes = 0
                self.cpxprimals = []
            if "   Node  Left     Objective  IInf  Best Integer    Best Bound    ItCnt     Gap" in line:
                self.inTable = True
            elif self.inTable and ("cuts applied:" in line or "Root node processing" in line):
                self.inTable = False
            elif self.inTable and "Repeating presolve." in line:
                self.inTable = False
            elif self.inTable and len(line) > 0 and (line.startswith(" ") or line.startswith("*")):
                if line == "\n":
                    return None
                nodeinlineidx = 7
                while line[nodeinlineidx] != " " and line[nodeinlineidx] != "+":
                    nodeinlineidx += 1
                nnodes = int(line[:nodeinlineidx].split()[-1].strip('*+')) + 1
                if line.startswith("*"):
                    if '+' in line:
                        primalbound = line.split()[-3]
                    else:
                        primalbound = line.split()[-4]
                    self.cpxprimals.append((nnodes, primalbound))
                self.lastnnodes = nnodes
            elif self.elapsedtime_expr.match(line):
                thetime = float(line.split()[3])
                self.processCpxprimals(thetime)

                self.nnodessincelastelapsedtime = self.lastnnodes
                self.lastelapsedtime = thetime

            elif "Solution time =" in line:
                thetime = float(line.split()[3])
                self.processCpxprimals(thetime)

    def processCpxprimals(self, currenttime):
        solvednodes = (self.lastnnodes - self.nnodessincelastelapsedtime)
        timespentonnode = (currenttime - self.lastelapsedtime) / max(1.0, float(solvednodes))
        assert currenttime >= self.lastelapsedtime
        for node, bound in self.cpxprimals:
            estimatedtime = self.lastelapsedtime + (node - self.nnodessincelastelapsedtime) * timespentonnode
            self.addHistoryData(Key.PrimalBoundHistory, estimatedtime, bound)

        self.cpxprimals = []

class CbcSolver(Solver):

    solverId = "CBC"
    recognition_expr = re.compile("Welcome to the CBC MILP Solver")
    primalbound_expr = re.compile("^Objective value:\s*(\S*)")
    dualbound_expr = re.compile("^(?:Lower bound\s*|Objective value\s*):\s*(\S*)")
    solvingtime_expr = re.compile("Total time \(CPU seconds\):\s*(\S*)")
    version_expr = re.compile("^Version: (\S+)")
    nodes_expr = re.compile("^Enumerated nodes: *(\S+)")

    solverstatusmap = {"Result - Optimal solution found" : Key.SolverStatusCodes.Optimal,
                       "Result - Stopped on time limit" : Key.SolverStatusCodes.TimeLimit,
                       "Result - Problem proven infeasible" : Key.SolverStatusCodes.Infeasible,
                       "\*\* Current model not valid" : Key.SolverStatusCodes.Readerror
                       #                       "" : Key.SolverStatusCodes.MemoryLimit,
                       #                       "" : Key.SolverStatusCodes.NodeLimit,
                       #                       "" : Key.SolverStatusCodes.Interrupted
                       }

    def __init__(self, **kw):
        super(CbcSolver, self).__init__(**kw)

    def extractPrimalboundHistory(self, line : str):
        """ Extract the sequence of primal bounds
        """
        if "Integer solution of " in line:
            self.readBoundAndTime(line, 4, -2, timestripchars = "(")
        return None

class XpressSolver(Solver):

    solverId = "XPRESS"
    recognition_expr = re.compile("FICO Xpress-Optimizer")
    primalbound_expr = re.compile("Objective value =\s*(\S*)")
    dualbound_expr = re.compile("Best Bound =\s*(\S*)")
    solvingtime_expr = re.compile(" \*\*\* Search.*\*\*\*\s*Time:\s*(\S*)")
    version_expr = re.compile("FICO Xpress-Optimizer \S* v(\S*)")
    nodes_expr = re.compile("^Nodes explored = (.*)$")


    # TODO does this work? Benchmarks seem to be broken
    solverstatusmap = {r"Best integer solution found" : Key.SolverStatusCodes.Optimal,
                       "Problem is integer infeasible" : Key.SolverStatusCodes.Infeasible,
                       "STOPPING - MAXTIME limit reached" : Key.SolverStatusCodes.TimeLimit,
                       "\?(45|20)" : Key.SolverStatusCodes.MemoryLimit,
                       #                       "" : Key.SolverStatusCodes.NodeLimit,
                       r" \*\*\* Search unfinished \*\*\*" : Key.SolverStatusCodes.Interrupted,
                      r"\?(66|1038|1039)" : Key.SolverStatusCodes.Readerror
                       }

    objsensemap = {
            "^Minimizing MILP" : Key.ObjectiveSenseCode.MINIMIZE,
            "^Maximizing MILP" : Key.ObjectiveSenseCode.MAXIMIZE,
        }

    # variables needed for primal bound history extraction
    xpresscutidx = -1

    def __init__(self, **kw):
        super(XpressSolver, self).__init__(**kw)

    def extractPrimalboundHistory(self, line : str):
        """ Extract the sequence of primal bounds
        """
        if "BestSoln" in line:
            self.xpresscutidx = line.index("BestSoln") + len("BestSoln")
        elif re.search("^[a-zA-Z*](\d| )", line):
            self.readBoundAndTime(line, -1, -1, cutidx = self.xpresscutidx)
        elif line.startswith(" \*\*\* Heuristic solution found: "):
            self.readBoundAndTime(line, -4, -2)

    def extractStatus(self, line:str):
        if self.getData(Key.SolverStatus) in [Key.SolverStatusCodes.Crashed, Key.SolverStatusCodes.Optimal]:
            Solver.extractStatus(self, line)

# class CouenneSolver(Solver):
#
#    # TODO fix regexes to contain groups which can extract numbers, test, etc
#    solverID = "Couenne"
#    recognition_expr = re.compile("Couenne  --  an Open-Source solver for Mixed Integer Nonlinear Optimization")
#    primalbound_expr = re.compile("^Upper bound:")
#    dualbound_expr = re.compile("^Lower Bound:")
#    solvingtime_expr = re.compile("^Total time:")
#    version_expr =  re.compile(" Couenne  --  an Open-Source solver for Mixed Integer Nonlinear Optimization \S* (\S*)")
#
#    solverstatusmap = {"" : Key.SolverStatusCodes.Optimal,
#                       "" : Key.SolverStatusCodes.Infeasible,
#                       "" : Key.SolverStatusCodes.TimeLimit,
#                       "" : Key.SolverStatusCodes.MemoryLimit,
#                       "" : Key.SolverStatusCodes.NodeLimit,
#                       "" : Key.SolverStatusCodes.Interrupted
#                       }
#
#    def __init__(self, **kw):
#        super(CouenneSolver, self).__init__(**kw)
#
#    def extractPrimalboundHistory(self, line : str):
#        """ Extract the sequence of primal bounds
#        """
#        if "Integer solution of " in line:
#            self.readBoundAndTime(line, 4, -2, timestripchars="(")
#        return None


class MatlabSolver(Solver):
    '''Solver class for the Matlab Intlinprog solver
    '''
    solverId = "Matlab"
    recognition_expr = re.compile(" *< M A T L A B \(R\) >")
    primalbound_expr = re.compile("PrimalBound (\S*)")
    dualbound_expr = re.compile("DualBound (\S*)")
    nodes_expr = re.compile("^BBnodes (\S+)")

    solverstatusmap = {"Intlinprog stopped.* because the objective value is within" : Key.SolverStatusCodes.Optimal,
                       "Intlinprog stopped because it exceeded the time limit" : Key.SolverStatusCodes.TimeLimit,
                       "Intlinprog stopped because the root LP problem is unbounded" : Key.SolverStatusCodes.Unbounded,
                       "Intlinprog stopped because no [a-z]* point" : Key.SolverStatusCodes.Infeasible,
                       "Intlinprog stopped because it exceeded its allocated memory" : Key.SolverStatusCodes.MemoryLimit,
                       "Intlinprog stopped because it reached the maximum number of nodes" : Key.SolverStatusCodes.NodeLimit,
                       "MPSREAD stopped because it encountered an invalid MPS format" : Key.SolverStatusCodes.Readerror,
                       "Intlinprog stopped" : Key.SolverStatusCodes.Interrupted
                       }

    def __init__(self, **kw):
        super(MatlabSolver, self).__init__(**kw)

class MosekSolver(Solver):
    '''Solver class for Mosek
    '''

    solverId = "Mosek"
    recognition_expr = re.compile("MOSEK")
    version_expr = re.compile("MOSEK Version (.*)$")
    solvingtime_expr = re.compile("Optimizer terminated\. Time: (.*)$")
    primalbound_expr = re.compile("^Objective of best integer solution : (.*)$")
    dualbound_expr = re.compile("^Best objective bound               : (.*)$")
    nodes_expr = re.compile("^Number of branches                 : (.*)$")

    solverstatusmap = {"^  Solution status : .*OPTIMAL" : Key.SolverStatusCodes.Optimal,
                       "^  Problem status  : PRIMAL_INFEASIBLE" : Key.SolverStatusCodes.Infeasible,
                       "^(  Problem status  : UNKNOWN|  Solution status : PRIMAL_FEASIBLE)" : Key.SolverStatusCodes.TimeLimit,
                       "^  Problem status  : PRIMAL_INFEASIBLE_OR_UNBOUNDED" : Key.SolverStatusCodes.InfOrUnbounded,
                       "^mosek.Error: \(1101\)" : Key.SolverStatusCodes.Readerror,
                       "^mosek.Error: \(1051\)" : Key.SolverStatusCodes.MemoryLimit
                       }

    def __init__(self, **kw):
        super(MosekSolver, self).__init__(**kw)

class MipclSolver(Solver):
    '''Solver class for the MIPCL solver
    '''

    solverId = "MIPCL"
    recognition_expr = re.compile("^MIPCL")
    version_expr = re.compile("^MIPCL version (.*)$")
    solvingtime_expr = re.compile("^Solution time: (.*)$")
    dualbound_expr = re.compile("^     lower-bound: (.*)$")
    #dualbound_expr = re.compile("^Objective value: (.*) - optimality proven")
    primalbound_expr = re.compile("^Objective value: (\S+)")
    nodes_expr = re.compile("Branch-and-Cut nodes: (.*)$")



    solverstatusmap = {"^Objective value: .* - optimality proven" : Key.SolverStatusCodes.Optimal,
                       "^This problem is infeasible" : Key.SolverStatusCodes.Infeasible,
                       "^Time limit reached" : Key.SolverStatusCodes.TimeLimit
                       }

    # members needed for primal bound history
    inTable = False
    primalboundhistory_exp = re.compile("^      Time     Nodes    Leaves   Sols       Best Solution         Lower Bound     Gap%")
    endtable = re.compile('^===========================================')

    def __init__(self, **kw):
        super(MipclSolver, self).__init__(**kw)


    def extractDualbound(self, line : str):
        Solver.extractDualbound(self, line)
        # Mipcl only reports a primal bound in case it solved to completion
        if self.primalbound_expr.match(line) and re.search("optimality proven$", line):
            self.extractByExpression(line, self.primalbound_expr, Key.DualBound)



    def extractHistory(self, line : str):
        """ Extract the sequence of primal bounds
        """

        return

        if not self.isTableLine(line):
            return

        # history reader should be in a table. check if a display char indicates a new primal bound
        if self.inTable:
            allmatches = misc.numericExpressionOrInf.findall(line)
            if len(allmatches) == 0:
                return

            pointInTime = allmatches[0]
            pb = allmatches[4]
            db = allmatches[5]
            # in the case of ugscip, we reacted on a disp char, so no problem at all.
            self.addHistoryData(Key.PrimalBoundHistory, pointInTime, pb)
            self.addHistoryData(Key.DualBoundHistory, pointInTime, db)

    def isTableLine(self, line):
        if self.primalboundhistory_exp.match(line):
            self.inTable = True
            return False
        elif self.inTable and self.endtable.match(line):
            self.inTable = False
            return False
        return self.inTable

class NuoptSolver(Solver):

    solverId = "Nuopt"
    recognition_expr = re.compile("^MSI Numerical Optimizer")
    primalbound_expr = re.compile("^VALUE_OF_OBJECTIVE *(\S+)")
    dualbound_expr = re.compile("^(?:Lower bound\s*|Objective value\s*):\s*(\S*)")
    solvingtime_expr = re.compile("^ELAPSED_TIME\(sec\.\) \s*(\S+)")
    version_expr = re.compile("^^MSI Numerical Optimizer (\S+)")
    nodes_expr = re.compile("^PARTIAL_PROBLEM_COUNT \s*(\S+)")
    gap_expr = re.compile("^GAP *(\S+)")
    no_feasible_sol_expr = re.compile("^\(NUOPT 2[02]\) .* \(no feas\.sol\.\)")
    viol_expr = re.compile("^\(NUOPT (14|34|36)\)")

    solverstatusmap = {"^STATUS *OPTIMAL" : Key.SolverStatusCodes.Optimal,
                       "^STATUS *NON_OPTIMAL" : Key.SolverStatusCodes.TimeLimit,
                       "^\(NUOPT 16\) Infeasible MIP" : Key.SolverStatusCodes.Infeasible,
                       "^__STDIN__:\d+: \(MPS FILE \d+\)" : Key.SolverStatusCodes.Readerror,
                       "^(\<preprocess begin\>\.+)*\(NUOPT 12\)" : Key.SolverStatusCodes.MemoryLimit,
                       #                       "" : Key.SolverStatusCodes.NodeLimit,
                       #                       "" : Key.SolverStatusCodes.Interrupted
                       }

    def __init__(self, **kw):
        super(NuoptSolver, self).__init__(**kw)

    def extractDualbound(self, line : str):
        """
        Nuopt only reports the gap, but not the actual dual bound.
        """
        gap_match = self.gap_expr.match(line)

        if gap_match:
            gap = float(gap_match.groups()[0])

            #
            #  A gap of -1 is reported if no solution was found
            #
            if gap >= 0:
                self.addData(Key.DualBound, self.getData(Key.PrimalBound) - gap)
        elif self.solvingtime_expr.match(line) and self.getData(Key.SolverStatus) == Key.SolverStatusCodes.Optimal:
            self.addData(Key.DualBound, self.getData(Key.PrimalBound))

    def extractPrimalbound(self, line : str):
        self.extractByExpression(line, self.primalbound_expr, Key.PrimalBound, float)

        # ## remove primal bound if no feasible solution has been found
        #
        # Nuopt reports 0 in this case
        #
        if self.no_feasible_sol_expr.match(line) or self.viol_expr.match(line):
            self.deleteData(Key.PrimalBound)
            self.deleteData(Key.DualBound)


class SasSolver(Solver):
    '''Solver class for Sas
    '''

    solverId = "SAS"
    recognition_expr = re.compile("^NOTE: SAS \(r\) Proprietary Software")
    version_expr = re.compile("^NOTE: SAS \(r\) Proprietary Software (\S+)")
    solvingtime_expr = re.compile("^ *Solution Time *(\S+)$")
    primalbound_expr = re.compile("^ *Objective Value *(\S+)$")
    dualbound_expr = re.compile("^ *Best Bound *(\S+)$")
    nodes_expr = re.compile("^ *Nodes *(\S+)$")

    solverstatusmap = {"^ *Solution Status *(Conditionally)* (Optimal|Failed)" : Key.SolverStatusCodes.Optimal,
                       "^ *Solution Status *Infeasible" : Key.SolverStatusCodes.Infeasible,
                       "^ *Solution Status *Time Limit Reached" : Key.SolverStatusCodes.TimeLimit,
                       "^ *Solution Status *Infeasible or Unbounded" : Key.SolverStatusCodes.InfOrUnbounded,
                       "^ERROR: The MPS file is incomplete\." : Key.SolverStatusCodes.Readerror,
                       "^ *Solution Status *Out of Memory" : Key.SolverStatusCodes.MemoryLimit
                       }

    def __init__(self, **kw):
        super(SasSolver, self).__init__(**kw)
