'''
Created on 02.08.2017

@author: gregor
'''
import unittest
from ipet.Experiment import Experiment
from ipet.TestRun import TestRun
from ipet import Key
from os import path as osp
DATADIR = osp.join(osp.dirname(__file__), "data")

class PrimalDualBoundHistoryTest(unittest.TestCase):


    def testEmptyLine(self):
        """
        the file in this test contains an empty line during the table output.
        
        In previous IPET versions, IPET would not detect anymore that
        the table continues, and return wrong Primal and dual bound histories.
        """
        correctPbHistory = [(0.1, 0.1176408), (0.1, 0.2329977), (0.2, 0.2333972), (0.2, 0.2425407), (0.2, 0.2458207), (42.6, 0.2529466), (42.7, 0.2533669), (42.9, 0.2566015), (43.0, 0.2580527), (0.14, 0.117640800073596)]
        ex = Experiment()
        ex.addOutputFile(osp.join(DATADIR, "scip-primalintegral-emptyline.out"))
        ex.collectData()
        tr = ex.getTestRuns()[0]
        assert isinstance(tr, TestRun)
        pbHistory = tr.getProblemDataById(0, Key.PrimalBoundHistory)
        
        self.assertListEqual(pbHistory, correctPbHistory, "Lists should be equal\nExpected\t:{}\nGot\t:{}\n".format(correctPbHistory, pbHistory))
        
    
        


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testEmptyLine']
    unittest.main()