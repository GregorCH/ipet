
import re
import os
from ipet import Key
from ipet.misc import misc
from ipet.parsing.StatisticReader import StatisticReader
from ipet.Key import SolverStatusCodes
from operator import itemgetter
from pip._vendor.distlib._backport.tarfile import TUREAD

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

    def extractPrimalboundHistory(self, line : str):
        """ Extract the sequence of primal bounds  
        """
        pass 
    
    def extractDualboundHistory(self, line : str):
        """ Extract the sequence of dual bounds  
        """
        pass 
    
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

    def addData(self, key, datum):
        """Add data to local data-dictionary
        """
        self.data[key] = datum

    def addHistoryData(self, key, timestr : str, boundstr : str):
        """Add data to local data-dictionary
        """
        try:
            time = float(timestr)
            bound = float(boundstr)
        except:
            return
        history = self.data.setdefault(key, [])
        # only append newly found bounds
        if history == [] or history[-1][1] != bound:
            if(key == Key.PrimalBoundHistory):
                history.append((time, bound))
            elif(key == Key.DualBoundHistory) and (history == [] or history[-1][0] != time):
                history.append((time, bound))

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
        self.extractPrimalboundHistory(line)

    # This method should be overwritten by subclasses
    def extractOptionalInformation(self, line : str):
        """Read optional data
        """
        pass

    def extractGeneralInformation(self, line : str):
        """Read general data
        """
        self.extractVersion(line)
        self.extractDualboundHistory(line)

    def reset(self):
        """Reset all Data except the solverId
        """
        self.data = {}
        self.addData(Key.Solver, self.solverId)
        self.addData(Key.SolverStatus, Key.SolverStatusCodes.Crashed)
#        TODO how does the historydata work ?
        self.data.setdefault(Key.PrimalBoundHistory, [])
        self.data.setdefault(Key.DualBoundHistory, [])

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
        return filecontext in [Key.CONTEXT_ERRFILE, Key.CONTEXT_LOGFILE]

    # Helper for primalboundhistory-reading
    def readBoundAndTime(self, line, boundidx, timeidx, timestripchars="", cutidx=-1):
        splitline = line.split()
        primalbound = line[:cutidx].split()[boundidx]
        pointInTime = splitline[timeidx].strip(timestripchars)
        self.addHistoryData(Key.PrimalBoundHistory, pointInTime, primalbound)

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

    # variables needed for primal bound history
    inTable = False
    primalboundhistory_exp = re.compile('^\s+time\s+\| .* \|\s+primalbound\s+\|\s+gap')
    heurdispcharexp = re.compile('^[^ \d]')
    heurdispcharexpugmode = re.compile('^\*')
    """ all lines starting with a non-whitespace and non-digit character """

    shorttablecheckexp = re.compile('s\|')
    firstsolexp = re.compile('^  First Solution   :')
    ugtableexp = re.compile('^\s+Time\s+Nodes')
    ugmode = False
    shorttablecheckexp = re.compile('s\|')
    
    # variables needed for dual bound history
    regular_exp = re.compile('\|')  # compile the regular expression to speed up reader
    
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

    def reset(self):
        Solver.reset(self)
        # variables needed for dual bound history
        self.lastdualbound = misc.FLOAT_INFINITY
        self.lasttime = -1
        self.dualboundindex = -1
    
    def extractPrimalboundHistory(self, line : str):
        """ Extract the sequence of primal bounds  
        """
        if not self.isTableLine(line):
            return 
        
        # history reader should be in a table. check if a display char indicates a new primal bound
        if self.inTable and self.heurdispcharexp.match(line) and not self.ugmode or \
            self.inTable and self.heurdispcharexpugmode.match(line) and self.ugmode:

            if not self.ugmode:
                allmatches = misc.numericExpression.findall(line[:line.rindex("|")])
            else:
                allmatches = misc.numericExpression.findall(line)[:5]

            if len(allmatches) == 0:
                return

            pointInTime = allmatches[0]
            PrimalBound = allmatches[-1]
            # in the case of ugscip, we reacted on a disp char, so no problem at all.
            self.addHistoryData(Key.PrimalBoundHistory, pointInTime, PrimalBound)

        elif not self.inTable and self.firstsolexp.match(line):
            matches = self.numericExpression.findall(line)
            PrimalBound = matches[0]
            pointInTime = matches[3]
            # store newly found (time, primal bound) tuple if it differs from the last primal bound
            self.addHistoryData(Key.PrimalBoundHistory, pointInTime, PrimalBound)
    
    def extractDualboundHistory(self, line : str):
        """ Extract the sequence of dual bounds  
        """
        timeindex = 0
    
        if not self.isTableLine(line):
            if self.inTable:
                # parse index of dual bound entry
                columnheaders = list(map(str.strip, line.split('|')))
                self.dualboundindex = columnheaders.index('dualbound')
            return 

        try:
            # FARI This works, why is eclipse complaining?
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
     
    def isTableLine(self, line):
        if self.primalboundhistory_exp.match(line):
            self.inTable = True
            self.ugmode = False
            return False
        elif line.startswith("     Time          Nodes        Left   Solvers     Best Integer        Best Node"):
            self.inTable = True
            self.ugmode = True
            return False
        elif self.inTable and ((line.startswith("SCIP Status") and self.ugmode) \
                         or ((not self.ugmode) and not self.shorttablecheckexp.search(line))):
            self.inTable = False
        return self.inTable

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

    def extractOptionalInformation(self, line : str):
        """Extract the path info
        """
        self.extractPath(line)
        self.extractMoreData(line)
        self.extractDualboundHistory(line)

