# -*- coding: utf-8 -*-
"""
The MIT License (MIT)

Copyright (c) 2016 Zuse Institute Berlin, www.zib.de

Permissions are granted as stated in the license file you have obtained
with this software. If you find the library useful for your purpose,
please refer to README.md for how to cite IPET.

@author: Gregor Hendel
"""
from .StatisticReader import StatisticReader
import re

class VariableReader(StatisticReader):
    """
    Reader class to parse SCIP variable and constraint counts for original and transformed problem
    """
    name = 'VariableReader'
    varexp = re.compile(r'^  Variables        :')
    consexp= re.compile(r'^  Constraints      :')
    varkeys = ['Vars', 'BinVars', 'IntVars', 'ImplVars', 'ContVars']
    conskeys = ["InitialNCons", "MaxNCons"]
    problemtype = None
    
    def extractStatistic(self, line):
        
        # parse the problem type (original or presolved)
        if line.startswith('Presolved Problem  :'):
            self.problemtype = "PresolvedProblem"
        elif line.startswith('Original Problem   :'):
            self.problemtype = "OriginalProblem"
     
        # check if the SCIP variable expression is matched by line
        elif self.problemtype and self.varexp.match(line):
            nvariables = list(map(int, self.numericExpression.findall(line)[:len(self.varkeys)]))
            datakeys = ["%s_%s"%(self.problemtype,key) for key in self.varkeys]
            self.addData(datakeys, nvariables)

        # check if the constraint expression is matched by line
        elif self.problemtype and self.consexp.match(line):
            nconns = list(map(int, self.numericExpression.findall(line)[:len(self.conskeys)]))

            datakeys = ["%s_%s"%(self.problemtype,key) for key in self.conskeys]
            self.addData(datakeys, nconns)
            
            #reset the problem type
            self.problemtype = None
            
        return None
