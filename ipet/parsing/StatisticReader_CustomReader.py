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
import builtins
import logging

class CustomReader(StatisticReader):
    """
    Reader to be initialised interactively through IPET or from an interactive python shell
    """
    name = 'CustomReader'
    regexp = 'Custom'
    datakey = 'Custom'
    data = None

    METHOD_FIRST = 1
    METHOD_LAST = 2
    METHOD_SUM = 3
    METHOD_MIN = 4
    METHOD_MAX = 5
    METHOD_COUNT = 6

    str2method = {
                  "first" : METHOD_FIRST,
                  "last" : METHOD_LAST,
                  "sum" : METHOD_SUM,
                  "min" : METHOD_MIN,
                  "max" : METHOD_MAX,
                  "count" : METHOD_COUNT
                  }


    requiredoptions = {
            "datatype" : ["float", "int"],
            "method" : list(str2method.keys())
        }

    def __init__(self, name=None, regpattern=None, datakey=None, index=0, datatype="float", method="last"):
        """
        constructor of a custom reader to parse additional simple solver output from log file context

        Parameters:
        -----------

        name : a name to distinguish this reader from the others

        regpattern : A string or regular expression pattern to detect lines from which output should be read

        datakey : The data key under which the parsed datum gets stored for every problem

        index : The zero-based index of the number in the specified line (only numbers count)

        datatype : choose 'int' or 'float'

        method : how to treat multiple occurrences of this data within one problem; 'count' occurrences or parse 'first', 'last', 'sum', 'min' or 'max'
        """

        if regpattern is None:
            raise ValueError("Error: No 'regpattern' specified for reader with name %s" % str(name))

        if name in [None, ""]:
            self.name = datakey + "Reader"
            self.username = False
        else:
            self.name = name
            self.username = True

        self.set_datakey(datakey)

        self.set_index(index)

        self.regpattern = regpattern
        self.set_regpattern(regpattern)

        self.method = method
        self.methodint = self.METHOD_LAST
        self.set_method(method)

        self.set_datatype(datatype)

    def getEditableAttributes(self):
        return ['name', 'regpattern', 'datakey', 'index', 'datatype', 'method']

    def getRequiredOptionsByAttribute(self, attr):
        return self.requiredoptions.get(attr, None)

    def extractStatistic(self, line):
        if self.regexp.search(line):

            try:
                data = self.getNumberAtIndex(line, self.index)
                data = self.datatypemethod(data)

                previousdata = self.testrun.getProblemDataById(self.problemname, self.datakey)

                if self.methodint == CustomReader.METHOD_FIRST:
                    if previousdata is None:
                        self.addData(self.datakey, data)

                elif self.methodint == CustomReader.METHOD_LAST:
                    self.addData(self.datakey, data)

                elif self.methodint == CustomReader.METHOD_SUM:
                    if previousdata is None:
                        previousdata = 0

                    self.addData(self.datakey, data + previousdata)

                elif self.methodint == CustomReader.METHOD_MIN:
                    if previousdata is None:
                        self.addData(self.datakey, data)
                    elif data < previousdata:
                        self.addData(self.datakey, data)

                elif self.methodint == CustomReader.METHOD_MAX:
                    if previousdata is None:
                        self.addData(self.datakey, data)
                    elif data > previousdata:
                        self.addData(self.datakey, data)
                elif self.methodint == CustomReader.METHOD_COUNT:
                    if previousdata is None:
                        self.addData(self.datakey, 1)
                    else:
                        self.addData(self.datakey, previousdata + 1)



            except:
                logging.debug("Reader %s could not retrieve data at index %d from matching line '%s'", self.getName(), self.index, line)
                pass


        return None

    def setDataType(self, sometype):
        """
        recognizes data types (e.g., 'float' or 'int') and sets reader data type to this value
        """
        try:
            # FARI how to resolve this error?
            # self.datatypemethod = getattr(__builtin__, sometype)
            self.datatype = sometype
        except:
            logging.debug("Error: Could not recognize data type %s, using float" % sometype)
            self.datatypemethod = float
            self.datatype = 'float'
            
    def set_datatype(self, datatype):
        self.setDataType(datatype)

    def set_method(self, method):
        self.methodint = self.str2method.get(method, self.methodint)
        self.method = method

    def set_regpattern(self, regpattern):
        self.regexp = re.compile(regpattern)
        self.regpattern = regpattern
        
    def set_name(self, name):
        if name == self.getName():
            return
        if name in ["", None]:
            self.name = self.datakey + "Reader"
            self.username = False
        else:
            self.name = name
            self.username = True
        
        
    def set_datakey(self, datakey):
        self.datakey = datakey
        if not self.username:
            self.name = self.datakey + "Reader"

    def set_index(self, index):
        self.index = int(index)
