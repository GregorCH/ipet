'''
Created on 04.08.2017

@author: gregor
'''
import unittest
import pandas as pd
from ipet.evaluation.IPETEvalTable import IPETEvaluation, IPETEvaluationColumn,\
    StrTuple
import numpy
class HelperExperiment:
    """An experiment with data
    """
    d=pd.DataFrame([
                    ["A1", "B1", 1, "ok"],
                    ["A2", "B1", 2, "ok"],
                    ["A1", "B2", 3, "ok"],
                    ["A2", "B2", 4, "ok"],
                    ], columns=["A", "B", "C", "Status"])
    
    def getJoinedData(self):
        return self.d
    


class DefaultGroupTest(unittest.TestCase):
    """
    Default groups should be computed if and only if
    a wrong user input specifies a non-existing
    group
    """
    def setUp(self):
        self.ev = IPETEvaluation(index="B A", defaultgroup="A1")
        self.ev.addColumn(IPETEvaluationColumn(origcolname="C", comp="quot"))
        self.data = HelperExperiment().getJoinedData()
        pass


    def tearDown(self):
        pass
    
    def testDefaultGroupContained(self):
        """Test if both groups A1 and A2 are correctly recognized as contained
        """
        for g in ["A1", "A2"]:
            self.ev.editAttribute("defaultgroup", g)
            self.assertTrue(self.ev.defaultgroupIsContained(self.ev.getDefaultgroup(self.data), self.data), 
                            "{} is contained in column {} of data:\n{}\n".format(g, self.ev.getColIndex(), self.data))
            
    def testDefaultGroupNotContained(self):
        """Test if the default group recognition copes with wrong user input
        """
        for g in ["A", "1", "B1", "B2", "None", "B1:A1"]:
            self.assertFalse(self.ev.defaultgroupIsContained(g, self.data), 
                            "{} is not contained in column {} of data:\n{}\n".format(g, self.ev.getColIndex(), self.data))
            self.ev.editAttribute("defaultgroup", g)
            self.assertTrue(self.ev.defaultgroupIsContained(self.ev.getDefaultgroup(self.data), self.data), 
                            "{} is contained in column {} of data:\n{}\n".format(g, self.ev.getColIndex(), self.data))
            
    def testTwoLevelDefaultGroup(self):
        self.ev.set_index("A B Status")
        self.ev.set_indexsplit(-2)
        
        for g in ["B1:ok", "B2:ok"]:
            self.ev.editAttribute("defaultgroup", g)
            self.assertTrue(self.ev.defaultgroupIsContained(self.ev.getDefaultgroup(self.data), self.data), 
                            "{} is contained in column {} of data:\n{}\n".format(g, self.ev.getColIndex(), self.data))
            
        for g in ["B1", "B2", "A1:ok", "A2:ok"]:
            self.ev.editAttribute("defaultgroup", g)
            self.assertFalse(self.ev.defaultgroupIsContained(StrTuple(g).getTuple(), self.data), 
                            "{} is not contained in column {} of data:\n{}\n".format(StrTuple(g).getTuple(), self.ev.getColIndex(), self.data))
        

    def testDefaultGroup(self):
        """A generated default group must always be contained in the data
        """
        #
        # create a simple evaluation using A and B as index
        #
        ev = IPETEvaluation(index="A B")
        
        #
        # the default group of the evalution must be contained in the data
        #
        self.assertTrue(ev.defaultgroupIsContained(ev.getDefaultgroup(self.data), self.data), 
                        "{} is contained in column {} of data:\n{}\n".format(ev.getDefaultgroup(self.data), ev.getColIndex(), self.data))
        
        


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testDefaultGroup']
    unittest.main()