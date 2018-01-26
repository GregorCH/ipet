'''
Created on 25.01.2018

@author: gregor
'''
import unittest
from ipet.evaluation.Validation import Interval as I 
from ipet.evaluation import Validation
from ipet.Key import ObjectiveSenseCode as osc
from ipet import Key
import numpy
import pandas as pd
from ipet.Key import SolverStatusCodes as ssc
from ipet.Key import ProblemStatusCodes as psc

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


class ValidationTest(unittest.TestCase):


    def testIntervals(self):
        intersecting_intervals = [
            [I((1,3)), I((2,3))], # simple intervals
            [I((1,2)), I((2,3))], # intersect in a point
            [I((2,2)), I((2,3))], # point and interval
            [I((2,2),0), I((2,3),0)], # point and interval with zero tolerance 
            [I((1e9,1e9), tol=1e-1), I((0.99 * 1e9, 0.99 * 1e9))], # larger tolerance
            [I((0,1e6)), I((1e6+1,2 * 1e6)) ] # nonintersecting intervals at larger scales
            ]
        
        nonintersecting_intervals = [
            [I((2,3)), I((4,5))], # points with small values that are far apart
            [I((0,0.9999), tol=1e-6), I((0.99991,1), tol=0)], # close together, small tolerance
            [I((-2 * 1e-3,-1e-3)), I((1e-3,2 * 1e-3))], #values close to 0.0  
            ]
        
        for i1, i2 in intersecting_intervals:
            self.assertTrue(i1.intersects(i2), "Intervals {} and {} should intersect".format(i1, i2))
            
        for i1, i2 in nonintersecting_intervals:
            self.assertFalse(i1.intersects(i2), "Intervals {} and {} should not intersect".format(i1, i2))
        

    def testBoundReplacement(self):
        """Test if Null values are replaced correctly 
        """
        v = Validation()
        inftys = [(v.getDbValue, osc.MAXIMIZE),
                  (v.getPbValue, osc.MINIMIZE)]
        
        neginftys = [(v.getDbValue, osc.MINIMIZE),
                  (v.getPbValue, osc.MAXIMIZE)]
        for m, s in inftys:
            self.assertEqual(m(None, s), numpy.inf, "Should be inf")
            
        for m, s in neginftys:
            self.assertEqual(m(None, s), -numpy.inf, "Should be negative inf")
            
            
    def testInstanceData(self):
        """
        test some fake instances
        """
        
        d = pd.DataFrame(
        [#  ProblemName PrimalBound DualBound     Objsense           SolverStatus       Status
                (inf_good,     None,     None,osc.MINIMIZE,    ssc.Infeasible,          psc.Ok),
                (inf_bad,         5,        5,osc.MINIMIZE,    ssc.Optimal,             psc.FailSolOnInfeasibleInstance), 
                (inf_time,     None,     None,osc.MINIMIZE,    ssc.TimeLimit,           psc.TimeLimit),
                (feas_good,       3,     None,osc.MAXIMIZE,    ssc.MemoryLimit,         psc.MemoryLimit),
                (feas_bad,        3,     None,osc.MAXIMIZE,    ssc.Infeasible,          psc.FailDualBound),
                (opt_good,        10,      10,osc.MAXIMIZE,    ssc.Optimal,             psc.Ok),
                (opt_bad,          9,        9,osc.MAXIMIZE,   ssc.Optimal,             psc.FailObjectiveValue),
                (opt_tol,    10-1e-5,  10-1e-5,osc.MAXIMIZE,   ssc.Optimal,             psc.Ok),
                (best_good,       105,     85,osc.MINIMIZE,    ssc.NodeLimit,           psc.NodeLimit),
                (best_dbad,       105,     103,osc.MINIMIZE,   ssc.NodeLimit,           psc.FailObjectiveValue),
                (best_pbad,       85,      85,osc.MINIMIZE,    ssc.Optimal,             psc.FailObjectiveValue),
                ], 
               columns=[Key.ProblemName, Key.PrimalBound, Key.DualBound, Key.ObjectiveSense, Key.SolverStatus, "Status"])
        
        v = Validation()
        v.solufiledict = {
            inf_good : (Validation.__infeas__, None),
            inf_bad : (Validation.__infeas__, None),
            inf_time : (Validation.__infeas__, None),
            feas_good : (Validation.__feas__, Validation.__feas__),
            feas_bad : (Validation.__feas__, Validation.__feas__),
            opt_good : (10,10),
            opt_bad : (10,10),
            opt_tol : (10,10),
            best_good : (100, 90),
            best_pbad : (100, 90),
            best_dbad : (100, 90)
            }
        
        vstatus = d.apply(v.validateSeries, axis = 1)
        
        # compare validation status to expected status codes
        self.assertTrue(numpy.all(vstatus == d.Status), 
                        "Not matching validation status codes:\n{}"
                           
                           "\nData:\n"
                           "{}".format(vstatus[vstatus != d.Status], d[vstatus != d.Status])
                        )
        
        
    def testInconsistencydetection(self):
        """test if inconsistent primal and dual bounds are detected well.
        """
        
        d = pd.DataFrame(
            [
                (opt_good, 100, 90, osc.MINIMIZE, ssc.TimeLimit),
                (opt_good,  95, 85, osc.MINIMIZE, ssc.TimeLimit),
                (opt_bad,  100, 90, osc.MINIMIZE, ssc.TimeLimit),
                (opt_bad,   89, 89, osc.MINIMIZE, ssc.Optimal)
                ],
            columns=[Key.ProblemName, Key.PrimalBound, Key.DualBound, Key.ObjectiveSense, Key.SolverStatus])
        
        print(d)
        
        v = Validation()
        
        v.collectInconsistencies(d)
        
        self.assertNotIn(opt_good, v.inconsistentset, "{} wrongly appears as inconsistent".format(opt_good))
        self.assertIn(opt_bad, v.inconsistentset, "{} should be inconsistent".format(opt_bad))
        
        

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()