class GurobiSolver(Solver):

    solverID = "GUROBI"
    recognition_expr = re.compile("Gurobi Optimizer version")
    primalbound_expr = re.compile("^Best objective (\S+)")
    dualbound_expr = re.compile("^Best objective (?:\S+), best bound (\S+)")
    solvingtimer_expr = re.compile("Explored \d* nodes \(.*\) in (\S*) seconds")
    version_expr = re.compile("Gurobi Optimizer version (\S+)")
    limitreached_expr = re.compile("^Time limit reached")

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
            self.readBoundAndTime(line, -5, -1, timestripchars="s")

        elif "Cutting planes:" in line and self.inTable:
            self.inTable = False
        elif self.gurobiextralist != [] and "Explored " in line:
            pointInTime = line.split()[-2]
            self.addHistoryData(Key.PrimalBoundHistory, pointInTime, self.gurobiextralist[-1])
            self.gurobiextralist = []
        return None
    
    def extractDualboundHistory(self, line : str):
        """ Extract the sequence of dual bounds  
        """
        pass 
    
class CplexSolver(Solver):

    solverID = "CPLEX"
    recognition_expr = re.compile("Welcome to IBM(R) ILOG(R) CPLEX(R) Interactive Optimizer")
    primalbound_expr = re.compile("^MIP -.*Objective =\s*(\S+)")
    dualbound_expr = re.compile("^Current MIP best bound =\s*(\S+)")
    solvingtimer_expr = re.compile("Solution time =\s*(\S+)")
    version_expr = re.compile("Welcome to IBM(R) ILOG(R) CPLEX(R) Interactive Optimizer (\S+)")
    limitreached_expr = None

    # variables needed for primal bound history extraction
    easyCPLEX = True
    lastelapsedtime = 0.0
    nnodessincelastelapsedtime = 0
    lastnnodes = 0
    cpxprimals = []
    inTable = True
    
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
            elif self.inTable and len(line) > 0 and line.startswith(" ") or line.startswith("*"):
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
            elif "Elapsed time = " in line:
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

    solverID = "CBC"
    recognition_expr = re.compile("Welcome to the CBC MILP Solver")
    primalbound_expr = re.compile("Objective value computed by solver: (\S*)")
    dualbound_expr = re.compile("Objective value:\s*(\S*)")
    solvingtimer_expr = re.compile("Total time \(CPU seconds\):\s*(\S*)")
    version_expr = re.compile("Version: (\S+)")
    limitreached_expr = None

    def __init__(self, **kw):
        super(CbcSolver, self).__init__(**kw)

    def extractPrimalboundHistory(self, line : str):
        """ Extract the sequence of primal bounds  
        """
        if "Integer solution of " in line:
            self.readBoundAndTime(line, 4, -2, timestripchars="(")
        return None
        
class XpressSolver(Solver):

    solverID = "XPRESS"
    recognition_expr = re.compile("FICO Xpress-Optimizer")
    primalbound_expr = re.compile("Best integer solution found is\s*(\S*)")
    dualbound_expr = re.compile("Best bound is\s*(\S*)")
    solvingtimer_expr = re.compile("\*\*\* Search completed \*\*\*\s*Time\s*(\S*)")
    version_expr = re.compile("FICO Xpress-Optimizer \S* (\S*)")
    limitreached_expr = re.compile("STOPPING = (\S*) limit reached")

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
            self.readBoundAndTime(line, -1, -1, cutidx=self.xpresscutidx)
        elif line.startswith(" *** Heuristic solution found: "):
            self.readBoundAndTime(line, -4, -2)

    
#class CouenneSolver(Solver):
#
#    # TODO fix regexes to contain groups which can extract numbers
#    solverID = "Couenne"
#    recognition_expr = re.compile("Couenne  --  an Open-Source solver for Mixed Integer Nonlinear Optimization")
#    primalbound_expr = re.compile("^Upper bound:")
#    dualbound_expr = re.compile("^Lower Bound:")
#    solvingtimer_expr = re.compile("^Total time:")
#    version_expr =  re.compile(" Couenne  --  an Open-Source solver for Mixed Integer Nonlinear Optimization \S* (\S*)")
#    limitreached_expr = None
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

