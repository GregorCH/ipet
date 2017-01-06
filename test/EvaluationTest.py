'''
The MIT License (MIT)

Copyright (c) 2016 Zuse Institute Berlin, www.zib.de

Permissions are granted as stated in the license file you have obtained
with this software. If you find the library useful for your purpose,
please refer to README.md for how to cite IPET.

@author: Gregor Hendel
'''

import unittest
from ipet.evaluation import IPETEvaluation
from xml.dom.minidom import parseString
import xml.etree.ElementTree as ElementTree
import os
from ipet.misc import saveAsXML
from ipet.evaluation import IPETFilter, IPETFilterGroup, IPETInstance
from ipet.evaluation import Aggregation
from ipet.evaluation import IPETEvaluationColumn

DATADIR = os.path.join(os.path.dirname(__file__), "data")
TMPDIR = os.path.join(os.path.dirname(__file__), ".tmp")
EVALTEST = os.path.join(DATADIR, 'testevaluate.xml')
import shutil
class EvaluationTest(unittest.TestCase):


    def setUp(self):
        os.mkdir(TMPDIR)

    def tearDown(self):
        shutil.rmtree(TMPDIR)

    def test_constructor(self):
        '''
        test if the constructor is working without arguments
        '''
        evaluation = IPETEvaluation()

    def test_testEvaluateXML(self):
        ev = IPETEvaluation.fromXMLFile(EVALTEST)

    def test_xmlWrite(self):
        classes = [(IPETFilter, "filter"),
                   (Aggregation, "agg"),
                   (IPETFilterGroup, "group"),
                   (IPETInstance, "instance"),
                   (IPETEvaluationColumn, "column")]

        for cl, basename in classes:
            node = cl()
            try:
                saveAsXML(node, os.path.join(TMPDIR, basename + ".xml"))
            except TypeError as e:
                print(node.toXMLElem())
                print(node.attributesToStringDict())
                raise e

        ev = IPETEvaluation.fromXMLFile(EVALTEST)
        try:
            saveAsXML(ev, os.path.join(TMPDIR, "test.xml"))
        except TypeError as e:
            print(ev.attributesToStringDict())
            raise e


    def test_xml(self):
        '''
        test construction of modified evaluations, and if they persist after constructing a twin directly from the XML representation
        '''

        modificationlist = [{},
                            {"sortlevel":1},
                            {"groupkey":"foo"},
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
