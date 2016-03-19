'''
Created on 31.07.2013

@author: bzfhende
'''
import re
from StatisticReader import StatisticReader

class PluginStatisticsReader(StatisticReader):
   '''
   Reader which tries to read various data about plugin types arranged in table format -
   Format Foo: a    b
          1  : 0    5
          2  : 7    9

   will be parsed into flattened data keys Foo_a_1, Foo_a_2, Foo_b_1 etc. and added to the testrun with their corresponding
   (numeric) table entry

   It can also read single column tables of the form
   Foo:
   a  : 1
   b  : 2
   ...

   and will store the corresponding values under Foo_a, and Foo_b
   '''
   name = 'PluginStatisticsReader'
   plugintypes = ['Presolvers', 'Constraints', 'Constraint Timings', 'Propagators', 'Propagator Timings', 'Conflict Analysis',
              'Separators', 'Branching Rules', 'Diving Statistics', 'LP', 'Branching Analysis']
   singlecolumnnames = ['Root Node', 'Total Time', 'B&B Tree']
   active = False
   spacesepcolumnnames = ['LP Iters']
   replacecolumnnames = [''.join(sscname.split()) for sscname in spacesepcolumnnames]
   wrongplugintype = 'Wrong'
   plugintype = wrongplugintype


   def convertToFloat(self, x):
      try:
         return float(x)
      except:
         return None

   def extractStatistic(self, line):
      if re.match('^SCIP Status', line):
         self.active = True

      elif self.active and re.match('[a-zA-Z]', line):
         if not re.search(':', line):
            return None
         try:
            colonidx = line.index(':')
         except:
            print StatisticReader.problemname, line
            raise Exception()
         plugintype = line[:colonidx].rstrip()
         self.plugintype = ''.join(plugintype.split())
         if plugintype in self.plugintypes:

            preprocessedline = line[colonidx + 1:]
            for expr, replacement in zip(self.spacesepcolumnnames, self.replacecolumnnames):
               preprocessedline = re.sub(expr, replacement, preprocessedline)

               # we are parsing a table
            self.columns = preprocessedline.split()

               # we are only parsing a single column
         elif plugintype in self.singlecolumnnames:
            self.columns = []
         else:
            self.plugintype = self.wrongplugintype

      elif self.active and self.plugintype != self.wrongplugintype:
         try:
            colonidx = line.index(':')
         except:
            self.plugintype = self.wrongplugintype
            return None

         pluginname = ''.join(line[:colonidx].split())

         #distinguish between vectors and
         if self.columns != []:

            # treat tables (tables with at least two data columns)
            datakeys = ['_'.join((self.plugintype, column, pluginname)) for column in self.columns]
            data = map(self.convertToFloat, StatisticReader.numericExpression.findall(line[colonidx+1:]))
         else:
            # treat vectors (tables with only one data column)
            datakeys = ['_'.join((self.plugintype, pluginname))]
            data = [self.convertToFloat(StatisticReader.numericExpression.search(line, colonidx + 1).group(0))]

         # determine minimum length (necessary if more headers were recognized than actual available data)
         minlen = min(len(datakeys), len(data))

         self.testrun.addData(StatisticReader.problemname, datakeys[:minlen], data[:minlen])

   def execEndOfProb(self):
      self.active = False
