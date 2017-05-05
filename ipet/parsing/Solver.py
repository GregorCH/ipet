
import re
import os
from ipet import Key
from ipet.misc import misc
from ipet.parsing.StatisticReader import StatisticReader
from ipet.Key import SolverStatusCodes
from operator import itemgetter

class Solver():

    DEFAULT = None
    solverId = "defaultSolver"
    recognition_expr = None
    primalbound_expr = None
    dualbound_expr = None
    solvingtimer_expr = None
    version_expr = None
    limitreached_expr = None

    solverstatusmap = {}

    def __init__(self,
                 solverID = None,
                 recognition_pattern = None,
                 primalbound_pattern = None,
                 dualbound_pattern = None,
                 solvingtimer_pattern = None,
                 version_pattern = None,
                 limitreached_pattern = None,
                 solverstatusmap = None):

        if solverID is not None:
            self.solverId = solverID

        if not recognition_pattern is None:
            self.recognition_expr = re.compile(recognition_pattern)
        if not primalbound_pattern is None:
            self.primalbound_expr = re.compile(primalbound_pattern)
        if not dualbound_pattern is None:
            self.dualbound_expr = re.compile(dualbound_pattern)
        if not solvingtimer_pattern is None:
            self.solvingtimer_expr = re.compile(solvingtimer_pattern)
        if not version_pattern is None:
            self.version_expr = re.compile(version_pattern)
        if not limitreached_pattern is None:
            self.limitreached_expr = re.compile(limitreached_pattern)

        if solverstatusmap is not None:
            self.solverstatusmap = solverstatusmap
        self.solverstatusses = sorted(self.solverstatusmap.items(), key = itemgetter(1))


        self.data = {}
        self.reset()

    def extractStatus(self, line : str):
        """Check if the line matches one of the status patterns
        """
        for pattern, status in self.solverstatusses:
            if line.startswith(pattern):

                self.addData(Key.SolverStatus, status)
                # break in order to prevent parsing a weaker status
                break

    def extractVersion(self, line : str):
        """Extract the version of the solver-software
        """
        self.extractByExpression(line, self.version_expr, Key.Version)

    def extractSolvingTime(self, line : str):
        """Read the overall solving time
        """
        self.extractByExpression(line, self.solvingtimer_expr, Key.SolvingTime)

    def extractDualbound(self, line : str):
        """Return the reported dual bound (at the end of the solver-output)
        """
        self.extractByExpression(line, self.dualbound_expr, Key.DualBound)

    def extractPrimalbound(self, line : str):
        """Read the primal bound (at the end of the solver-output)
        """
        self.extractByExpression(line, self.primalbound_expr, Key.PrimalBound)

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
        m = expr.match(line)
        if m is not None:
            try:
                d = datatype(m.groups()[0])
                self.addData(key, d)
            except:
                pass

    def addData(self, key, data):
        """Add data to local data-dictionary
        """
        self.data[key] = data

    def readLine(self, line : str):
        """Read solver-specific data from that line
        """
        self.extractElementaryInformation(line)
        self.extractOptionalInformation(line)
        self.extractGeneralInformation(line)

    def extractElementaryInformation(self, line : str):
        """Read Data that is needed for validation
        """
        self.extractPrimalbound(line)
        self.extractDualbound(line)
        self.extractSolvingTime(line)
        self.extractVersion(line)
        self.extractStatus(line)


    # This method should be overwritten by subclasses
    def extractOptionalInformation(self, line : str):
        """Read optional data
        """
        pass

    def extractGeneralInformation(self, line : str):
        """Read general data
        """
        self.extractVersion(line)

    def reset(self):
        """Reset all Data except the solverId
        """
        self.data = {}
        self.addData(Key.Solver, self.solverId)
        self.addData(Key.SolverStatus, Key.SolverStatusCodes.Crashed)

    def recognizeOutput(self, line : str):
        return self.recognition_expr.match(line) != None

    def getData(self, datakey = None):
        """Return data stored under datakey or return collected data as a tuple of two generators
        """
        if datakey is None:
            return map(list, zip(*self.data.items()))
        else:
            return self.data.get(datakey)

    def getName(self):
        return self.solverId

    def isSolverInstance(self, filecontext):
        return filecontext is StatisticReader.CONTEXT_ERRFILE or filecontext is StatisticReader.CONTEXT_LOGFILE

###############################################################
##################### DERIVED Classes #########################
###############################################################

