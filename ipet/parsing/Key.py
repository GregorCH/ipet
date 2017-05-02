
"""
This module acts as collection for the datakeys and its datatypes
"""

PrimalBound = "PrimalBound"
DualBound = "DualBound"
SolvingTime = "SolvingTime"
TimeLimitReached = "LimitReached"
Solver = "Solver"
Version = "Version"
Settings = "Settings"
SettingsPathAbsolute = "AbsolutePathSettings"
ProblemName = "ProblemName"

class SolverStatus:
    Crashed = -1
    Optimal = 0
    Infeasible = 1
    TimeLimit = 2
    MemLimit = 3
    Limit = 4
