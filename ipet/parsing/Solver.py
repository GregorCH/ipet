
from .StatisticReader import StatisticReader, ListReader

import re

class Solver():
    
    DEFAULT=None
    DEFAULTTIMELIMITKEYS="@05"
    DEFAULT_SOLVERID="defaultSolver"
    
    def __init__(self, 
                 solverID=DEFAULT_SOLVERID, 
                 recognition_pattern=DEFAULT, 
                 primalbound_pattern=DEFAULT, 
                 primalbound_lineindices=DEFAULT, 
                 dualbound_pattern=DEFAULT, 
                 dualbound_lineindices=DEFAULT, 
                 solvingtimer_pattern=DEFAULT, 
                 solvingtime_lineindices=DEFAULT,
                 timelimitreadkeys=DEFAULTTIMELIMITKEYS,
                 version_pattern=DEFAULT,
                 version_lininedices=DEFAULT,
                 timelimitreached_pattern=DEFAULT, 
                 timelimitreached_expression=DEFAULT):
        self.solverId = solverID
        self.recognition_pattern = recognition_pattern
        self.primalbound_pattern = primalbound_pattern 
        self.primalbound_lineindices = primalbound_lineindices
        self.dualbound_pattern = dualbound_pattern
        self.dualbound_lineindices = dualbound_lineindices
        self.solvingtimer_pattern = solvingtimer_pattern
        self.solvingtime_lineindices = solvingtime_lineindices
        self.timelimitreadkeys = timelimitreadkeys
        self.version_pattern = version_pattern
        self.version_lininedices = version_lininedices
        self.timelimitreached_pattern = timelimitreached_pattern
        self.timelimitreached_expression = timelimitreached_expression
        
    def readline(self, line):
        pass
     
    # BestSolInfeasibleReader, 
    def bestSolutionIsInfeasible(self):
        pass
    
    # DualBoundReader, 
    def getDualBound(self):
        pass
    
    # SolvingTimeReader, 
    def getSolvingTime(self):
        pass 
    
    # LimitReachedReader,
    def limitWasReached(self):
        pass
    
    # PrimalBoundReader, 
    def getPrimalBound(self):
        pass
    
    # ErrorFileReader  
    
    # primalboundhistory, dualboundhistory
        
    # ObjsenseReader, 
    
    # ObjlimitReader,   
    
