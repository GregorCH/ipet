# -*- coding: utf-8 -*-
from .StatisticReader import StatisticReader
import re

class VariableReader(StatisticReader):
    '''
    Reader class to parse SCIP variable and constraint counts for original and transformed problem
    '''
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
