'''
Created on 25.01.2018

@author: gregor
'''
import unittest
from ipet.validation import Validation
from ipet.Key import ObjectiveSenseCode as osc
from ipet import Key
import numpy
import pandas as pd
from ipet.Key import SolverStatusCodes as ssc
from ipet.Key import ProblemStatusCodes as psc
from ipet.misc import getInfinity as infty

# infeasible instances
inf_good = "inf_good"
inf_bad = "inf_bad"
inf_time = "inf_time"

# feasible instances (it is bad to state infeasible)
feas_good = "feas_good"
feas_bad = "feas_bad"

# instances for which an optimal solution is known
opt_good = "opt_good"
opt_tol = "opt_tol"
opt_bad = "opt_bad"

# best instances for which also a dual bound is known
best_good = "best_good"
best_pbad = "best_pbad"
best_dbad = "best_dbad"

# instances for which no reference exists for which both solvers consistently report infeasibility
both_infeasible = "both_infeasible"

# instances that crashed
opt_abort = "opt_abort"
opt_readerror = "opt_readerror"

# an instance that is partially inconsistent
part_inconsistent = "part_inconsistent"


class ValidationTest(unittest.TestCase):


    def testBoundReplacement(self):
        """Test if Null values are replaced correctly 
        """
        v = Validation()
        inftys = [(v.getDbValue, osc.MAXIMIZE),
                  (v.getPbValue, osc.MINIMIZE)]

        neginftys = [(v.getDbValue, osc.MINIMIZE),
                  (v.getPbValue, osc.MAXIMIZE)]
        for m, s in inftys:
            self.assertEqual(m(None, s), infty(), "Should be inf")

        for m, s in neginftys:
            self.assertEqual(m(None, s), -infty(), "Should be negative inf")

    def compareValidationStatus(self, d : pd.DataFrame, v : Validation):
        vstatus = d.apply(v.validateSeries, axis = 1)

        # compare validation status to expected status codes
        self.assertTrue(numpy.all(vstatus == d.Status),
                        "Not matching validation status codes:\n{}"

                           "\nData:\n"
                           "{}".format(vstatus[vstatus != d.Status], d[vstatus != d.Status])
                        )


    def testInstanceData(self):
        """
        test some fake instances
        """

        d = pd.DataFrame(
        [  #  ProblemName PrimalBound DualBound     Objsense           SolverStatus       Status
                (inf_good, None, None, osc.MINIMIZE, ssc.Infeasible, psc.Ok),
                (inf_bad, 5, 5, osc.MINIMIZE, ssc.Optimal, psc.FailSolOnInfeasibleInstance),
                (inf_time, None, None, osc.MINIMIZE, ssc.TimeLimit, psc.TimeLimit),
                (feas_good, 3, None, osc.MAXIMIZE, ssc.MemoryLimit, psc.MemoryLimit),
                (feas_bad, 3, None, osc.MAXIMIZE, ssc.Infeasible, psc.FailDualBound),
                (opt_good, 10, 10, osc.MAXIMIZE, ssc.Optimal, psc.Ok),
                (opt_bad, 9, 9, osc.MAXIMIZE, ssc.Optimal, psc.FailDualBound),
                (opt_tol, 10 - 1e-5, 10 - 1e-5, osc.MAXIMIZE, ssc.Optimal, psc.Ok),
                (best_good, 105, 85, osc.MINIMIZE, ssc.NodeLimit, psc.NodeLimit),
                (best_dbad, 105, 103, osc.MINIMIZE, ssc.NodeLimit, psc.FailDualBound),
                (best_pbad, 85, 85, osc.MINIMIZE, ssc.Optimal, psc.FailObjectiveValue),
                (opt_abort, None, None, osc.MINIMIZE, ssc.Crashed, psc.FailAbort),
                (opt_readerror, None, None, osc.MINIMIZE, ssc.Readerror, psc.FailReaderror),
                ],
               columns = [Key.ProblemName, Key.PrimalBound, Key.DualBound, Key.ObjectiveSense, Key.SolverStatus, "Status"])

        v = Validation()
        v.referencedict = {
            inf_good : (Validation.__infeas__, None),
            inf_bad : (Validation.__infeas__, None),
            inf_time : (Validation.__infeas__, None),
            feas_good : (Validation.__feas__, Validation.__feas__),
            feas_bad : (Validation.__feas__, Validation.__feas__),
            opt_good : (10, 10),
            opt_bad : (10, 10),
            opt_tol : (10, 10),
            best_good : (100, 90),
            best_pbad : (100, 90),
            best_dbad : (100, 90),
            opt_abort : (1, 1),
            opt_readerror : (1, 1)
            }


        self.compareValidationStatus(d, v)


    def testInconsistencydetection(self):
        """test if inconsistent primal and dual bounds are detected well.
        """

        d = pd.DataFrame(
            [
                (opt_good, 100, 90, osc.MINIMIZE, ssc.TimeLimit, psc.TimeLimit),
                (opt_good, 95, 85, osc.MINIMIZE, ssc.TimeLimit, psc.TimeLimit),
                (opt_bad, 100, 90, osc.MINIMIZE, ssc.TimeLimit, psc.FailInconsistent),
                (opt_bad, 89, 89, osc.MINIMIZE, ssc.Optimal, psc.FailInconsistent),
                (part_inconsistent, 12, 12, osc.MINIMIZE, ssc.Optimal, psc.FailDualBound),
                (part_inconsistent, 10, 10, osc.MINIMIZE, ssc.Optimal, psc.FailInconsistent),
                (part_inconsistent, 9, 9, osc.MINIMIZE, ssc.Optimal, psc.FailInconsistent),
                (both_infeasible, numpy.nan, numpy.nan, osc.MAXIMIZE, ssc.Infeasible, psc.Ok),
                (both_infeasible, numpy.nan, numpy.nan, osc.MAXIMIZE, ssc.Infeasible, psc.Ok),
                ],
            columns = [Key.ProblemName, Key.PrimalBound, Key.DualBound, Key.ObjectiveSense, Key.SolverStatus, "Status"])

        v = Validation()

        v.referencedict = { part_inconsistent :  (10, 0) }

        v.collectInconsistencies(d)

        self.assertNotIn(opt_good, v.inconsistentset, "{} wrongly appears as inconsistent".format(opt_good))
        self.assertNotIn(both_infeasible, v.inconsistentset, "{} wrongly appears as inconsistent".format(both_infeasible))
        self.assertIn(opt_bad, v.inconsistentset, "{} should be inconsistent".format(opt_bad))
        self.assertIn(part_inconsistent, v.inconsistentset, "{} should be inconsistent".format(part_inconsistent))

        self.compareValidationStatus(d, v)

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
