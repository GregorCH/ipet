"""
The MIT License (MIT)

Copyright (c) 2016 Zuse Institute Berlin, www.zib.de

Permissions are granted as stated in the license file you have obtained
with this software. If you find the library useful for your purpose,
please refer to README.md for how to cite IPET.

@author: Gregor Hendel
"""
import unittest
import os
import json
import re
import shutil
import sys
import numpy as np
from pandas.util.testing import assert_frame_equal
from ipet.Experiment import Experiment
from ipet.TestRun import TestRun
from ipet.parsing import ListReader
from ipet.parsing import ReaderManager
from ipet import Key

DATADIR = os.path.join(os.path.dirname(__file__), "data")
TMPDIR = os.path.join(os.path.dirname(__file__), ".tmp")


class ExperimentTest(unittest.TestCase):
#     datasamples = [
#         ("meanvarx", 'Datetime_Start', convertTimeStamp(1406905030)),
#         ("lseu", 'Settings', 'testmode'),
#         ("misc03", "Datetime_End", convertTimeStamp(1406904997)),
#         ("findRoot", "Nodes", 8),
#         ("linking", "LineNumbers_BeginLogFile", 4),
#         ("j301_2", "LineNumbers_BeginLogFile", 276),
#         ("j301_2", "LineNumbers_EndLogFile", 575),
#     ]
    datasamples = [
        #(26, 'Datetime_Start', convertTimeStamp(1406905030)),
        #(12, 'Settings', 'testmode'),
        #(14, "Datetime_End", convertTimeStamp(1406904997)),
        (39, "Nodes", 8),
        (0, "LineNumbers_BeginLogFile", 4),
        (1, "LineNumbers_BeginLogFile", 276),
        (1, "LineNumbers_EndLogFile", 575),
    ]
    
    checkColumns=['SolvingTime', 'Nodes', 'Datetime_Start', 'GitHash']

    def setUp(self):
        try:
            os.mkdir(TMPDIR)
        except FileExistsError:
            pass
        self.experiment = Experiment()

    def tearDown(self):
        shutil.rmtree(TMPDIR)
        
    def test_datacollection(self):
        fname = "check.short.scip-3.1.0.1.linux.x86_64.gnu.dbg.spx.opt85.testmode.out"
        out_file = os.path.join(DATADIR, fname)
        solu_file = os.path.join(DATADIR, "short.solu")
        self.experiment.addOutputFile(out_file)
        self.experiment.addSoluFile(solu_file)
        self.experiment.collectData()

        df = self.experiment.getTestRuns()[0].getData()
        for index, column, value in self.datasamples:
            entry = df.loc[index, column]
            msg = "Wrong value parsed for problem %s in column %s: should be %s, have %s" % \
                  (index, column, repr(value), repr(entry))
            self.assertEqual(entry, value, msg)

    # FARI How to fake input from stdin?
    def test_datacollection_from_stdin(self):
        fname = "bell3a.out"
        out_file = os.path.join(DATADIR, fname)
        with open(out_file, "r") as f:
            sys.stdin = f
             
            self.experiment.addStdinput()
            self.experiment.collectData()
            sys.stdin = sys.__stdin__

        experimentFromFile = Experiment()
        experimentFromFile.addOutputFile(out_file)
        experimentFromFile.collectData()
        
        trstdin = self.experiment.getTestRuns()[0]
        trfile = experimentFromFile.getTestRuns()[0]
        
        columns = ["PrimalBound", "DualBound", "SolvingTime"]

        self.checkTestrunsEqual(trstdin, trfile, columns)

    def test_problem_name_parsing(self):
        fname = "check.IP_0s_1s.scip-3.2.1.2.linux.x86_64.gnu.dbg.cpx.opt-low.default.out"
        out_file = os.path.join(DATADIR, fname)
        solu_file = os.path.join(DATADIR, "IP_0s_1s.solu")
        self.experiment.addOutputFile(out_file)
        self.experiment.addSoluFile(solu_file)
        self.experiment.collectData()
        data = self.experiment.getTestRuns()[0].getData()
        # ensure that the correct number of problems are properly parsed
        self.assertEqual(len(data), 411)

    def checkTestrunsEqual(self, tr, tr2, columns=checkColumns):
        msg = "Testruns do not have exactly same column data."
        return self.assertIsNone(assert_frame_equal(tr.getData()[columns], tr2.getData()[columns]), msg)

    def test_saveAndLoad(self):
        fname = "check.short.scip-3.1.0.1.linux.x86_64.gnu.dbg.spx.opt85.testmode.out"
        out_file = os.path.join(DATADIR, fname)
        solu_file = os.path.join(DATADIR, "short.solu")
        self.experiment.addOutputFile(out_file)
        self.experiment.addSoluFile(solu_file)
        self.experiment.collectData()
        save_file = os.path.join(TMPDIR, ".testcomp.cmp")
        self.experiment.saveToFile(save_file)
        Experiment.loadFromFile(save_file)

        tr = self.experiment.getTestRuns()[0]
        trn_file = os.path.join(DATADIR, ".testrun.trn")
        tr.saveToFile(trn_file)
        tr2 = TestRun.loadFromFile(trn_file)
        self.checkTestrunsEqual(tr, tr2)

    def test_problemNameRecognition(self):
        rm = ReaderManager()
        problemnames2line = {}
        fname = os.path.join(DATADIR, "problemnames.txt")
        with open(fname, "r") as problemNames:
            for line in problemNames:
                parsedName = rm.getProblemName(line)
                self.assertIsNotNone(parsedName, "'%s' problem name line was parsed to None" % line)
                msg = "Error in line '%s'\n: '%s' already contained in line '%s'" % \
                      (line, parsedName, problemnames2line.get(parsedName))
                self.assertTrue((parsedName not in problemnames2line), msg)
                problemnames2line[parsedName] = line[:]

    def test_line_numbers(self):
        fname = "check.MMM.scip-hashing.linux.x86_64.gnu.dbg.cpx.mip-dbg.heuraggr.out"
        out_file = os.path.join(DATADIR, fname)
        solu_file = os.path.join(DATADIR, "MMM.solu")
        self.experiment.addOutputFile(out_file)
        self.experiment.addSoluFile(solu_file)
        self.experiment.collectData()
        data = self.experiment.getTestRuns()[0].data
        
        for v in data["LineNumbers_BeginLogFile"]:
            self.assertTrue(isinstance(v, np.int64))

        for v in data["LineNumbers_EndLogFile"]:
            self.assertTrue(isinstance(v, np.int64))

    def test_trnfileextension(self):
        trn_file = os.path.join(DATADIR, ".testrun.trn")
        self.experiment.addOutputFile(trn_file)
        self.experiment.collectData()

    def test_fileExtensions(self):
        """
        Test if an experiment accepts
        """
        # all possible extensions  should be accepted
        for extension in ReaderManager().getFileExtensions():
            self.experiment.addOutputFile("bla" + extension)

        # if called with an unknown extension, this should raise a ValueError
        for otherextension in [".res", ".txt"]:
            with self.assertRaises(ValueError):
                self.experiment.addOutputFile("bla" + otherextension)

    def test_ListReader(self):
        lr = ListReader("([ab]c) +([^ ]*)", "testlr")
        lines = ("ac 1", "bc 2", "ab 3")
        correctanswers = (("ac", 1), ("bc", 2), None)
        for idx, line in enumerate(lines):
            lrlinedata = lr.getLineData(line)
            self.assertEqual(lrlinedata, correctanswers[idx], "Wrongly parsed line '%s'" % line)

    def test_parsingOfSettingsFile(self):
        fname = "check.bugs.scip-221aa62.linux.x86_64.gnu.opt.spx.opt97.default.set"
        set_file = os.path.join(DATADIR, fname)
        self.experiment.addOutputFile(set_file)
        self.experiment.collectData()

        tr = self.experiment.getTestRuns()[0]
        values, defaultvalues = tr.getParameterData()

        crappysettings = collect_settings(set_file)

        valuesamples = {
            "constraints/quadratic/scaling": True,
            "conflict/bounddisjunction/continuousfrac": 0.4,
            "constraints/soc/sparsifymaxloss": 0.2,
            "separating/cgmip/nodelimit": 10000,
            "presolving/abortfac": 0.0001,
            "vbc/filename": "\"-\"",
        }
        for key, val in valuesamples.items():
            msg = "wrong parameter value %s parsed for parameter <%s>, should be %s" % \
                  (repr(values[key]), key, repr(val))
            self.assertEqual(val, values[key], msg)
            msg = "wrong default value %s parsed for parameter <%s>, should be %s" % \
                  (repr(defaultvalues[key]), key, repr(val))
            self.assertEqual(val, defaultvalues[key], msg)

        for key, val in crappysettings.items():
            msg = "wrong parameter value %s parsed for parameter <%s>, should be %s" % \
                  (repr(values[key]), key, repr(val))
            self.assertEqual(val, values[key], msg)

    def testStatusComparisons(self):
        goodStatusList = [Key.ProblemStatusCodes.Ok, Key.ProblemStatusCodes.Better, Key.ProblemStatusCodes.SolvedNotVerified]
        badStatusList = [Key.ProblemStatusCodes.FailAbort, Key.ProblemStatusCodes.FailObjectiveValue, Key.ProblemStatusCodes.Fail]
        
        msg = "Returned status {0} is not the expected {1}"
        for status, expected in [(Key.ProblemStatusCodes.getBestStatus(goodStatusList + badStatusList), Key.ProblemStatusCodes.Ok),
                     (Key.ProblemStatusCodes.getBestStatus(*(goodStatusList + badStatusList)), Key.ProblemStatusCodes.Ok),
                     (Key.ProblemStatusCodes.getWorstStatus(goodStatusList + badStatusList), Key.ProblemStatusCodes.FailAbort),
                     (Key.ProblemStatusCodes.getBestStatus(badStatusList + ["dummy"]), "dummy"),
                     (Key.ProblemStatusCodes.getWorstStatus(goodStatusList + ["timelimit"]), "timelimit")]:
            self.assertEqual(status, expected, msg.format(status, expected)) 
            
def collect_settings(path):
    """
    A crappy settings file parser
    """
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
    """
    Guesses the str representation of the variables type
    """
    var = str(var)

    for caster in (boolify, int, float):
        try:
            return caster(var)
        except ValueError:
            pass
    return var

if __name__ == "__main__":
    unittest.main()
    
    