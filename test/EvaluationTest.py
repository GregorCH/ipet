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

DATADIR = os.path.join(os.path.dirname(__file__), "data")

class EvaluationTest(unittest.TestCase):
    
    def test_constructor(self):
        '''
        test if the constructor is working without arguments
        '''
        evaluation = IPETEvaluation()
        
    def test_testEvaluateXML(self):
        ev = IPETEvaluation.fromXMLFile(os.path.join(DATADIR, 'testevaluate.xml'))
        
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
