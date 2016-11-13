'''
Created on 02.08.2014

@author: Customer
'''
import unittest
from ipet.Experiment import Experiment
import os
from ipet.TestRun import TestRun
from pandas.util.testing import assert_frame_equal
import numpy

class ExperimentTest(unittest.TestCase):
    datasamples = [("meanvarx", 'Datetime_Start', "2014-08-01 16:57:10"),
                   ("lseu", 'Settings', 'testmode'),
                   ("misc03", "Datetime_End", "2014-08-01 16:56:37"),
                   ("findRoot", "Nodes", 8),
                   ("linking", "LineNumbers_BeginLogFile", 4),
                   ("j301_2", "LineNumbers_BeginLogFile", 273),
                   ("j301_2", "LineNumbers_EndLogFile", 569)
                   ]


    def setUp(self):
        self.experiment = Experiment()

    def test_datacollection(self):
        self.experiment.addOutputFile("check.short.scip-3.1.0.1.linux.x86_64.gnu.dbg.spx.opt85.testmode.out")
        self.experiment.addSoluFile("short.solu")
        self.experiment.collectData()
        # print self.experiment.testrunmanager.getManageables()[0].data[['Datetime_Start', 'Settings', 'Datetime_End']]

        df = self.experiment.testrunmanager.getManageables()[0].data
        for index, column, value in self.datasamples:
            entry = df.loc[index, column]
            self.assertEqual(entry, value, "Wrong value parsed for instance %s in column %s: should be %s, have %s" % (index, column, repr(value), repr(entry)))
    def test_saveAndLoad(self):
        self.experiment.addOutputFile("check.short.scip-3.1.0.1.linux.x86_64.gnu.dbg.spx.opt85.testmode.out")
        self.experiment.addSoluFile("short.solu")
        self.experiment.collectData()
        self.experiment.saveToFile(".testcomp.cmp")
        secondcomp = Experiment.loadFromFile(".testcomp.cmp")

        tr = self.experiment.testrunmanager.getManageables()[0]
        tr.saveToFile(".testrun.trn")
        tr2 = TestRun.loadFromFile(".testrun.trn")

        self.assertTrue(numpy.all(tr.data.columns.order() == tr2.data.columns.order()), "Columns are not equal")
        columns = ['SolvingTime', 'Nodes', 'Datetime_Start', 'GitHash']
        self.assertIsNone(assert_frame_equal(tr.data[columns], tr2.data[columns]), "Testruns do not have exactly same column data:")

        #os.remove(".testcomp.cmp")

    def test_problemNameRecognition(self):
        from ipet.parsing import ReaderManager
        rm = ReaderManager()

        problemnames2line = {}
        with open("problemnames.txt", "r") as problemNames:
            for line in problemNames:
                parsedName = rm.getProblemName(line)
                self.assertIsNotNone(parsedName, "'%s' problem name line was parsed to None" % line)
                self.assertFalse((parsedName in problemnames2line), "Error in line '%s'\n: '%s' already contained in line '%s'" % (line, parsedName, \
                                 problemnames2line.get(parsedName))
                                  )
                problemnames2line[parsedName] = line[:]


    def test_trnfileextension(self):
        self.experiment.addOutputFile(".testrun.trn")
        self.experiment.collectData()

    def test_ListReader(self):
        from ipet.parsing import ListReader
        lr = ListReader("([ab]c) +([^ ]*)", "testlr")
        lines = ("ac 1", "bc 2", "ab 3")
        correctanswers = (("ac", 1), ("bc", 2), None)
        for idx, line in enumerate(lines):
            lrlinedata = lr.getLineData(line)
            self.assertEqual(lrlinedata, correctanswers[idx], "Wrongly parsed line '%s'" % line)

    def test_parsingOfSettingsFile(self):
        inputfile = "check.bugs.scip-221aa62.linux.x86_64.gnu.opt.spx.opt97.default.set"
        self.experiment.addOutputFile(inputfile)
        self.experiment.collectData()
        
        tr = self.experiment.testrunmanager.getManageables()[0]
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
