
"""
This module acts as collection for the datakeys and its datatypes
"""

BestSolutionInfeasible = "BestSolInfeas"
DatetimeEnd = "Datetime_End"
DatetimeStart = "Datetime_Start"
DualBound = "DualBound"
DualIntegral = "DualIntegral"
DualLpTime = "DualLpTime"
ErrorCode = "ErrorCode"
Gap = "Gap"
LimitReached = "LimitReached"
MaximumDepth = "MaxDepth"
Nodes = "Nodes"
ObjectiveLimit = "Objlimit"
ObjectiveSense = "Objsense"
OptimalValue = "OptVal"
PrimalBound = "PrimalBound"
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
TimeLimitReached = "TimeLimitReached"
Version = "Version"

class ProblemStatuses:
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
        """
        returns the best status among a list of status codes given as args
        """
        return max(*args, key=lambda x : ProblemStatus.statusToPriority.get(x, 0))
    
    @staticmethod
    def getWorstStatus(*args):
        """
        return the worst status among a list of status codes
        """
        return min(*args, key=lambda x : ProblemStatus.statusToPriority.get(x, 0)) 

class SolverStatuses:
    Crashed = -1
    Optimal = 0
    Infeasible = 1
    TimeLimit = 2
    MemoryLimit = 3
    Limit = 4
    NodeLimit = 5
