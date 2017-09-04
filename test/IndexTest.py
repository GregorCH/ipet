'''
Created on 03.09.2017

@author: Gregor Hendel
'''
import unittest
from ipet import Experiment, Key
import pandas as pd
from ipet.evaluation import IPETEvaluation, IPETEvaluationColumn, IPETFilterGroup, IPETFilter
from ipet.evaluation.IPETFilter import IPETValue

class HelpExperiment(Experiment):
    """A simple data frame that meets the requirements of the Index test
    
    """
    
    def __init__(self):
        self.data = pd.DataFrame(
        [
         ["A1", "B1","C1", 1.0],
         ["A1", "B2","C1", 2.0],
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


class IndexTest(unittest.TestCase):
    """Test the correct treatment of index columns
    
    Index columns guide the appearance of the reduced
    table. They should not be reduced by themselves.
    It is incorrect to submit a reduction function
    to an index column 
    """


    def setUp(self):
        self.ex = HelpExperiment()
        ev = IPETEvaluation(defaultgroup="C1", 
                            index="A C"
                            )
        
        ev.addColumn(IPETEvaluationColumn(origcolname="D"))
        fg = IPETFilterGroup("Test")
        fi = IPETFilter(operator="keep", datakey="A")
        fi.addChild(IPETValue("A1"))
        fg.addFilter(fi)
        fg2 = IPETFilterGroup("Test2")
        fi2 = IPETFilter(operator="keep", datakey="A")
        fi2.addChild(IPETValue("A2"))
        fg2.addFilter(fi2)
        ev.addFilterGroup(fg2)
        ev.addFilterGroup(fg)
        self.ev = ev
        self.fg = fg

    def tearDown(self):
        pass
    
    def assertTableShape(self, expected : tuple, table : pd.DataFrame) :
        self.assertEqual(table.shape, expected, 
                         "Expecting table of shape {}, got shape {}: \n{}\n".format(expected, table.shape, table))
        

    def testSimpleEvaluation(self):
        """Test an evaluation that does not have the index as evaluation column"""
        longtable = self.ev.evaluate(self.ex)[0]
        #
        # assert that the table has the right shape
        #
        self.assertTableShape((2,2), longtable)
        self.assertTrue(longtable.index.isin(["A1", "A2"]).all(),
                         "All index entries of the table should be A1 or A2"
                         )
        igd = self.ev.getInstanceGroupData(self.fg)
        self.assertTableShape((1,2), igd)
        
        
    def testColumnAsIndex(self):
        """Add the column to the user columns
        """
        self.ev.addColumn(IPETEvaluationColumn(origcolname="A"))
      
        longtable = self.ev.evaluate(self.ex)[0]
        self.assertTableShape((2,2), longtable)
        self.assertTrue(longtable.index.isin(["A1", "A2"]).all(), 
                        "All index entries of the table should be A1 or A2")
        
        


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()