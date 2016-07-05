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
        self.comparator.addOutputFile("check.short.scip-3.1.0.1.linux.x86_64.gnu.dbg.spx.opt85.testmode.out")
        self.comparator.addSoluFile("short.solu")
        self.comparator.collectData()
        print self.comparator.testrunmanager.getManageables()[0].data[['Datetime_Start', 'Settings', 'Datetime_End']]

        df = self.comparator.testrunmanager.getManageables()[0].data
        for index, column, value in self.datasamples:
            entry = df.loc[index, column]
            self.assertEqual(entry, value, "Wrong value parsed for instance %s in column %s: should be %s, have %s" % (index, column, repr(value), repr(entry)))
    def test_saveAndLoad(self):
        self.comparator.addOutputFile("check.short.scip-3.1.0.1.linux.x86_64.gnu.dbg.spx.opt85.testmode.out")
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

        #os.remove(".testcomp.cmp")

    def test_trnfileextension(self):
        self.comparator.addOutputFile(".testrun.trn")
        self.comparator.collectData()

    def test_parsingOfSettingsFile(self):
        inputfile = "check.bugs.scip-221aa62.linux.x86_64.gnu.opt.spx.opt97.default.set"
        self.comparator.addOutputFile(inputfile)
        self.comparator.collectData()
        
        tr = self.comparator.testrunmanager.getManageables()[0]
        values, defaultvalues = tr.getParameterData()
        
        import json
        import re
        import sys

        def collect_settings(path):
            '''
            A crappy settings file parser
            '''
            with open(path, "r") as f:
                settings_contents = f.readlines()

            settings = {}
            for line in settings_contents:
                exclude = r"^\s*#"
                comment_match = re.match(exclude, line)
                if not comment_match and line != "\n":
                    parts = line.split(" = ")
                    settings[parts[0].strip()] = estimate_type(parts[1].strip())

            return settings


        def boolify(value):
            if value.lower() == "true":
                return True
            elif value.lower() == "false":
                return False
            raise ValueError("{} is not a bool".format(value))


        def estimate_type(var):
            '''
            Guesses the str representation of the variables type
            '''
            var = str(var)

            for caster in (boolify, int, float):
                try:
                    return caster(var)
                except ValueError:
                    pass
            return var

        crappysettings = collect_settings(inputfile)

        valuesamples = {"constraints/quadratic/scaling" : True,
                        "conflict/bounddisjunction/continuousfrac" : 0.4,
                        "constraints/soc/sparsifymaxloss" : 0.2,
                        "separating/cgmip/nodelimit" : 10000,
                        "presolving/abortfac" : 0.0001,
                        "vbc/filename": "\"-\""}

        for key, val in valuesamples.iteritems():
            self.assertEqual(val, values[key], "wrong parameter value %s parsed for parameter <%s>, should be %s" % (repr(values[key]), key, repr(val)))
            self.assertEqual(val, defaultvalues[key], "wrong default value %s parsed for parameter <%s>, should be %s" % (repr(defaultvalues[key]), key, repr(val)))

        for key, val in crappysettings.iteritems():
            self.assertEqual(val, values[key], "wrong parameter value %s parsed for parameter <%s>, should be %s" % (repr(values[key]), key, repr(val)))

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
