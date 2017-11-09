
""" This module acts as collection for the datakeys and its datatypes and several status codes
"""

# constants that represent the different contexts that a reader should be active in
CONTEXT_LOGFILE = 1  # the log file of a solver which most readers are reading from
CONTEXT_ERRFILE = 2  # the error file of a solver
CONTEXT_SETFILE = 3  # the settings file used for solving
CONTEXT_SOLUFILE = 4  # the solution file that contains the statuses and optimal objective values for every problem
CONTEXT_TRACEFILE = 5
CONTEXT_METAFILE = 0  # the metadata

contextname2contexts = {
        "log" : CONTEXT_LOGFILE,
        "err" : CONTEXT_ERRFILE,
        "set" : CONTEXT_SETFILE,
        "solu" : CONTEXT_SOLUFILE,
        "trace" : CONTEXT_TRACEFILE,
        "meta" : CONTEXT_METAFILE,
        "" : CONTEXT_LOGFILE
    }

fileextension2context = {
                         ".err" : CONTEXT_ERRFILE,
                         ".out" : CONTEXT_LOGFILE,
                         ".set" : CONTEXT_SETFILE,
                         ".solu": CONTEXT_SOLUFILE,
                         ".trc" : CONTEXT_TRACEFILE,
                         ".meta" : CONTEXT_METAFILE,
                         "" : CONTEXT_LOGFILE # workaround for input from stdin
                         }
"""map for file extensions to the file contexts to specify the relevant readers"""

context2Sortkey = {
                   CONTEXT_ERRFILE : 2,
                   CONTEXT_LOGFILE : 1,
                   CONTEXT_SETFILE : 3,
                   CONTEXT_SOLUFILE : 4,
                   CONTEXT_TRACEFILE : 5,
                   CONTEXT_METAFILE : 0
                   }
""" defines a sorting order for file contexts """

BestSolutionInfeasible = "BestSolInfeas"
DatetimeEnd = "Datetime_End"
DatetimeStart = "Datetime_Start"
DualBound = "DualBound"
DualBoundHistory = "DualBoundHistory"
DualIntegral = "DualIntegral"
DualLpTime = "DualLpTime"
ErrorCode = "ErrorCode"
Gap = "Gap"
GitHash = "GitHash"
LogFileName = "LogFileName"
LPSolver = "LPSolver"
MetaData = "MetaData"
MaximumDepth = "MaxDepth"
Mode = "mode"
Nodes = "Nodes"
ObjectiveLimit = "Objlimit"
ObjectiveSense = "Objsense"
OptimalValue = "OptVal"
Path = "Path"
PrimalBound = "PrimalBound"
PrimalBoundHistory = "PrimalBoundHistory"
PrimalIntegral = "PrimalIntegral"
ProblemName = "ProblemName"
ProblemStatus = "Status"
RootNodeFixings = "RootNodeFixs"
Settings = "Settings"
SettingsPathAbsolute = "AbsolutePathSettings"
SolvingTime = "SolvingTime"
Solver = "Solver"
SolverStatus = "SolverStatus"
SolutionFileStatus = "SoluFileStatus"
TimeToBestSolution = "TimeToBest"
TimeToFirstSolution = "TimeToFirst"
TimeLimit = "TimeLimit"
Version = "Version"

class SolverStatusCodes:
    """ The reason why a solver stopped its calculation.

    There are several reasons for a solver to terminate its calculations:
    It could have

        - found the optimal solution
        - found, that the problem was infeasible
        - hit a limit of memory, time or nodes,

    or it could have simply been cancelled by the user
    or worse, could have crashed.
    """
    Readerror = -2
    Crashed = -1
    Optimal = 0
    Infeasible = 1
    TimeLimit = 2
    MemoryLimit = 3
    NodeLimit = 4
    Interrupted = 5
    Unbounded = 6
    GapLimit = 7

class ProblemStatusCodes:
    """ Keeping track of how good the solution of a solver actually was.

    After comparing the calculated result of a problem with the actual result,
    the status of the computation is graded and saved as one of the following:
    ...
    """
    Ok = 'ok'
    SolvedNotVerified = "solved_not_verified"
    Better = "better"
    Unknown = "unknown"
    FailDualBound = "fail_dual_bound"
    FailObjectiveValue = "fail_objective_value"
    FailSolInfeasible = "fail_solution_infeasible"
    FailSolOnInfeasibleInstance = "fail_solution_on_infeasible_instance"
    Fail = "fail"
    FailAbort = "fail_abort"
    FailReaderror = "fail_readerror"
    TimeLimit = "timelimit"
    MemoryLimit = "memlimit"
    NodeLimit = "nodelimit"
    Interrupted = "interrupt"

    statusToPriority = {Ok : 1000,
                        SolvedNotVerified : 500,
                        Better : 250,
                        Interrupted : 237,
                        NodeLimit : 225,
                        TimeLimit : 200,
                        MemoryLimit : 150,
                        Unknown : 100,
                        FailDualBound :-250,
                        FailObjectiveValue :-500,
                        FailSolInfeasible :-1000,
                        FailSolOnInfeasibleInstance :-2000,
                        Fail :-3000,
                        FailReaderror : -4000,
                        FailAbort :-10000}

    @staticmethod
    def getBestStatus(*args):
        """ Return the best status among a list of status codes given as args
        """
        return max(*args, key = lambda x : ProblemStatusCodes.statusToPriority.get(x, 0))

    @staticmethod
    def getWorstStatus(*args):
        """ Return the worst status among a list of status codes
        """
        return min(*args, key = lambda x : ProblemStatusCodes.statusToPriority.get(x, 0))

solver2problemStatusCode = {
    SolverStatusCodes.GapLimit : ProblemStatusCodes.Ok,
    SolverStatusCodes.Crashed : ProblemStatusCodes.FailAbort,
    SolverStatusCodes.Infeasible : ProblemStatusCodes.Ok,
    SolverStatusCodes.Optimal : ProblemStatusCodes.Ok,
    SolverStatusCodes.Unbounded : ProblemStatusCodes.Ok,
    SolverStatusCodes.TimeLimit : ProblemStatusCodes.TimeLimit,
    SolverStatusCodes.MemoryLimit : ProblemStatusCodes.MemoryLimit,
    SolverStatusCodes.NodeLimit : ProblemStatusCodes.NodeLimit,
    SolverStatusCodes.Interrupted : ProblemStatusCodes.Interrupted,
    SolverStatusCodes.Readerror : ProblemStatusCodes.FailReaderror}

def solverToProblemStatusCode(solverstatus : int) -> str:
    """Map the status of the solver to the corresponding problem status code

    Parameters
    ----------
    solverstatus
        integer status code reported by the solver
    """
    return solver2problemStatusCode.get(solverstatus, ProblemStatusCodes.FailAbort)
