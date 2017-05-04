'''
Created on 04.05.2017

@author: Gregor Hendel
'''
import unittest
import os
DATADIR = os.path.join(os.path.dirname(__file__), "data")
TMPDIR = os.path.join(os.path.dirname(__file__), ".tmp")
from ipet.parsing.Solver import SCIPSolver
from ipet import Key

class SCIPSolverTest(unittest.TestCase):

    file2primalbound = {
        "scip-infeasible" :+1.00000000000000e+20,
        "scip-memorylimit" :+1.49321500000000e+06,
        "scip-optimal"  :+3.36000000000000e+03,
        "scip-timelimit":+1.16800000000000e+03,
        "scip-crashed" : None
        }

    file2dualbound = {
        "scip-infeasible":+1.00000000000000e+20,
        "scip-memorylimit":+1.49059347656250e+06,
        "scip-optimal":+3.36000000000000e+03,
        "scip-timelimit":+1.13970859166290e+03,
        "scip-crashed" : None
        }

    def setUp(self):
        self._s = SCIPSolver()

    def tearDown(self):
        pass

    def testSCIPSolverID(self):
        self.assertEqual("SCIP", self._s.getData(Key.Solver))

    def readFile(self, filename):
        with open(filename, "r") as f:
            for line in f:
                self._s.readLine(line)

    def getFileName(self, basename):
        return os.path.join(DATADIR, "{}.{}".format(basename, "out"))

    def assertFileStatus(self, filename, statuscode):
        fname = self.getFileName(filename)
        self.readFile(fname)
        self.assertEqual(self._s.getData(Key.SolverStatus), statuscode)

    def testStatusOptimal(self):
        self.assertFileStatus("scip-optimal", Key.SolverStatusCodes.Optimal)

    def testStatusInfeasible(self):
        self.assertFileStatus("scip-infeasible", Key.SolverStatusCodes.Infeasible)

    def testStatusMemoryLimit(self):
        self.assertFileStatus("scip-memorylimit", Key.SolverStatusCodes.MemoryLimit)

    def testStatusTimeLimit(self):
        self.assertFileStatus("scip-timelimit", Key.SolverStatusCodes.TimeLimit)

    def testStatusCrashed(self):
        self.assertFileStatus("scip-crashed", Key.SolverStatusCodes.Crashed)

    def assertBound(self, filename, key = Key.PrimalBound):
        if key == Key.PrimalBound:
            refbound = self.file2primalbound.get(filename)
        else:
            refbound = self.file2dualbound.get(filename)
        fname = self.getFileName(filename)
        self.readFile(fname)
        if refbound is not None:
            self.assertAlmostEqual(refbound, self._s.getData(key), delta = 1e-6,
                                   msg = "{0} has {1} as {2}, should be {3}".format(filename, self._s.getData(key), key, refbound))
        else:
            self.assertIsNone(self._s.getData(key), "'{}' should have 'None' as {}".format(filename, key))

        self._s.reset()

    def testPrimalBounds(self):
        for filename in self.file2primalbound.keys():
            self.assertBound(filename, Key.PrimalBound)

    def testDualBounds(self):
        for filename in self.file2dualbound.keys():
            self.assertBound(filename, Key.DualBound)




class XpressSolverTest(unittest.TestCase):
    pass


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