###############################################################
##################### DERIVED Classes #########################
###############################################################
#  
# class SCIPSolver(Solver):
#      
#     def __init__(self):
#         super(Solver, self).__init__(solverID="SCIP", 
#                                      recognition_pattern="SCIP version ", 
#                                      primalbound_pattern='^Primal Bound       :', 
#                                      primalbound_lineindices=3, 
#                                      dualbound_pattern="^Dual Bound         :", 
#                                      dualbound_lineindices=-1, 
#                                      solvingtimer_pattern="^Solving Time \(sec\) :", 
#                                      solvingtime_lineindices=-1,
#                                      version_pattern='SCIP version',
#                                      version_lininedices=2,
#                                      timelimitreached_pattern=re.compile(r'\[(.*) (reached|interrupt)\]'), 
#                                      timelimitreached_expression=re.compile(r'^SCIP Status        :'))
#      
# class GurobiSolver(Solver):
#      
#     def __init__(self):
#         super(Solver, self).__init__(solverID="GUROBI", 
#                                      recognition_pattern="Gurobi Optimizer version", 
#                                      primalbound_pattern='^Best objective ', 
#                                      primalbound_lineindices=2, 
#                                      dualbound_pattern='^Best objective', 
#                                      dualbound_lineindices=5, 
#                                      solvingtimer_pattern="Explored ", 
#                                      solvingtime_lineindices=-2,
#                                      version_pattern="Gurobi Optimizer version",
#                                      version_lininedices=3,
#                                      timelimitreached_pattern=re.compile(r'^(Time limit) reached'), 
#                                      timelimitreached_expression=re.compile(r'^Time limit reached'))
#          
# class CplexSolver(Solver):
#      
#     def __init__(self):
#         super(Solver, self).__init__(solverID="CPLEX", 
#                                      recognition_pattern="Welcome to IBM(R) ILOG(R) CPLEX(R) Interactive Optimizer", 
#                                      primalbound_pattern='^MIP -.*Objective = ', 
#                                      primalbound_lineindices=-1, 
#                                      dualbound_pattern='(^Current MIP best bound =|^MIP - Integer optimal)', 
#                                      dualbound_lineindices=5, 
#                                      solvingtimer_pattern="Solution time =", 
#                                      solvingtime_lineindices=3,
#                                      version_pattern="Welcome to IBM(R) ILOG(R) CPLEX(R)",
#                                      version_lininedices=-1)
#          
# class CbcSolver(Solver):
#      
#     def __init__(self):
#         super(Solver, self).__init__(solverID="CBC", 
#                                      recognition_pattern="FICO Xpress-Optimizer", 
#                                      solvingtimer_pattern="Coin:Total time \(CPU seconds\):", 
#                                      solvingtime_lineindices=4,
#                  version_pattern="Version:",
#                  version_lininedices=-1)
#          
# class XpressSolver(Solver):
#      
#     def __init__(self):
#         super(Solver, self).__init__(solverID="XPRESS", 
#                                      recognition_pattern="Welcome to the CBC MILP Solver",
#                                      primalbound_pattern="Best integer solution found is", 
#                                      primalbound_lineindices=-1,
#                                      dualbound_pattern="Best bound is", 
#                                      dualbound_lineindices=-1, 
#                                      solvingtimer_pattern=" \*\*\* Search ", 
#                                      solvingtime_lineindices=5,
#                                      version_pattern="FICO Xpress Optimizer",
#                                      version_lininedices=4)
#          
# class CouenneSolver(Solver):
#      
#     def __init__(self):
#         super(Solver, self).__init__(solverID="Couenne", 
#                                      recognition_pattern=" Couenne  --  an Open-Source solver for Mixed Integer Nonlinear Optimization", 
#                                      primalbound_pattern="^Upper bound:", 
#                                      primalbound_lineindices=2,
#                                      dualbound_pattern='^Lower Bound:', 
#                                      dualbound_lineindices=2,
#                                      solvingtimer_pattern="^Total time:", 
#                                      solvingtime_lineindices=2,
#                                      timelimitreadkeys="^@05",
#                                      version_pattern=" Couenne  --  an Open-Source solver for Mixed Integer Nonlinear Optimization",
#                                      version_lininedices=-1)

