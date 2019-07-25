'''
Created on 25.07.2019

@author: Gregor Hendel
'''
import unittest
from ipet import Experiment, Key
import pandas as pd
from ipet.evaluation import IPETEvaluation, IPETEvaluationColumn, IPETFilterGroup, IPETFilter
from ipet.evaluation.IPETFilter import IPETValue

class HelpExperiment(Experiment):
    """A simple data frame that meets the requirements of the Fill In test
    """

    def __init__(self):
        self.data = pd.DataFrame(
        [
         ["A1", "B1","C1", 1.0],
        #  ["A1", "B2","C1", 2.0], # This is a missing data element
         ["A2", "B1","C1", 3.0],
         ["A2", "B2","C1", 4.0],
         ["A1", "B1","C2", 9.0],
         ["A1", "B2","C2", 8.0],
         ["A2", "B1","C2", 7.0],
         ["A2", "B2","C2", 6.0],
        ],
        columns = list("ABCD")
        )
        self.data[Key.ProblemStatus] = Key.ProblemStatusCodes.Ok

    def getJoinedData(self):
        return self.data


class FillInTest(unittest.TestCase):
    """Test the correct fill in behavior

    Test if an evaluation fills in missing data correctly.
    """


    def setUp(self):
        """
        create an evaluation around a helper experiment
        """
        self.ex = HelpExperiment()
        ev = IPETEvaluation(defaultgroup="C1",
                            index="A B C",
                            fillin=True,
                            indexsplit=3
                            )

        ev.addColumn(IPETEvaluationColumn(origcolname="D", alternative="100", maxval=15))
        fg = IPETFilterGroup("Test")
        fi = IPETFilter(operator="keep", datakey="A")
        fi.addChild(IPETValue("A1"))
        fg.addFilter(fi)
        ev.addFilterGroup(fg)
        self.ev = ev
        self.fg = fg

    def tearDown(self):
        pass


    def testComputationMissingEntries(self):
        """Add the column to the user columns
        """
        self.ev.evaluate(self.ex)
        fgdata = self.ev.getAggregatedGroupData(self.fg)
        self.assertTrue(fgdata['_miss_'].sum() == 1,
        "There should be exactly 1 missing entry for the test group %s\n%s"%(self.fg.getName(), fgdata))
        rettab = self.ev.getInstanceData()
        self.assertEqual(rettab['D'][('A1', 'B2', 'C1')], 15.0, "Value of the missing element should be 15.0")





if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()