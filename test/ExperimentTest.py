'''
The MIT License (MIT)

Copyright (c) 2016 Zuse Institute Berlin, www.zib.de

Permissions are granted as stated in the license file you have obtained
with this software. If you find the library useful for your purpose,
please refer to README.md for how to cite IPET.

@author: Gregor Hendel
'''
import unittest
import os
import json
import re
import numpy
from pandas.util.testing import assert_frame_equal

from ipet.Experiment import Experiment
from ipet.TestRun import TestRun
from ipet.parsing import ListReader
from ipet.parsing import ReaderManager


DATADIR = os.path.join(os.path.dirname(__file__), "data")


class ExperimentTest(unittest.TestCase):
    datasamples = [
        ("meanvarx", 'Datetime_Start', "2014-08-01 16:57:10"),
        ("lseu", 'Settings', 'testmode'),
        ("misc03", "Datetime_End", "2014-08-01 16:56:37"),
        ("findRoot", "Nodes", 8),
        ("linking", "LineNumbers_BeginLogFile", 4),
        ("j301_2", "LineNumbers_BeginLogFile", 276),
        ("j301_2", "LineNumbers_EndLogFile", 575),
    ]

    def setUp(self):
        self.experiment = Experiment()

    def test_datacollection(self):
        fname = "check.short.scip-3.1.0.1.linux.x86_64.gnu.dbg.spx.opt85.testmode.out"
        out_file = os.path.join(DATADIR, fname)
        solu_file = os.path.join(DATADIR, "short.solu")
        self.experiment.addOutputFile(out_file)
        self.experiment.addSoluFile(solu_file)
        self.experiment.collectData()

        df = self.experiment.testrunmanager.getManageables()[0].data
        for index, column, value in self.datasamples:
            entry = df.loc[index, column]
            msg = "Wrong value parsed for instance %s in column %s: should be %s, have %s" % \
                  (index, column, repr(value), repr(entry))
            self.assertEqual(entry, value, msg)

    def test_instance_name_parsing(self):
        fname = "check.IP_0s_1s.scip-3.2.1.2.linux.x86_64.gnu.dbg.cpx.opt-low.default.out"
        out_file = os.path.join(DATADIR, fname)
        solu_file = os.path.join(DATADIR, "IP_0s_1s.solu")
        self.experiment.addOutputFile(out_file)
        self.experiment.addSoluFile(solu_file)
        self.experiment.collectData()

        data = json.loads(self.experiment.testrunmanager.getManageables()[0].data.to_json())
        # ensure that the correct number of instances are properly parsed
        self.assertEqual(len(data["Nodes"].keys()), 408)

    def test_saveAndLoad(self):
        fname = "check.short.scip-3.1.0.1.linux.x86_64.gnu.dbg.spx.opt85.testmode.out"
        out_file = os.path.join(DATADIR, fname)
        solu_file = os.path.join(DATADIR, "short.solu")
        self.experiment.addOutputFile(out_file)
        self.experiment.addSoluFile(solu_file)
        self.experiment.collectData()
        save_file = os.path.join(DATADIR, ".testcomp.cmp")
        self.experiment.saveToFile(save_file)
        Experiment.loadFromFile(save_file)

        tr = self.experiment.testrunmanager.getManageables()[0]
        trn_file = os.path.join(DATADIR, ".testrun.trn")
        tr.saveToFile(trn_file)
        tr2 = TestRun.loadFromFile(trn_file)
        msg = "Columns are not equal"
        self.assertTrue(numpy.all(tr.data.columns.sort_values() == tr2.data.columns.sort_values()),
                        msg)
        columns = ['SolvingTime', 'Nodes', 'Datetime_Start', 'GitHash']
        msg = "Testruns do not have exactly same column data:"
        self.assertIsNone(assert_frame_equal(tr.data[columns], tr2.data[columns]), msg)

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
        manageables = self.experiment.testrunmanager.getManageables()[0]
        data = json.loads(manageables.data.to_json())

        for k, v in data["LineNumbers_BeginLogFile"].items():
            self.assertTrue(isinstance(v, int))

        for k, v in data["LineNumbers_EndLogFile"].items():
            self.assertTrue(isinstance(v, int))

    def test_trnfileextension(self):
        trn_file = os.path.join(DATADIR, ".testrun.trn")
        self.experiment.addOutputFile(trn_file)
        self.experiment.collectData()

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

        tr = self.experiment.testrunmanager.getManageables()[0]
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


if __name__ == "__main__":
    unittest.main()
