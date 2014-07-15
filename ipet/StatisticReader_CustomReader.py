from StatisticReader import StatisticReader
import re
import __builtin__

class CustomReader(StatisticReader):
   '''
   Reader to be initialised interactively through IPET or from an interactive python shell
   '''
   name = 'CustomReader'
   regexp = 'Custom'
   datakey = 'Custom'
   activateexpression = "CUSTOM"
   data = None



   def __init__(self, **kw):
      self.name = kw.get("name", self.name)
      self.activateexpression = kw.get("activateexpression", self.activateexpression)
      self.regexp = kw.get("regexp", self.regexp)
      self.datakey = kw.get("datakey", self.datakey)
      self.index = kw.get("index", 0)
      self.active = False
      self.defaultvalue = kw.get("defaultvalue", 0.0)
      self.data = self.defaultvalue
      self.setDataType(kw.get("datatype", 'float'))

   def extractStatistic(self, line):
      if not self.active and (self.activateexpression == "" or re.search(self.activateexpression, line)):
         self.active = True
      if self.active and re.search(self.regexp, line):

         try:
            self.data = self.getNumberAtIndex(line, self.index)
            self.data = self.datatype(self.data)
         except:
            print "Error when parsing data -> using default value", self.name
            self.data = self.datatype(self.defaultvalue)

         self.active = False
      return None

   def execEndOfProb(self):
      self.active = False
      self.testrun.addData(self.problemname, self.datakey, self.data)
      self.data = self.datatype(self.defaultvalue)

   def setDataType(self, sometype):
      '''
      recognizes data types (e.g., 'float' or 'int') and sets reader data type to this value
      '''
      try:
         self.datatype = getattr(__builtin__, sometype)
      except:
         print "Error: Could not recognize data type, using float", sometype
         self.datatype = float
