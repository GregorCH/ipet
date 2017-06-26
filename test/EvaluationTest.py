"""
The MIT License (MIT)

Copyright (c) 2016 Zuse Institute Berlin, www.zib.de

Permissions are granted as stated in the license file you have obtained
with this software. If you find the library useful for your purpose,
please refer to README.md for how to cite IPET.

@author: Gregor Hendel
"""

import unittest
from ipet.evaluation import IPETEvaluation
from xml.dom.minidom import parseString
import xml.etree.ElementTree as ElementTree
import os
import re
import pandas as pd
from ipet import Experiment
from ipet.misc import saveAsXML
from ipet.evaluation import IPETFilter, IPETFilterGroup, IPETValue
from ipet.evaluation import Aggregation
from ipet.evaluation import IPETEvaluationColumn

DATADIR = os.path.join(os.path.dirname(__file__), "data")
TMPDIR = os.path.join(os.path.dirname(__file__), ".tmp")
EVALTEST = os.path.join(DATADIR, 'testevaluate.xml')
import shutil

testevalstr_head = '<?xml version="1.0" ?>\n'
testevalstr_eval = [
                    '<Evaluation index="ProblemName Status" indexsplit="0">\n',
                    '<Evaluation index="ProblemName Status" indexsplit="2">\n',
#                    '<Evaluation index="ProblemName Indic Status" indexsplit="1">\n',
#                    '<Evaluation index="ProblemName Indic Status" indexsplit="2">\n',
#                    '<Evaluation index="ProblemName Indic Status" indexsplit="3">\n',
                    ]
testevalstr_col = ['\t<Column name="Time" origcolname="SolvingTime" alternative="100" reduction="mean">\n{}\t</Column>\n',
                   '\t<Column origcolname="ProblemName" reduction="strConcat">\n{}\t</Column>\n',
                   '\t<Column name="Indic" constant="0" alternative="1" reduction="max">\n\
\t\t<Filter expression1="SolvingTime" expression2="10" operator="ge" />\n{}\n\t</Column>\n']
testevalstr_agg = ['\t\t<Aggregation aggregation="mean" />\n',
                   '\t\t<Aggregation aggregation="strConcat" />\n',
                   '\t\t<Aggregation aggregation="strConcat" />\n']
testevalstr_fg = ['\t<FilterGroup active="True" filtertype="intersection" name="all"/>\n',
                  '\t<FilterGroup name="hard">\n\t\t<Filter anytestrun="any" expression1="Time" expression2="100" operator="ge"/>\n\t</FilterGroup>\n']
testevalstr_foot = '</Evaluation>'
test_trn = os.path.join(DATADIR, 'check.MMM.scip-hashing.linux.x86_64.gnu.dbg.cpx.mip-dbg.heuraggr.trn')

class EvaluationTest(unittest.TestCase):

    test_fgs = [None, [0], [1], [0, 1]]
    test_cols = [None,
                 [[0, True]],
                 [[0, False]],
                 [[0, True], [2, True]],
                 [[0, True], [2, False]],
#                 [[0, False], [2, True]],
                 [[0, False], [2, False]],
                 [[0, True], [1, True], [2, True]],
                 [[0, True], [1, True], [2, False]],
                 [[0, False], [1, False], [2, False]],
                 ]

    def test_evalformat(self):
        for (evalstr, cols, fg) in ((evalstr, cols, fg) for evalstr in testevalstr_eval for cols in self.test_cols for fg in self.test_fgs):
            testevalstr = testevalstr_head + evalstr
            if cols is not None:
                for (col, agg) in cols:
                    testevalstr = testevalstr + testevalstr_col[col].format((testevalstr_agg[col] if agg else ""))
            if fg is not None:
                for pos in fg:
                    testevalstr = testevalstr + testevalstr_fg[pos]
            testevalstr = testevalstr + testevalstr_foot

            ev = IPETEvaluation.fromXML(testevalstr)
            ex = Experiment()
            ex.addOutputFile(test_trn)
            try:
                tab_long, tab_agg = ev.evaluate(ex)
            except AttributeError as e:
                print(e)
                continue

            self.assertEqual(type(tab_long), pd.DataFrame, "Type of long table wrong.")
            self.assertEqual(type(tab_agg), pd.DataFrame, "Type of aggregated table wrong.")

            index = self.getAttrFromStr("index", evalstr).split()
            indexsplit = int(self.getAttrFromStr("indexsplit", evalstr))
            # do not allow rowindex to be empty
            if indexsplit == 0:
                indexsplit = 1

            rowindex_level = len(index[:indexsplit])
            columns_level = len(index[indexsplit:])

            self.assertEqual(tab_long.columns.nlevels, columns_level + 1, "Level of columnindex of long table wrong.")
            self.assertEqual(tab_agg.index.nlevels, columns_level + 1, "Level of rowindex of agg table wrong.")

            self.assertEqual(tab_long.index.nlevels, rowindex_level, "Level of rowindex of long table wrong.")

    def getAttrFromStr(self, attr, evalstr):
        start = re.search(attr, evalstr).end() + 2
        end = re.search("\"", evalstr[start:]).start()
        return evalstr[start:][:end]

    def setUp(self):
        try:
            os.mkdir(TMPDIR)
        except FileExistsError:
            pass

    def tearDown(self):
        shutil.rmtree(TMPDIR)

    def test_constructor(self):
        """
        test if the constructor is working without arguments
        """
        evaluation = IPETEvaluation()

    def test_testEvaluateXML(self):
        ev = IPETEvaluation.fromXMLFile(EVALTEST)

    def test_xmlWrite(self):
        classes = [(IPETFilter, "filter"),
                   (Aggregation, "agg"),
                   (IPETFilterGroup, "group"),
                   (IPETValue, "instance"),
                   (IPETEvaluationColumn, "column")]

        for cl, basename in classes:
            node = cl()
            try:
                saveAsXML(node, os.path.join(TMPDIR, basename + ".xml"))
            except TypeError as e:
                raise e

        ev = IPETEvaluation.fromXMLFile(EVALTEST)
        try:
            saveAsXML(ev, os.path.join(TMPDIR, "test.xml"))
        except TypeError as e:
            print(ev.attributesToStringDict())
            raise e


    def test_xml(self):
        """
        test construction of modified evaluations, and if they persist after constructing a twin directly from the XML representation
        """

        modificationlist = [{},
                            {"sortlevel":1},
                            {"index":"foo bar"},
                            {"defaultgroup":"bar"},
                            {"evaluateoptauto":False}
                            ]
        for mod in modificationlist:
            evaluation = IPETEvaluation(**mod)
            evaluation2 = IPETEvaluation.fromXML(ElementTree.tostring(evaluation.toXMLElem()))
            self.assertTrue(evaluation.equals(evaluation2),
                             "The two evaluations are not the same after modifying %s" % mod)




if __name__ == "__main__":
    unittest.main()