###############################################################
########################### Notes #############################
###############################################################

    # from statisticreader
    #SOLVERTYPE_SCIP = "SCIP"
    #SOLVERTYPE_GUROBI = "GUROBI"
    #SOLVERTYPE_CPLEX = "CPLEX"
    #SOLVERTYPE_CBC = "CBC"
    #SOLVERTYPE_XPRESS = "XPRESS"
    #SOLVERTYPE_COUENNE = "Couenne"
    
    # from readermanager
    #solvertype_recognition = {
    #    StatisticReader.SOLVERTYPE_SCIP:"SCIP version ",
    #    StatisticReader.SOLVERTYPE_GUROBI:"Gurobi Optimizer version",
    #    StatisticReader.SOLVERTYPE_CPLEX:"Welcome to IBM(R) ILOG(R) CPLEX(R) Interactive Optimizer",
    #    StatisticReader.SOLVERTYPE_XPRESS:"FICO Xpress-Optimizer",
    #    StatisticReader.SOLVERTYPE_CBC:"Welcome to the CBC MILP Solver",
    #    StatisticReader.SOLVERTYPE_COUENNE:" Couenne  --  an Open-Source solver for Mixed Integer Nonlinear Optimization"
    #    }

    # from statisticreader.primalboundreader
    #primalboundpatterns = {StatisticReader.SOLVERTYPE_SCIP: '^Primal Bound       :',
    #                       StatisticReader.SOLVERTYPE_CPLEX : '^MIP -.*Objective = ',
    #                       StatisticReader.SOLVERTYPE_GUROBI : '^Best objective ',
    #                       StatisticReader.SOLVERTYPE_COUENNE : "^Upper bound:",
    #                       StatisticReader.SOLVERTYPE_XPRESS : "Best integer solution found is"}
    #primalboundlineindices = {StatisticReader.SOLVERTYPE_SCIP: 3,
    #                          StatisticReader.SOLVERTYPE_CPLEX :-1,
    #                          StatisticReader.SOLVERTYPE_GUROBI : 2,
    #                          StatisticReader.SOLVERTYPE_COUENNE : 2,
    #                          StatisticReader.SOLVERTYPE_XPRESS :-1}
    
    # from statisticreader.dualboundreader
    #dualboundpatterns = {StatisticReader.SOLVERTYPE_SCIP : "^Dual Bound         :",
    #                     StatisticReader.SOLVERTYPE_GUROBI : '^Best objective',
    #                     StatisticReader.SOLVERTYPE_CPLEX : '(^Current MIP best bound =|^MIP - Integer optimal)',
    #                     StatisticReader.SOLVERTYPE_COUENNE : '^Lower Bound:',
    #                     StatisticReader.SOLVERTYPE_XPRESS : "Best bound is"}
    #dualboundlineindices = {StatisticReader.SOLVERTYPE_SCIP :-1,
    #                        StatisticReader.SOLVERTYPE_CPLEX : 5,
    #                        StatisticReader.SOLVERTYPE_GUROBI : 5,
    #                        StatisticReader.SOLVERTYPE_COUENNE : 2,
    #                        StatisticReader.SOLVERTYPE_XPRESS :-1}

    # from statisticreader.solvingtimereader
    #solvingtimereadkeys = {
    #    StatisticReader.SOLVERTYPE_SCIP : "^Solving Time \(sec\) :",
    #    StatisticReader.SOLVERTYPE_CPLEX : "Solution time =",
    #    StatisticReader.SOLVERTYPE_GUROBI : "Explored ",
    #    StatisticReader.SOLVERTYPE_CBC : "Coin:Total time \(CPU seconds\):",
    #    StatisticReader.SOLVERTYPE_XPRESS : " \*\*\* Search ",
    #    StatisticReader.SOLVERTYPE_COUENNE : "^Total time:"
    #}

    #solvingtimelineindex = {
    #    StatisticReader.SOLVERTYPE_SCIP :-1,
    #    StatisticReader.SOLVERTYPE_CPLEX : 3,
    #    StatisticReader.SOLVERTYPE_GUROBI :-2,
    #    StatisticReader.SOLVERTYPE_CBC : 4,
    #    StatisticReader.SOLVERTYPE_XPRESS :5,
    #    StatisticReader.SOLVERTYPE_COUENNE : 2
    #}

    # from timelimitreader
    #timelimitreadkeys = {
    #               StatisticReader.SOLVERTYPE_SCIP : '@05',
    #               StatisticReader.SOLVERTYPE_CPLEX : '@05',
    #               StatisticReader.SOLVERTYPE_GUROBI : "@05",
    #               StatisticReader.SOLVERTYPE_CBC : "@05",
    #               StatisticReader.SOLVERTYPE_XPRESS : "@05",
    #               StatisticReader.SOLVERTYPE_COUENNE : "^@05"}
                
    # from generalinformationreader -> version_pattern
    #versionkeys = {StatisticReader.SOLVERTYPE_SCIP : 'SCIP version',
    #               StatisticReader.SOLVERTYPE_CPLEX : "Welcome to IBM(R) ILOG(R) CPLEX(R)",
    #               StatisticReader.SOLVERTYPE_GUROBI : "Gurobi Optimizer version",
    #               StatisticReader.SOLVERTYPE_CBC : "Version:",
    #               StatisticReader.SOLVERTYPE_XPRESS : "FICO Xpress Optimizer",
    #               StatisticReader.SOLVERTYPE_COUENNE : " Couenne  --  an Open-Source solver for Mixed Integer Nonlinear Optimization"}
    # -> version_lininedices
    #versionlineindices = {StatisticReader.SOLVERTYPE_SCIP : 2,
    #                      StatisticReader.SOLVERTYPE_CPLEX :-1,
    #                      StatisticReader.SOLVERTYPE_GUROBI :3,
    #                      StatisticReader.SOLVERTYPE_CBC :-1,
    #                      StatisticReader.SOLVERTYPE_XPRESS: 4,
    #                      StatisticReader.SOLVERTYPE_COUENNE:-1}

    # from limitreachedreader -> timelimitreached_pattern, timelimitreached_expression
    # = {StatisticReader.SOLVERTYPE_SCIP: re.compile(r'\[(.*) (reached|interrupt)\]'),
    #               StatisticReader.SOLVERTYPE_GUROBI: re.compile(r'^(Time limit) reached')}
    
    #lineexpression = {StatisticReader.SOLVERTYPE_GUROBI: re.compile(r'^Time limit reached'),
    #                  StatisticReader.SOLVERTYPE_SCIP: re.compile(r'^SCIP Status        :')}
      
