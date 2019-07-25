'''
Created on 03.09.2017

@author: Gregor Hendel
'''
import unittest
from ipet.evaluation import IPETEvaluation, IPETEvaluationColumn, IPETFilter, IPETFilterGroup
import pandas as pd
from ipet import Experiment, Key

class HelperExperiment(Experiment):
    """Special Experiment as minimal working example
    """

    def __init__(self):
        self.data = pd.DataFrame(
            [
                ["1", 1.0, -1.0]
                ],
            columns = ["Index", "Data", "FilterData"]
            )
        self.data[Key.ProblemStatus] = Key.ProblemStatusCodes.Ok
    def getJoinedData(self):
        return self.data

class FilterDataTest(unittest.TestCase):


    def setUp(self):
        """Set up the evaluation

            The evaluation has only one column
            for the 'Data' key, but applies
            filtering on the 'FilterData' key
        """
        self.ex = HelperExperiment()
        ev = IPETEvaluation(index="Index", indexsplit="1")
        ev.addColumn(IPETEvaluationColumn(origcolname="Data"))
        fg = IPETFilterGroup("TestGroup")
        fi = IPETFilter(expression1="FilterData", expression2=-1.0, operator="eq")
        fg.addFilter(fi)
        ev.addFilterGroup(fg)

        self.ev = ev

    def tearDown(self):
        pass


    def testFilterData(self):
        """
        Test if the 'FilterData' column is correctly
        used although it is not specified by the evaluation
        """
        _, aggtable = self.ev.evaluate(self.ex)

        #
        # Test through the aggregated table that should contain
        # the TestGroup and therefore have exactly one row
        #
        expected_shape = (1, 10)
        self.assertEqual(aggtable.shape, expected_shape,
                         "Expected shape {} in table, got {},n{}\n".format(expected_shape, aggtable.shape, aggtable) )



if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testFilterData']
    unittest.main()