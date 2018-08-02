'''
Created on 04.05.2017

@author: Gregor Hendel
'''
import unittest
import os
from ipet.parsing.Solver import SCIPSolver, GurobiSolver, CplexSolver, CbcSolver, XpressSolver, MipclSolver
from ipet import Key

DATADIR = os.path.join(os.path.dirname(__file__), "data")
TMPDIR = os.path.join(os.path.dirname(__file__), ".tmp")

SOLVER = 0
NAME = 1
PRECISE = 0
ALMOST = 1

class SolverTest(unittest.TestCase):

    fileinfo = {
                "cbc298-app1-2" : [ {
                    Key.Solver: "CBC",
                    Key.Version: "2.9.8",
                    Key.SolvingTime: 7132.49,
                    Key.Nodes: 31867,
                    Key.SolverStatus: Key.SolverStatusCodes.TimeLimit }, {
                    Key.PrimalBound: None,
                    Key.DualBound:-96.111} ],
                "cbc298-ash608gpia-3col" : [ {
                    Key.Solver: "CBC",
                    Key.Version: "2.9.8",
                    Key.SolvingTime: 224.71,
                    Key.Nodes: 0,
                    Key.SolverStatus: Key.SolverStatusCodes.Infeasible }, {
                    Key.PrimalBound: None ,
                    Key.DualBound: None} ],
                "cbc298-bab5" : [ {
                    Key.Solver: "CBC",
                    Key.Version: "2.9.8",
                    Key.SolvingTime: 7194.79,
                    Key.Nodes: 162253,
                    Key.SolverStatus: Key.SolverStatusCodes.TimeLimit }, {
                    Key.PrimalBound:-104286.921,
                    Key.DualBound:-111273.306} ],
                "cbc298-dfn-gwin-UUM" : [ {
                    Key.Solver: "CBC",
                    Key.Version: "2.9.8",
                    Key.SolvingTime: 725.37,
                    Key.Nodes: 378472,
                    Key.SolverStatus: Key.SolverStatusCodes.Optimal }, {
                    Key.PrimalBound: 38752,
                    Key.DualBound: 38752} ],
                "cbc298-enlight14" : [ {
                    Key.Solver: "CBC",
                    Key.Version: "2.9.8",
                    Key.SolvingTime: 7131.16,
                    Key.Nodes: 762406,
                    Key.SolverStatus: Key.SolverStatusCodes.TimeLimit }, {
                    Key.PrimalBound: None,
                    Key.DualBound: 36.768} ],
                "cbc298-satellites1-25" : [ {
                    Key.Solver: "CBC",
                    Key.Version: "2.9.8",
                    Key.SolvingTime: 4511.76,
                    Key.Nodes: 51033,
                    Key.SolverStatus: Key.SolverStatusCodes.Optimal }, {
                    Key.PrimalBound:-5,
                    Key.DualBound:-5} ],
                "cplex1271-app1-2" : [ {
                    Key.Solver: "CPLEX",
                    Key.Version: "12.7.1.0",
                    Key.Nodes: 1415,
                    Key.SolverStatus: Key.SolverStatusCodes.Optimal }, {
                    Key.PrimalBound:-41,
                    Key.DualBound:-41} ],
                "cplex1271-bab5" : [ {
                    Key.Solver: "CPLEX",
                    Key.Version: "12.7.1.0",
                    Key.Nodes: 101234,
                    Key.ObjectiveSense: Key.ObjectiveSenseCode.MINIMIZE,
                    Key.SolverStatus: Key.SolverStatusCodes.Optimal }, {
                    Key.PrimalBound:-106411.84,
                    Key.DualBound:-106411.84} ],
                "cplex1271-dfn-gwin-UUM" : [ {
                    Key.Solver: "CPLEX",
                    Key.Version: "12.7.1.0",
                    Key.Nodes: 16132,
                    Key.ObjectiveSense: Key.ObjectiveSenseCode.MINIMIZE,
                    Key.SolverStatus: Key.SolverStatusCodes.Optimal }, {
                    Key.PrimalBound: 38752,
                    Key.DualBound: 38752} ],
                "cplex1271-enlight14" : [ {
                    Key.Solver: "CPLEX",
                    Key.Version: "12.7.1.0",
                    Key.Nodes: 0,
                    Key.ObjectiveSense: Key.ObjectiveSenseCode.MINIMIZE,
                    Key.SolverStatus: Key.SolverStatusCodes.Infeasible }, {
                    Key.PrimalBound: None,
                    Key.DualBound: None} ],
                "cplex1271-satellites1-25" : [ {
                    Key.Solver: "CPLEX",
                    Key.Version: "12.7.1.0",
                    Key.Nodes: 2942,
                    Key.ObjectiveSense: Key.ObjectiveSenseCode.MINIMIZE,
                    Key.SolverStatus: Key.SolverStatusCodes.Optimal }, {
                    Key.PrimalBound:-5,
                    Key.DualBound:-5} ],
                "cplex1280-bab5" : [ {
                    Key.Solver: "CPLEX",
                    Key.Version: "12.8.0.0",
                    Key.SolvingTime: 1551.53,
                    Key.Nodes: 51737,
                    Key.SolverStatus: Key.SolverStatusCodes.Optimal }, {
                    Key.PrimalBound: -1.0641184010e+05,
                    Key.DualBound: -1.0641184010e+05} ],
                "cplex1280-enlight13" : [ {
                    Key.Solver: "CPLEX",
                    Key.Version: "12.8.0.0",
                    Key.SolvingTime: 0.00,
                    Key.Nodes: 0,
                    Key.SolverStatus: Key.SolverStatusCodes.Optimal }, {
                    Key.PrimalBound: 7.1000000000e+01,
                    Key.DualBound: 7.1000000000e+01} ],
                "cplex1280-enlight14" : [ {
                    Key.Solver: "CPLEX",
                    Key.Version: "12.8.0.0",
                    Key.SolvingTime: 0.00,
                    Key.Nodes: 0,
                    Key.SolverStatus: Key.SolverStatusCodes.Infeasible }, {
                    Key.PrimalBound: None,
                    Key.DualBound: None} ],
                "cplex1280-mine-90-10" : [ {
                    Key.Solver: "CPLEX",
                    Key.Version: "12.8.0.0",
                    Key.SolvingTime: 924.71,
                    Key.Nodes: 388227,
                    Key.SolverStatus: Key.SolverStatusCodes.Optimal }, {
                    Key.PrimalBound: -7.8430233763e+08,
                    Key.DualBound: -7.8430233763e+08} ],
                "cplex1280-satellites1-25" : [ {
                    Key.Solver: "CPLEX",
                    Key.Version: "12.8.0.0",
                    Key.SolvingTime: 216.80,
                    Key.Nodes: 3896,
                    Key.SolverStatus: Key.SolverStatusCodes.Optimal }, {
                    Key.PrimalBound: -5.0000000000e+00,
                    Key.DualBound: -5.0000000000e+00} ],
                "cplex1280-tanglegram2" : [ {
                    Key.Solver: "CPLEX",
                    Key.Version: "12.8.0.0",
                    Key.SolvingTime: 0.98,
                    Key.Nodes: 3,
                    Key.SolverStatus: Key.SolverStatusCodes.Optimal }, {
                    Key.PrimalBound: 4.4300000000e+02,
                    Key.DualBound: 4.4300000000e+02} ],
                "gurobi700-app1-2" : [ {
                    Key.Solver: "GUROBI",
                    Key.Version: "7.0.0",
                    Key.SolvingTime: 46.67,
                    Key.Nodes: 526,
                    Key.SolverStatus: Key.SolverStatusCodes.Optimal }, {
                    Key.PrimalBound:-41 ,
                    Key.DualBound:-41} ],
                "gurobi700-bab5" : [ {
                    Key.Solver: "GUROBI",
                    Key.Version: "7.0.0",
                    Key.SolvingTime: 65.35,
                    Key.Nodes: 534,
                    Key.SolverStatus: Key.SolverStatusCodes.Optimal }, {
                    Key.PrimalBound:-106411.84 ,
                    Key.DualBound:-106411.84} ],
                "gurobi700-dfn-gwin-UUM" : [ {
                    Key.Solver: "GUROBI",
                    Key.Version: "7.0.0",
                    Key.SolvingTime: 388.98,
                    Key.Nodes: 170061,
                    Key.SolverStatus: Key.SolverStatusCodes.Optimal }, {
                    Key.PrimalBound: 38752 ,
                    Key.DualBound: 38752} ],
                "gurobi700-enlight14" : [ {
                    Key.Solver: "GUROBI",
                    Key.Version: "7.0.0",
                    Key.SolvingTime: 0.00,
                    Key.Nodes: 0,
                    Key.SolverStatus: Key.SolverStatusCodes.Infeasible }, {
                    Key.PrimalBound: None,
                    Key.DualBound: None} ],
                "gurobi700-satellites1-25" : [ {
                    Key.Solver: "GUROBI",
                    Key.Version: "7.0.0",
                    Key.SolvingTime: 59.70,
                    Key.Nodes: 1170,
                    Key.SolverStatus: Key.SolverStatusCodes.Optimal }, {
                    Key.PrimalBound:-5 ,
                    Key.DualBound:-5} ],
                "gurobi800-bab5" : [ {
                    Key.Solver: "GUROBI",
                    Key.Version: "8.0.0",
                    Key.SolvingTime: 25.52,
                    Key.Nodes: 1,
                    Key.SolverStatus: Key.SolverStatusCodes.Optimal }, {
                    Key.PrimalBound: -1.064118401000e+05,
                    Key.DualBound: -1.064118401000e+05} ],
                "gurobi800-enlight13" : [ {
                    Key.Solver: "GUROBI",
                    Key.Version: "8.0.0",
                    Key.SolvingTime: 0.00,
                    Key.Nodes: 0,
                    Key.SolverStatus: Key.SolverStatusCodes.Optimal }, {
                    Key.PrimalBound: 7.100000000000e+01,
                    Key.DualBound: 7.100000000000e+01} ],
                "gurobi800-enlight14" : [ {
                    Key.Solver: "GUROBI",
                    Key.Version: "8.0.0",
                    Key.SolvingTime: 0.00,
                    Key.Nodes: 0,
                    Key.SolverStatus: Key.SolverStatusCodes.Infeasible }, {
                    Key.PrimalBound: None,
                    Key.DualBound: None} ],
                "gurobi800-mine-90-10" : [ {
                    Key.Solver: "GUROBI",
                    Key.Version: "8.0.0",
                    Key.SolvingTime: 769.45,
                    Key.Nodes: 1181932,
                    Key.SolverStatus: Key.SolverStatusCodes.Optimal }, {
                    Key.PrimalBound: -7.843023376332e+08,
                    Key.DualBound: -7.843023376332e+08} ],
                "gurobi800-satellites1-25" : [ {
                    Key.Solver: "GUROBI",
                    Key.Version: "8.0.0",
                    Key.SolvingTime: 40.86,
                    Key.Nodes: 380,
                    Key.SolverStatus: Key.SolverStatusCodes.Optimal }, {
                    Key.PrimalBound: -5.000000000000e+00,
                    Key.DualBound: -5.000000000000e+00} ],
                "gurobi800-tanglegram2" : [ {
                    Key.Solver: "GUROBI",
                    Key.Version: "8.0.0",
                    Key.SolvingTime: 0.57,
                    Key.Nodes: 1,
                    Key.SolverStatus: Key.SolverStatusCodes.Optimal }, {
                    Key.PrimalBound: 4.430000000000e+02,
                    Key.DualBound: 4.430000000000e+02} ],
                "xpress300103-app1-2" : [ {
                    Key.Solver: "XPRESS",
                    Key.Version: "30.01.03",
                    Key.SolvingTime: 29,
                    Key.Nodes: 265,
                    Key.ObjectiveSense: Key.ObjectiveSenseCode.MINIMIZE,
                    Key.SolverStatus: Key.SolverStatusCodes.Optimal }, {
                    Key.PrimalBound:-41,
                    Key.DualBound:-41} ],
                "xpress300103-bab5" : [ {
                    Key.Solver: "XPRESS",
                    Key.Version: "30.01.03",
                    Key.SolvingTime: 7200,
                    Key.Nodes: 71853,
                    Key.ObjectiveSense: Key.ObjectiveSenseCode.MINIMIZE,
                    Key.SolverStatus: Key.SolverStatusCodes.TimeLimit }, {
                    Key.PrimalBound:-106411.84,
                    Key.DualBound:-106701.8161} ],
                "xpress300103-dfn-gwin-UUM" : [ {
                    Key.Solver: "XPRESS",
                    Key.Version: "30.01.03",
                    Key.SolvingTime:181 ,
                    Key.Nodes: 158849,
                    Key.ObjectiveSense: Key.ObjectiveSenseCode.MINIMIZE,
                    Key.SolverStatus: Key.SolverStatusCodes.Optimal }, {
                    Key.PrimalBound: 38752,
                    Key.DualBound: 38748} ],
                "xpress300103-enlight14" : [ {
                    Key.Solver: "XPRESS",
                    Key.Version: "30.01.03",
                    Key.SolvingTime: 0,
                    Key.Nodes: 0,
                    Key.ObjectiveSense: Key.ObjectiveSenseCode.MINIMIZE,
                    Key.SolverStatus: Key.SolverStatusCodes.Infeasible }, {
                    Key.PrimalBound: 1e+40,
                    Key.DualBound: 1e+40} ],
                "xpress300103-satellites1-25" : [ {
                    Key.Solver: "XPRESS",
                    Key.Version: "30.01.03",
                    Key.SolvingTime: 228,
                    Key.Nodes: 5937,
                    Key.ObjectiveSense: Key.ObjectiveSenseCode.MINIMIZE,
                    Key.SolverStatus: Key.SolverStatusCodes.Optimal }, {
                    Key.PrimalBound:-5 ,
                    Key.DualBound:-5} ],
                "xpress330103-bab5" : [ {
                    Key.Solver: "XPRESS",
                    Key.Version: "33.01.03",
                    Key.SolvingTime: 7200,
                    Key.Nodes: 24575,
                    Key.ObjectiveSense: Key.ObjectiveSenseCode.MINIMIZE,
                    Key.SolverStatus: Key.SolverStatusCodes.TimeLimit }, {
                    Key.PrimalBound: -106361.339104,
                    Key.DualBound: -106600.8564439218171173707} ],
                "xpress330103-enlight13" : [ {
                    Key.Solver: "XPRESS",
                    Key.Version: "33.01.03",
                    Key.SolvingTime: 0,
                    Key.Nodes: 0,
                    Key.ObjectiveSense: Key.ObjectiveSenseCode.MINIMIZE,
                    Key.SolverStatus: Key.SolverStatusCodes.Optimal }, {
                    Key.PrimalBound: 71,
                    Key.DualBound: 71} ],
                "xpress330103-enlight14" : [ {
                    Key.Solver: "XPRESS",
                    Key.Version: "33.01.03",
                    Key.SolvingTime: 84,
                    Key.Nodes: 1,
                    Key.ObjectiveSense: Key.ObjectiveSenseCode.MINIMIZE,
                    Key.SolverStatus: Key.SolverStatusCodes.Optimal }, {
                    Key.PrimalBound: 52200,
                    Key.DualBound: 52200.00000000001455191523} ],
                "xpress330103-mine-90-10" : [ {
                    Key.Solver: "XPRESS",
                    Key.Version: "33.01.03",
                    Key.SolvingTime: 5,
                    Key.Nodes: 505,
                    Key.ObjectiveSense: Key.ObjectiveSenseCode.MINIMIZE,
                    Key.SolverStatus: Key.SolverStatusCodes.Optimal }, {
                    Key.PrimalBound: -566395707.871,
                    Key.DualBound: -566395707.8708435297012329} ],
                "xpress330103-satellites1-25" : [ {
                    Key.Solver: "XPRESS",
                    Key.Version: "33.01.03",
                    Key.SolvingTime: 99,
                    Key.Nodes: 7917,
                    Key.ObjectiveSense: Key.ObjectiveSenseCode.MINIMIZE,
                    Key.SolverStatus: Key.SolverStatusCodes.Optimal }, {
                    Key.PrimalBound: -5.00000000001,
                    Key.DualBound: -5.000000000005489830812166} ],
                "xpress330103-tanglegram2" : [ {
                    Key.Solver: "XPRESS",
                    Key.Version: "33.01.03",
                    Key.SolvingTime: 0,
                    Key.Nodes: 5,
                    Key.ObjectiveSense: Key.ObjectiveSenseCode.MINIMIZE,
                    Key.SolverStatus: Key.SolverStatusCodes.Optimal }, {
                    Key.PrimalBound: 443,
                    Key.DualBound: 443} ],
                "mipcl131-app1-2" : [ {
                    Key.Solver: "MIPCL",
                    Key.Version: "1.3.1",
                    Key.SolverStatus: Key.SolverStatusCodes.Optimal }, {
                    Key.PrimalBound:-41,
                    Key.DualBound:-41} ],
                "mipcl131-bab5" : [ {
                    Key.Solver: "MIPCL",
                    Key.Version: "1.3.1",
                    Key.SolverStatus: Key.SolverStatusCodes.Optimal }, {
                    Key.PrimalBound:-106411.84,
                    Key.DualBound:-106411.84} ],
                "mipcl131-dfn-gwin-UUM" : [ {
                    Key.Solver: "MIPCL",
                    Key.Version: "1.3.1",
                    Key.SolverStatus: Key.SolverStatusCodes.Optimal }, {
                    Key.PrimalBound: 38752,
                    Key.DualBound: 38752} ],
                "mipcl131-enlight14" : [ {
                    Key.Solver: "MIPCL",
                    Key.Version: "1.3.1",
                    Key.SolverStatus: Key.SolverStatusCodes.Infeasible }, {
                    Key.PrimalBound: None ,
                    Key.DualBound: None} ],
                "mipcl131-satellites1-25" : [ {
                    Key.Solver: "MIPCL",
                    Key.Version: "1.3.1",
                    Key.SolverStatus: Key.SolverStatusCodes.Optimal }, {
                    Key.PrimalBound:-5 ,
                    Key.DualBound:-5} ],
                "mipcl152-bab5" : [ {
                    Key.Solver: "MIPCL",
                    Key.Version: "1.5.2",
                    Key.SolvingTime: 514.635,
                    Key.Nodes: 264,
                    Key.SolverStatus: Key.SolverStatusCodes.Optimal }, {
                    Key.PrimalBound: -106411.8401,
                    Key.DualBound: -106411.8401} ],
                "mipcl152-bnatt350" : [ {
                    Key.Solver: "MIPCL",
                    Key.Version: "1.5.2",
                    Key.SolvingTime: 7199.330,
                    Key.Nodes: 117400,
                    Key.SolverStatus: Key.SolverStatusCodes.TimeLimit }, {
                    Key.PrimalBound: None,
                    Key.DualBound: -0.0000} ],
                "mipcl152-enlight13" : [ {
                    Key.Solver: "MIPCL",
                    Key.Version: "1.5.2",
                    Key.SolvingTime: 70.477,
                    Key.Nodes: 280,
                    Key.SolverStatus: Key.SolverStatusCodes.Optimal }, {
                    Key.PrimalBound: 71.0000,
                    Key.DualBound: 71.0000} ],
                "mipcl152-enlight14" : [ {
                    Key.Solver: "MIPCL",
                    Key.Version: "1.5.2",
                    Key.SolvingTime: 280.405,
                    Key.Nodes: 1025,
                    Key.SolverStatus: Key.SolverStatusCodes.Infeasible }, {
                    Key.PrimalBound: None,
                    Key.DualBound: None} ],
                "mipcl152-mine-90-10" : [ {
                    Key.Solver: "MIPCL",
                    Key.Version: "1.5.2",
                    Key.SolvingTime: 7.370,
                    Key.Nodes: 1930,
                    Key.SolverStatus: Key.SolverStatusCodes.Optimal }, {
                    Key.PrimalBound: -566395707.8708,
                    Key.DualBound: -566395707.8708} ],
                "mipcl152-satellites1-25" : [ {
                    Key.Solver: "MIPCL",
                    Key.Version: "1.5.2",
                    Key.SolvingTime: 2999.199,
                    Key.Nodes: 14031,
                    Key.SolverStatus: Key.SolverStatusCodes.Optimal }, {
                    Key.PrimalBound: -5.0000,
                    Key.DualBound: -5.0000} ],
                "mipcl152-tanglegram2" : [ {
                    Key.Solver: "MIPCL",
                    Key.Version: "1.5.2",
                    Key.SolvingTime: 35.829,
                    Key.Nodes: 1,
                    Key.SolverStatus: Key.SolverStatusCodes.Optimal }, {
                    Key.PrimalBound: 443.0000,
                    Key.DualBound: 443.0000} ],
                "scip400-infeasible" : [ {
                    Key.Solver: "SCIP",
                    Key.Version: "4.0.0",
                    Key.Nodes: 1,
                    Key.SolvingTime: 0.02,
                    Key.GitHash: "ea0b6dd",
                    "mode": "optimized",
                    "LPSolver": "SoPlex 3.0.0",
                    "SpxGitHash": "b0cccbd",
                    Key.SolverStatus: Key.SolverStatusCodes.Infeasible }, {
                    Key.PrimalBound:+1.00000000000000e+20,
                    Key.DualBound:+1.00000000000000e+20} ],
                "scip400-memorylimit" : [ {
                    Key.Solver: "SCIP",
                    Key.Version: "4.0.0",
                    Key.Nodes: 1778883,
                    Key.SolvingTime: 6807.85,
                    Key.GitHash: "ea0b6dd",
                    "mode": "optimized",
                    "LPSolver": "SoPlex 3.0.0",
                    "SpxGitHash": "b0cccbd",
                    Key.SolverStatus: Key.SolverStatusCodes.MemoryLimit }, {
                    Key.PrimalBound:+1.49321500000000e+06,
                    Key.DualBound:+1.49059347656250e+06} ],
                "scip400-optimal" : [ {
                    Key.Solver: "SCIP",
                    Key.Version: "4.0.0",
                    Key.Nodes: 126,
                    Key.SolvingTime: 0.79,
                    Key.GitHash: "dd19a7b",
                    "mode": "optimized",
                    "LPSolver": "CPLEX 12.6.0.0",
                    "SpxGitHash": None,
                    Key.SolverStatus: Key.SolverStatusCodes.Optimal }, {
                    Key.PrimalBound:+3.36000000000000e+03,
                    Key.DualBound:+3.36000000000000e+03} ],
                "scip400-timelimit" : [ {
                    Key.Solver: "SCIP",
                    Key.Version: "4.0.0",
                    Key.Nodes: 101678,
                    Key.SolvingTime: 600.00,
                    Key.GitHash: "dd19a7b",
                    "mode": "optimized",
                    "LPSolver": "CPLEX 12.6.0.0",
                    "SpxGitHash": None,
                    Key.SolverStatus: Key.SolverStatusCodes.TimeLimit }, {
                    Key.PrimalBound:+1.16800000000000e+03,
                    Key.DualBound:+1.13970859166290e+03} ],
                "scip400-crashed" : [ {
                    Key.Solver: "SCIP",
                    Key.Version: "4.0.0",
                    Key.Nodes: None,
                    Key.SolvingTime: None,
                    Key.GitHash: "dd19a7b",
                    "mode": "optimized",
                    "LPSolver": "CPLEX 12.6.0.0",
                    "SpxGitHash": None,
                    Key.SolverStatus: Key.SolverStatusCodes.Crashed }, {
                    Key.PrimalBound: None,
                    Key.DualBound: None} ],
                "scip500-bab5" : [ {
                    Key.Solver: "SCIP",
                    Key.Version: "5.0.0",
                    Key.SolvingTime: 7200.00,
                    Key.Nodes: 120255,
                    Key.GitHash: "3bbd232",
                    "mode": "optimized",
                    "LPSolver": "SoPlex 3.1.0",
                    "SpxGitHash": "5147d37",
                    Key.SolverStatus: Key.SolverStatusCodes.TimeLimit }, {
                    Key.PrimalBound:-1.06411840100000e+05,
                    Key.DualBound:-1.06736016607273e+05} ],
                "scip500-enlight13" : [ {
                    Key.Solver: "SCIP",
                    Key.Version: "5.0.0",
                    Key.SolvingTime: 0.01,
                    Key.Nodes: 1,
                    Key.GitHash: "3bbd232",
                    "mode": "optimized",
                    "LPSolver": "SoPlex 3.1.0",
                    "SpxGitHash": "5147d37",
                    Key.SolverStatus: Key.SolverStatusCodes.Optimal }, {
                    Key.PrimalBound:+7.10000000000000e+01,
                    Key.DualBound:+7.10000000000000e+01} ],
                "scip500-enlight14" : [ {
                    Key.Solver: "SCIP",
                    Key.Version: "5.0.0",
                    Key.SolvingTime: 0.01,
                    Key.Nodes: 1,
                    Key.GitHash: "3bbd232",
                    "mode": "optimized",
                    "LPSolver": "CPLEX 12.8.0.0",
                    "SpxGitHash": None,
                    Key.SolverStatus: Key.SolverStatusCodes.Infeasible }, {
                    Key.PrimalBound:+1.00000000000000e+20,
                    Key.DualBound:+1.00000000000000e+20} ],
                "scip500-mine-90-10" : [ {
                    Key.Solver: "SCIP",
                    Key.Version: "5.0.0",
                    Key.SolvingTime: 45.86,
                    Key.Nodes: 1483,
                    Key.GitHash: "3bbd232",
                    "mode": "optimized",
                    "LPSolver": "SoPlex 3.1.0",
                    "SpxGitHash": "5147d37",
                    Key.SolverStatus: Key.SolverStatusCodes.Optimal }, {
                    Key.PrimalBound:-5.66395707870830e+08,
                    Key.DualBound:-5.66395707870830e+08} ],
                "scip500-satellites1-25" : [ {
                    Key.Solver: "SCIP",
                    Key.Version: "5.0.0",
                    Key.SolvingTime: 454.56,
                    Key.Nodes: 424,
                    Key.GitHash: "3bbd232",
                    "mode": "optimized",
                    "LPSolver": "CPLEX 12.8.0.0",
                    "SpxGitHash": None,
                    Key.SolverStatus: Key.SolverStatusCodes.Optimal }, {
                    Key.PrimalBound:-4.99999999999994e+00,
                    Key.DualBound:-4.99999999999994e+00} ],
                "scip500-tanglegram2" : [ {
                    Key.Solver: "SCIP",
                    Key.Version: "5.0.0",
                    Key.SolvingTime: 5.82,
                    Key.Nodes: 3,
                    Key.GitHash: "3bbd232",
                    "mode": "optimized",
                    "LPSolver": "SoPlex 3.1.0",
                    "SpxGitHash": "5147d37",
                    Key.SolverStatus: Key.SolverStatusCodes.Optimal }, {
                    Key.PrimalBound:+4.43000000000000e+02,
                    Key.DualBound:+4.43000000000000e+02} ],
                }

    solvers = []

    def setUp(self):
        self.solvers.append([SCIPSolver(), "SCIP"])
        self.solvers.append([GurobiSolver(), "GUROBI"])
        self.solvers.append([CplexSolver(), "CPLEX"])
        self.solvers.append([CbcSolver(), "CBC"])
        self.solvers.append([XpressSolver(), "XPRESS"])
        self.solvers.append([MipclSolver(), "MIPCL"])
        self.activeSolver = self.solvers[0][SOLVER]

    def tearDown(self):
        pass

    def testSolverIDs(self):
        for solver, name in self.solvers:
            self.assertEqual(name, solver.getData(Key.Solver))

    def testData(self):
        for filename in self.fileinfo.keys():
            file = self.getFileName(filename)
            self.readFile(file)
            for key in self.fileinfo.get(filename)[PRECISE].keys():
                self.assertPrecise(filename, key)
            for key in self.fileinfo.get(filename)[ALMOST].keys():
                self.assertAlmost(filename, key)

    def assertPrecise(self, filename, key):
        refvalue = self.fileinfo.get(filename)[PRECISE].get(key)
        self.assertEqual(refvalue, self.activeSolver.getData(key), "Wrong key value {}:{} parsed by solver {} from file {}".format(key, self.activeSolver.getData(key), self.activeSolver.getName(), filename))

    def assertAlmost(self, filename, key):
        refbound = self.fileinfo.get(filename)[ALMOST].get(key)
        if refbound is not None:
            self.assertIsNotNone(self.activeSolver.getData(key), "solver {} did not find a value {} in file {}".format(self.activeSolver.solverId, key, filename))
            self.assertAlmostEqual(refbound, self.activeSolver.getData(key), delta = 1e-1,
                                   msg = "{0} has {1} as {2}, should be {3}".format(filename, self.activeSolver.getData(key), key, refbound))
        else:
            self.assertIsNone(self.activeSolver.getData(key), "'{}' should have 'None' as {}".format(filename, key))

    def readFile(self, filename):
        self.readSolver(filename)
        self.activeSolver.reset()
        with open(filename, "r") as f:
            for line in f:
                self.activeSolver.readLine(line)

    def readSolver(self, filename):
        with open(filename) as f:
            for i, line in enumerate(f):
                for solver, name in self.solvers:
                    if solver.recognizeOutput(line):
                        self.activeSolver = solver
                        return

    def getFileName(self, basename):
        return os.path.join(DATADIR, "{}.{}".format(basename, "out"))

if __name__ == "__main__":
    unittest.main()



