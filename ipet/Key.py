
""" This module acts as collection for the datakeys and its datatypes and several status codes
"""

# FARI didn't we want to save the datatypes of the fields?

BestSolutionInfeasible = "BestSolInfeas"
DatetimeEnd = "Datetime_End"
DatetimeStart = "Datetime_Start"
DualBound = "DualBound"
DualBoundHistory = "DualBoundHistory"
DualIntegral = "DualIntegral"
DualLpTime = "DualLpTime"
ErrorCode = "ErrorCode"
Gap = "Gap"
LogFileName = "LogFileName"
MaximumDepth = "MaxDepth"
Nodes = "Nodes"
ObjectiveLimit = "Objlimit"
ObjectiveSense = "Objsense"
OptimalValue = "OptVal"
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
    Crashed = -1
    Optimal = 0
    Infeasible = 1
    TimeLimit = 2
    MemoryLimit = 3
    NodeLimit = 4
    Interrupted = 5

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

    statusToPriority = {Ok : 1000,
                        SolvedNotVerified : 500,
                        Better : 250,
                        Unknown : 100,
                        FailDualBound :-250,
                        FailObjectiveValue :-500,
                        FailSolInfeasible :-1000,
                        FailSolOnInfeasibleInstance :-2000,
                        Fail :-3000,
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


