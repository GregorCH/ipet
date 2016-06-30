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
    data = None

    METHOD_FIRST = 1
    METHOD_LAST = 2
    METHOD_SUM = 3

    str2method = {
                  "first" : METHOD_FIRST,
                  "last" : METHOD_LAST,
                  "sum" : METHOD_SUM
                  }




    def __init__(self, name = None, regpattern = None, datakey = None, index = 0, datatype = "float", method = "last"):

        if regpattern is None:
            raise ValueError("Error: No 'regpattern' specified for reader with name %s" % str(name))

        if name is None:
            name = CustomReader.name + regpattern
        self.name = name

        if datakey is None:
            datakey = CustomReader.datakey + regpattern
        self.datakey = datakey

        self.regpattern = regpattern
        self.regexp = re.compile(regpattern)
        self.index = int(index)

        self.method = self.str2method[method]

        self.datatype = datatype
        self.setDataType(datatype)

    def getEditableAttributes(self):
        return ['name', 'regpattern', 'datakey', 'index', 'datatype', 'method']

    def extractStatistic(self, line):
        if self.regexp.search(line):

            try:
                data = self.getNumberAtIndex(line, self.index)
                data = self.datatypemethod(data)

                previousdata = self.testrun.problemGetData(self.problemname, self.datakey)

                if self.method == CustomReader.METHOD_FIRST:
                    if previousdata is None:
                        self.testrun.addData(self.problemname, self.datakey, data)

                elif self.method == CustomReader.METHOD_LAST:
                    self.testrun.addData(self.problemname, self.datakey, data)

                elif self.method == CustomReader.METHOD_SUM:
                    if previousdata is None:
                        previousdata = 0

                    self.testrun.addData(self.problemname, self.datakey, data + previousdata)



            except:
                print "Error when parsing data -> using default value", self.name
                pass


        return None

    def setDataType(self, sometype):
        '''
        recognizes data types (e.g., 'float' or 'int') and sets reader data type to this value
        '''
        try:
            self.datatypemethod = getattr(__builtin__, sometype)
        except:
            print "Error: Could not recognize data type, using float", sometype
            self.datatypemethod = float
