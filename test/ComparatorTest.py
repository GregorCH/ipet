'''
Created on 02.08.2014

@author: Customer
'''
import unittest
from ipet.Comparator import Comparator
import os
from ipet.TestRun import TestRun
from pandas.util.testing import assert_frame_equal
import numpy

class ComparatorTest(unittest.TestCase):
    datasamples = [("meanvarx", 'Datetime_Start', "2014-08-01 16:57:10"),
                   ("lseu", 'Settings', 'testmode'),
                   ("misc03", "Datetime_End", "2014-08-01 16:56:37")
                   ]

    def setUp(self):
        self.comparator = Comparator()

    def test_datacollection(self):
        self.comparator.addLogFile("check.short.scip-3.1.0.1.linux.x86_64.gnu.dbg.spx.opt85.testmode.out")
        self.comparator.addSoluFile("short.solu")
        self.comparator.collectData()
        print self.comparator.testrunmanager.getManageables()[0].data[['Datetime_Start', 'Settings', 'Datetime_End']]

        df = self.comparator.testrunmanager.getManageables()[0].data
        for index, column, value in self.datasamples:
            entry = df.loc[index, column]
            self.assertEqual(entry, value, "Wrong value parsed for instance %s in column %s: should be %s, have %s" % (index, column, repr(value), repr(entry)))
    def test_saveAndLoad(self):
        self.comparator.addLogFile("check.short.scip-3.1.0.1.linux.x86_64.gnu.dbg.spx.opt85.testmode.out")
        self.comparator.addSoluFile("short.solu")
        self.comparator.collectData()
        self.comparator.saveToFile(".testcomp.cmp")
        secondcomp = Comparator.loadFromFile(".testcomp.cmp")

        tr = self.comparator.testrunmanager.getManageables()[0]
        tr.saveToFile(".testrun.trn")
        tr2 = TestRun.loadFromFile(".testrun.trn")

        self.assertTrue(numpy.all(tr.data.columns.order() == tr2.data.columns.order()), "Columns are not equal")
        columns = ['SolvingTime', 'Nodes', 'Datetime_Start', 'GitHash']
        self.assertIsNone(assert_frame_equal(tr.data[columns], tr2.data[columns]), "Testruns do not have exactly same column data:")

        os.remove(".testcomp.cmp")

    def test_trnfileextension(self):
        self.comparator.addLogFile(".testrun.trn")
        self.comparator.collectData()

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
