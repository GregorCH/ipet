# -*- coding: utf-8 -*-
from StatisticReader import StatisticReader
import re

class VariableReader(StatisticReader):
    name = 'VariableReader'
    varexp = re.compile(r'^  Variables        :')
    consexp= re.compile(r'^  Constraints      :')
    varkeys = ['Vars', 'BinVars', 'IntVars', 'ImplVars', 'ContVars']
    conskeys = ["InitialNCons", "MaxNCons"]
    problemtype = None
    
    def extractStatistic(self, line):
        if line.startswith('Presolved Problem  :'):
            self.problemtype = "PresolvedProblem"
        elif line.startswith('Original Problem   :'):
            self.problemtype = "OriginalProblem"
     
        elif self.problemtype and self.varexp.match(line):
            nvariables = map(int, self.numericExpression.findall(line)[:len(self.varkeys)])

            datakeys = ["%s_%s"%(self.problemtype,key) for key in self.varkeys]
            self.addData(datakeys, nvariables)
        elif self.problemtype and self.consexp.match(line):
            nconns = map(int, self.numericExpression.findall(line)[:len(self.conskeys)])

            datakeys = ["%s_%s"%(self.problemtype,key) for key in self.conskeys]
            self.addData(datakeys, nconns)
            self.problemtype = None
            
        return None
