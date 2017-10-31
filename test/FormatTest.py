'''
Created on 04.08.2017

@author: gregor
'''
import unittest
import pandas as pd
from ipet.evaluation.IPETEvalTable import IPETEvaluation, IPETEvaluationColumn
from ipet.evaluation.IPETFilter import IPETFilterGroup
import sys
from _io import StringIO

val = 0.00005
status = "ok"
class HelperExperiment():
    d = pd.DataFrame([[val, "A", "B", True, status]],
            columns=["numeric", "stringA","stringB", "bool", "Status"])

    def getJoinedData(self):
        return self.d


class FormatTest(unittest.TestCase):
    """
    Test if different format specifiers are correctly
    printed even if the desired data has
    non-numerical columns
    """
    
    fstrings = ["%.1f",
                "%.3f",
                "%.5f",
                "%.9f",
                "%16.5f",
                "%21.5f",
                "%28.5f",
                "%12.5f",
                "%9.5g",
                "%12.1g",
                "%9g",
                ]
        
    def setUp(self):
        """Redirect stdout"""
        self.out = StringIO()
        sys.stdout = self.out
        
        self.ev = IPETEvaluation(index="stringA stringB", indexsplit=1)
        self.numericcolumn = IPETEvaluationColumn(origcolname="numeric")
        self.ev.addColumn(self.numericcolumn)
        self.ev.addColumn(IPETEvaluationColumn(origcolname="Status", active="True", formatstr="%20s"))
        self.ev.addFilterGroup(IPETFilterGroup(name="FilterGroup"))
        
    def tearDown(self):
        """Close the String IO object"""
        self.out.close()
        sys.stdout = sys.__stdout__


    def testFormat(self):
        """Test all fstrings
        """
        for f in self.fstrings:
            self.numericcolumn.editAttribute("formatstr", f)
            ret, _ = self.ev.evaluate(HelperExperiment())
            self.ev.streamDataFrame(ret, "Test", "stdout")
        
            # scan output and check if the formatted value is in there
            container = self.out.getvalue()
            mem = " {} ".format(f % val)
            msg = "Expected formatted number '{}' in output \n{}\n".format(mem, container)
            self.assertIn(mem, container, msg)
        
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()