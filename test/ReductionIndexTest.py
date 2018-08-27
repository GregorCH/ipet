'''
Created on 27.07.2017

@author: gregor
'''
import unittest
from ipet.evaluation import IPETEvaluation, IPETEvaluationColumn
import pandas as pd
from ipet import Key
from ipet.concepts.IPETNode import IpetNodeAttributeError
import logging

class HelperExperiment():
    """Helper class that pretends to be joined data from an Experiment
    """
    def __init__(self):
        self.helper_dataframe=pd.DataFrame(
            [
                ["A1", "B1", "C1", 1.0],
                ["A2", "B1", "C1", 2.0],
                ["A1", "B2", "C1", 3.0],
                ["A2", "B2", "C1", 4.0],
                ["A1", "B1", "C2", 5.0],
                ["A2", "B1", "C2", 6.0],
                ["A1", "B2", "C2", 7.0],
                ["A2", "B2", "C2", 8.0],
                ], columns=list("ABCD"))
        self.helper_dataframe[Key.ProblemStatus] = Key.ProblemStatusCodes.Ok

    def getJoinedData(self):
        return self.helper_dataframe


class ReductionIndexTest(unittest.TestCase):


    def setUp(self):
        logger=logging.getLogger()
        logger.setLevel(logging.ERROR)
        self.helper = HelperExperiment()
        self.col = IPETEvaluationColumn(origcolname="D", name="D", reduction="min", reductionindex=2)
        pass


    def tearDown(self):
        pass

    def getPowerSet(self, indexList=list("ABC")):
        from itertools import chain, combinations
        return chain.from_iterable(combinations(indexList,n) for n in range(len(indexList)+1))

    def createAndEvaluateColumn(self, col):
        ev = IPETEvaluation(index="A B C", indexsplit=3)
        ev.addColumn(col)
        ev.evaluate(self.helper)

        return ev

    def checkEntrySize(self, ev, expsize):
        v_counts = ev.getInstanceData()["D"].value_counts()
        gotsize=v_counts.size
        self.assertEqual(gotsize, expsize, "Expecting {} distinct values, have {} in data\n{}\n".format(gotsize, expsize, ev.getInstanceData()))

    def testReductionIndex(self):
        """
        Test all integers between 0 and 4 for the reduction index
        """

        for idx in range(0,4):
            self.col.set_reductionindex(idx)
            ev = self.createAndEvaluateColumn(self.col)
            self.checkEntrySize(ev, 2**idx)


    def testReductionIndexNames(self):
        """
        Test all possible combinations of the index columns A, B, and C as reductionindex
        """
        for s in self.getPowerSet():
            self.col.set_reductionindex(" ".join(s))
            ev = self.createAndEvaluateColumn(self.col)
            self.checkEntrySize(ev, 2**len(s))


    def testDefaultReductionIndex(self):
        """
        Test if all values are preserved if we use the default reduction index of a column
        """
        col = IPETEvaluationColumn(origcolname="D", name="D", reduction="min")
        ev = self.createAndEvaluateColumn(col)
        self.checkEntrySize(ev, 8)

    def testBadReductionIndex(self):
        """
        Test if a suitable error occurs when a non existing column name is used as reduction index
        """
        col = IPETEvaluationColumn(origcolname="D", name="D", reduction="min", reductionindex="E F")

        self.assertRaises(IpetNodeAttributeError, self.createAndEvaluateColumn, col)


    def testReductionResult(self):
        """
        Test the result of a couple of reductions. This also ensures that the shmean shiftby format is recognized.
        """
        reduction2result = {
            "min" : 1.0,
            "max" : 8.0,
            "mean" : 4.5,
            "median" : 4.5,
            "sum" : 36,
            "prod" : 40320,
            "shmean shift. by 1" : 3.9541639,
            "shmean shift. by 10" : 4.3160184,
            "shmean shift. by 100" : 4.4748727,
            "shmean shift. by 1000" : 4.49738675
        }

        for reduction, result in reduction2result.items():
            self.col.set_reduction(reduction)
            self.col.set_reductionindex(0)
            ev = self.createAndEvaluateColumn(self.col)
            self.assertAlmostEqual(ev.getInstanceData()["D"].unique()[0], result, delta=1e-6)






if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testReductionIndex']
    unittest.main()