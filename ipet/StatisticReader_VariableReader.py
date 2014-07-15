# -*- coding: utf-8 -*-
from StatisticReader import StatisticReader
import re

class VariableReader(StatisticReader):
   name = 'VariableReader'
   regular_exp = re.compile(r'^  Variables        :')
   datakeys = ['Vars', 'BinVars', 'IntVars', 'ImplVars', 'ContVars']
   ready = False

   def extractStatistic(self, line):
      if line.startswith('Presolved Problem  :'):
         self.ready = True

      if self.ready and self.regular_exp.match(line):
         self.ready = False
         nvariables = map(int, self.numericExpression.findall(line))
         self.testrun.addData(StatisticReader.problemname, self.datakeys, nvariables)
      return None
