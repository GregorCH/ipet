'''
Created on 04.05.2017

@author: Gregor Hendel
'''
import unittest
import os
from ipet.parsing.Solver import SCIPSolver, GurobiSolver, CplexSolver, CbcSolver, XpressSolver
from ipet import Key
from ipet.parsing.MIPCLSolver import MIPCLSolver

DATADIR = os.path.join(os.path.dirname(__file__), "data")
TMPDIR = os.path.join(os.path.dirname(__file__), ".tmp")

SOLVER = 0
NAME = 1
PRECISE = 0
ALMOST = 1

class SolverTest(unittest.TestCase):
    
    fileinfo = {
                "cbc-app1-2" : [ {
                    Key.Solver: "CBC",
                    Key.Version: "2.9.8",
                    Key.SolverStatus: Key.SolverStatusCodes.TimeLimit }, {
                    Key.SolvingTime: 7132.49,
                    Key.PrimalBound: None,
                    Key.DualBound: -96.111} ],
                "cbc-ash608gpia-3col" : [ {
                    Key.Solver: "CBC",
                    Key.Version: "2.9.8",
                    Key.SolverStatus: Key.SolverStatusCodes.Infeasible }, {
                    Key.SolvingTime: 224.71,
                    Key.PrimalBound: None ,
                    Key.DualBound: None} ],
                "cbc-bab5" : [ {
                    Key.Solver: "CBC",
                    Key.Version: "2.9.8",
                    Key.SolverStatus: Key.SolverStatusCodes.TimeLimit }, {
                    Key.SolvingTime: 7194.79,
                    Key.PrimalBound: -104286.921,
                    Key.DualBound: -111273.306} ],
                "cbc-dfn-gwin-UUM" : [ {
                    Key.Solver: "CBC",
                    Key.Version: "2.9.8",
                    Key.SolverStatus: Key.SolverStatusCodes.Optimal }, {
                    Key.SolvingTime: 725.37,
                    Key.PrimalBound: 38752,
                    Key.DualBound: 38752} ],
                "cbc-enlight14" : [ {
                    Key.Solver: "CBC",
                    Key.Version: "2.9.8",
                    Key.SolverStatus: Key.SolverStatusCodes.TimeLimit }, {
                    Key.SolvingTime: 7131.16,
                    Key.PrimalBound: None,
                    Key.DualBound: 36.768} ],
                "cbc-satellites1-25" : [ {
                    Key.Solver: "CBC",
                    Key.Version: "2.9.8",
                    Key.SolverStatus: Key.SolverStatusCodes.Optimal }, {
                    Key.SolvingTime: 4511.76,
                    Key.PrimalBound: -5,
                    Key.DualBound: -5} ],
                "cplex-app1-2" : [ {
                    Key.Solver: "CPLEX",
                    Key.Version: "12.7.1.0",
                    Key.SolverStatus: Key.SolverStatusCodes.Optimal }, {
                    Key.PrimalBound: -41,
                    Key.DualBound: -41} ],
                "cplex-bab5" : [ {
                    Key.Solver: "CPLEX",
                    Key.Version: "12.7.1.0",
                    Key.SolverStatus: Key.SolverStatusCodes.Optimal }, {
                    Key.PrimalBound: -106411.84,
                    Key.DualBound: -106411.84} ],
                "cplex-dfn-gwin-UUM" : [ {
                    Key.Solver: "CPLEX",
                    Key.Version: "12.7.1.0",
                    Key.SolverStatus: Key.SolverStatusCodes.Optimal }, {
                    Key.PrimalBound: 38752,
                    Key.DualBound: 38752} ],
                "cplex-enlight14" : [ {
                    Key.Solver: "CPLEX",
                    Key.Version: "12.7.1.0",
                    Key.SolverStatus: Key.SolverStatusCodes.Infeasible }, {
                    Key.PrimalBound: None,
                    Key.DualBound: None} ],
                "cplex-satellites1-25" : [ {
                    Key.Solver: "CPLEX",
                    Key.Version: "12.7.1.0",
                    Key.SolverStatus: Key.SolverStatusCodes.Optimal }, {
                    Key.PrimalBound: -5,
                    Key.DualBound: -5} ],
                "gurobi-app1-2" : [ {
                    Key.Solver: "GUROBI",
                    Key.Version: "7.0.0",
                    Key.SolverStatus: Key.SolverStatusCodes.Optimal }, {
                    Key.PrimalBound: -41 ,
                    Key.DualBound: -41} ],
                "gurobi-bab5" : [ {
                    Key.Solver: "GUROBI",
                    Key.Version: "7.0.0",
                    Key.SolverStatus: Key.SolverStatusCodes.Optimal }, {
                    Key.PrimalBound: -106411.84 ,
                    Key.DualBound: -106411.84} ],
                "gurobi-dfn-gwin-UUM" : [ {
                    Key.Solver: "GUROBI",
                    Key.Version: "7.0.0",
                    Key.SolverStatus: Key.SolverStatusCodes.Optimal }, {
                    Key.PrimalBound: 38752 ,
                    Key.DualBound: 38752} ],
                "gurobi-enlight14" : [ {
                    Key.Solver: "GUROBI",
                    Key.Version: "7.0.0",
                    Key.SolverStatus: Key.SolverStatusCodes.Infeasible }, {
                    Key.PrimalBound: None,
                    Key.DualBound: None} ],
                "gurobi-satellites1-25" : [ {
                    Key.Solver: "GUROBI",
                    Key.Version: "7.0.0",
                    Key.SolverStatus: Key.SolverStatusCodes.Optimal }, {
                    Key.PrimalBound: -5 ,
                    Key.DualBound: -5} ],
                "xpress-app1-2" : [ {
                    Key.Solver: "XPRESS",
                    Key.Version: "30.01.03",
                    Key.SolverStatus: Key.SolverStatusCodes.Optimal }, {
                    Key.PrimalBound: -41,
                    Key.DualBound: -41} ],
                "xpress-bab5" : [ {
                    Key.Solver: "XPRESS",
                    Key.Version: "30.01.03",
                    Key.SolverStatus: Key.SolverStatusCodes.TimeLimit }, {
                    Key.PrimalBound: -106411.84,
                    Key.DualBound:-106701.8161} ],
                "xpress-dfn-gwin-UUM" : [ {
                    Key.Solver: "XPRESS",
                    Key.Version: "30.01.03",
                    Key.SolverStatus: Key.SolverStatusCodes.Optimal }, {
                    Key.PrimalBound: 38752,
                    Key.DualBound: 38748} ],
                "xpress-enlight14" : [ {
                    Key.Solver: "XPRESS",
                    Key.Version: "30.01.03",
                    Key.SolverStatus: Key.SolverStatusCodes.Infeasible }, {
                    Key.PrimalBound: None,
                    Key.DualBound: 1e+40} ],
                "xpress-satellites1-25" : [ {
                    Key.Solver: "XPRESS",
                    Key.Version: "30.01.03",
                    Key.SolverStatus: Key.SolverStatusCodes.Optimal }, {
                    Key.PrimalBound: -5 ,
                    Key.DualBound: -5} ],
                "mipcl-app1-2" : [ {
                    Key.Solver: "MIPCL",
                    Key.Version: "1.3.1",
                    Key.SolverStatus: Key.SolverStatusCodes.Optimal }, {
                    Key.PrimalBound:-41,
                    Key.DualBound:-41} ],
                "mipcl-bab5" : [ {
                    Key.Solver: "MIPCL",
                    Key.Version: "1.3.1",
                    Key.SolverStatus: Key.SolverStatusCodes.Optimal }, {
                    Key.PrimalBound:-106411.84,
                    Key.DualBound:-106411.84} ],
                "mipcl-dfn-gwin-UUM" : [ {
                    Key.Solver: "MIPCL",
                    Key.Version: "1.3.1",
                    Key.SolverStatus: Key.SolverStatusCodes.Optimal }, {
                    Key.PrimalBound: 38752,
                    Key.DualBound: 38752} ],
                "mipcl-enlight14" : [ {
                    Key.Solver: "MIPCL",
                    Key.Version: "1.3.1",
                    Key.SolverStatus: Key.SolverStatusCodes.Infeasible }, {
                    Key.PrimalBound: None ,
                    Key.DualBound: None} ],
                "mipcl-satellites1-25" : [ {
                    Key.Solver: "MIPCL",
                    Key.Version: "1.3.1",
                    Key.SolverStatus: Key.SolverStatusCodes.Optimal }, {
                    Key.PrimalBound:-5 ,
                    Key.DualBound:-5} ],
                "scip-infeasible" : [ {
                    Key.Solver: "SCIP",
                    Key.SolverStatus: Key.SolverStatusCodes.Infeasible }, {
                    Key.PrimalBound: +1.00000000000000e+20,
                    Key.DualBound: +1.00000000000000e+20} ],
                "scip-memorylimit" : [ {
                    Key.Solver: "SCIP",
                    Key.SolverStatus: Key.SolverStatusCodes.MemoryLimit }, {
                    Key.PrimalBound: +1.49321500000000e+06,
                    Key.DualBound: +1.49059347656250e+06} ],
                "scip-optimal" : [ {
                    Key.Solver: "SCIP",
                    Key.SolverStatus: Key.SolverStatusCodes.Optimal }, {
                    Key.PrimalBound: +3.36000000000000e+03,
                    Key.DualBound: +3.36000000000000e+03} ],
                "scip-timelimit" : [ {
                    Key.Solver: "SCIP",
                    Key.SolverStatus: Key.SolverStatusCodes.TimeLimit }, {
                    Key.PrimalBound: +1.16800000000000e+03,
                    Key.DualBound: +1.13970859166290e+03} ],
                "scip-crashed" : [ {
                    Key.Solver: "SCIP",
                    Key.SolverStatus: Key.SolverStatusCodes.Crashed }, {
                    Key.PrimalBound: None,
                    Key.DualBound: None} ]
                }
    
    solvers = []
    
    def setUp(self):
        self.solvers.append([SCIPSolver(), "SCIP"])
        self.solvers.append([GurobiSolver(), "GUROBI"])
        self.solvers.append([CplexSolver(), "CPLEX"])
        self.solvers.append([CbcSolver(), "CBC"])
        self.solvers.append([XpressSolver(), "XPRESS"])
        self.solvers.append([MIPCLSolver(), "MIPCL"])
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
        self.assertEqual(refvalue, self.activeSolver.getData(key))

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
    
    
    
