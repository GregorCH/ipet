from StatisticReader import StatisticReader
import re

class HeurDataReader(StatisticReader):
   name = 'HeurDataReader'
   defaultDatakeys = ['HeurCalls', 'HeurSols', 'HeurTime']
   indices = [-2,-1,-4]
   isHeurLine = False
   index = -1
   datatypes = [int, int, float]
   sleepAfterReturn = False

   def parseData(self, assumedtype, value):
      '''
      parse data into type, or return None if parse failed
      '''
      try:
         return assumedtype(value)
      except ValueError:
         return 0

   def extractStatistic(self, line):
      if not self.isHeurLine and re.search('Primal Heuristics  :', line):
         self.isHeurLine = True
      elif self.isHeurLine and re.search("^[A-Za-z]", line):
         self.isHeurLine = False
      elif self.isHeurLine:
#                print line
         newline = line.split()
         heurname = newline[0].rstrip(':')
         datakeys = ['_'.join((datakey, heurname)) for datakey in self.defaultDatakeys]
         data = [self.parseData(assumedtype, newline[idx]) for assumedtype, idx in zip(self.datatypes, self.indices)]
         self.testrun.addData(self.problemname, datakeys, data)
