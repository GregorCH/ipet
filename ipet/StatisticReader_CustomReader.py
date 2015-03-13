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



   def __init__(self, name=None, regpattern=None, activateexpression=None, datakey=None, index=0, datatype="float"):

      if regpattern is None:
          raise ValueError("Error: No 'regpattern' specified for reader with name %s"%str(name))

      if activateexpression is None:
          raise ValueError("Error: No 'activateexpression' specified for reader with name %s"%str(name))

      if name is None:
          name = CustomReader.name + regpattern
      self.name = name

      if datakey is None:
          datakey = CustomReader.datakey + regpattern
      self.datakey = datakey

      self.activateexpression = activateexpression
      self.regpattern = regpattern
      self.regexp = re.compile(regpattern)
      self.index = int(index)

      self.datatype = datatype
      self.setDataType(datatype)

      self.active = False

   def getEditableAttributes(self):
       return ['name', 'regpattern', 'activateexpression', 'datakey', 'index', 'datatype']

   def extractStatistic(self, line):
      if not self.active and (self.activateexpression == "" or re.search(self.activateexpression, line)):
         self.active = True
      if self.active and self.regexp.search(line):

         try:
            self.data = self.getNumberAtIndex(line, self.index)
            self.data = self.datatypemethod(self.data)

            self.testrun.addData(self.problemname, self.datakey, self.data)
         except:
            print "Error when parsing data -> using default value", self.name
            pass

         self.active = False
      return None

   def execEndOfProb(self):
      self.active = False

   def setDataType(self, sometype):
      '''
      recognizes data types (e.g., 'float' or 'int') and sets reader data type to this value
      '''
      try:
         self.datatypemethod = getattr(__builtin__, sometype)
      except:
         print "Error: Could not recognize data type, using float", sometype
         self.datatypemethod = float