class SCIPSolver(Solver):

    solverId = "SCIP"
    recognition_expr = re.compile("^SCIP version ")
    primalbound_expr = re.compile("^Primal Bound       : (\S+)")
    dualbound_expr = re.compile("^Dual Bound         : (\S+)")
    solvingtimer_expr = re.compile("^Solving Time \(sec\) : (\S+)")
    version_expr = re.compile("SCIP version (\S+)")
    limitreached_expr = re.compile("((?:^SCIP Status        :)|(?:\[(?:.*) (reached|interrupt)\]))")

    solverstatusmap = {
        "SCIP Status        : problem is solved [optimal solution found]":Key.SolverStatusCodes.Optimal,
        "SCIP Status        : problem is solved [infeasible]": Key.SolverStatusCodes.Infeasible,
        "SCIP Status        : solving was interrupted [time limit reached]" : Key.SolverStatusCodes.TimeLimit,
        "SCIP Status        : solving was interrupted [memory limit reached]" : Key.SolverStatusCodes.MemoryLimit,
        "SCIP Status        : solving was interrupted [node limit reached]" : Key.SolverStatusCodes.NodeLimit,
        "SCIP Status        : solving was interrupted" : Key.SolverStatusCodes.Interrupted,
        }

    def __init__(self, **kw):
        super(SCIPSolver, self).__init__(**kw)

    def extractOptionalInformation(self, line : str):
        """Extract the path info
        """
        self.extractPath(line)
        self.extractMoreData(line)

    def extractMoreData(self, line : str):
        """Handle more than just the version
        """
        for keyword in ["mode", "LP solver", "GitHash"]:
            data = re.search(r"\[%s: ([\w .-]+)\]" % keyword, line)
            if data:
                self.addData(keyword if keyword != "LP solver" else "LPSolver", data.groups()[0])

    def extractPath(self, line : str):
        """Extract the path info
        """
        if line.startswith('loaded parameter file'):
            absolutesettingspath = line[len('loaded parameter file '):].strip('<>')
            self.addData(Key.SettingsPathAbsolute, absolutesettingspath)
            settings = os.path.basename(absolutesettingspath)
            settings = os.path.splitext(settings)[0]

class GurobiSolver(Solver):

    solverID = "GUROBI"
    recognition_expr = re.compile("Gurobi Optimizer version")
    primalbound_expr = re.compile("^Best objective (\S+)")
    dualbound_expr = re.compile("^Best objective (?:\S+), best bound (\S+)")
    solvingtimer_expr = re.compile("Explored \d* nodes \(.*\) in (\S*) seconds")
    version_expr = re.compile("Gurobi Optimizer version (\S+)")
    limitreached_expr = re.compile("^Time limit reached")

    def __init__(self, **kw):
        super(GurobiSolver, self).__init__(**kw)

class CplexSolver(Solver):

    solverID = "CPLEX"
    recognition_expr = re.compile("Welcome to IBM(R) ILOG(R) CPLEX(R) Interactive Optimizer")
    primalbound_expr = re.compile("^MIP -.*Objective =\s*(\S+)")
    dualbound_expr = re.compile("^Current MIP best bound =\s*(\S+)")
    solvingtimer_expr = re.compile("Solution time =\s*(\S+)")
    version_expr = re.compile("Welcome to IBM(R) ILOG(R) CPLEX(R) Interactive Optimizer (\S+)")
    limitreached_expr = None

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

class CbcSolver(Solver):

    solverID = "CBC"
    recognition_expr = re.compile("Welcome to the CBC MILP Solver")
    primalbound_expr = re.compile("Objective value computed by solver: (\S*)")
    dualbound_expr = re.compile("Objective value:\s*(\S*)")
    solvingtimer_expr = re.compile("Total time \(CPU seconds\):\s*(\S*)")
    version_expr = re.compile("Version: (\S+)")
    limitreached_expr = None

    def __init__(self, **kw):
        super(CbcSolver, self).__init__(**kw)

class XpressSolver(Solver):

    solverID = "XPRESS"
    recognition_expr = re.compile("FICO Xpress-Optimizer")
    primalbound_expr = re.compile("Best integer solution found is\s*(\S*)")
    dualbound_expr = re.compile("Best bound is\s*(\S*)")
    solvingtimer_expr = re.compile("\*\*\* Search completed \*\*\*\s*Time\s*(\S*)")
    version_expr = re.compile("FICO Xpress-Optimizer \S* (\S*)")
    limitreached_expr = re.compile("STOPPING = (\S*) limit reached")

    def __init__(self, **kw):
        super(XpressSolver, self).__init__(**kw)
#
# class CouenneSolver(Solver):
#
#     solverID = "Couenne"
#     recognition_expr = re.compile("Couenne  --  an Open-Source solver for Mixed Integer Nonlinear Optimization")
#     primalbound_expr = re.compile("^Upper bound:")
#     dualbound_expr = re.compile("^Lower Bound:")
#     solvingtimer_expr = re.compile("^Total time:")
#     version_expr =  re.compile(" Couenne  --  an Open-Source solver for Mixed Integer Nonlinear Optimization \S* (\S*)")
#     limitreached_expr = None
#
#     def __init__(self, **kw):
#         super(CouenneSolver, self).__init__(**kw)
#
#
