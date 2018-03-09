"""
The MIT License (MIT)

Copyright (c) 2018 Zuse Institute Berlin, www.zib.de

Permissions are granted as stated in the license file you have obtained
with this software. If you find the library useful for your purpose,
please refer to README.md for how to cite IPET.

@author: Gregor Hendel
"""
from .StatisticReader import StatisticReader
import re
from ipet.misc import misc

class CustomHistoryReader(StatisticReader):
    """
    reads a history list from the table output in a SCIP log file; initialize with a list of column header strings as, e.g.,
    ['nodes', 'frac', ...]. The history reader parses each table line for tuples (a,b,...) corresponding to the
    requested column names. The history is returned as a list of tuples [(a1,b1, ...), (a2,b2, ...), ...,(an,bn, ...)]
    where each a(i) is different from a(i-1).
    """

    name = 'CustomHistoryReader'
    regular_exp = re.compile('\|')  # compile the regular expression to speed up reader
    datakey = 'somehistory'
    heuristicdispcharexp = re.compile('[a-zA-Z*]')
    numericexpression = misc.tablenumericExpression  # use the sophisticated numeric expression from the Custom Reader

    def __init__(self, listofheaders, listofindices=[], name='', collectheuristics=-1):
        """
        Constructor takes column header list as argument.

        - listofheaders: List of header names of columns to  parse common history for
        - listofindices: (optional) column indices of columns to parse from. Need not be passed since history reader
        -                can retrieve the required indices automatically
        - name         : (optional) a name for this history reader; if left out, the name will be parsed from the listofheaders
                       via capitalized column names + HistoryReader as suffix.
        """
        self.reset()
        self.listofheaders = listofheaders[:]
        if listofindices == []:
            self.listofindices = [-1] * len(self.listofheaders)
        else:
            self.listofindices = listofindices[:]
        if name != '':
            self.name = name
        else:
            self.name = ''.join(map(str.capitalize, self.listofheaders)) + "HistoryReader"

        self.datakey = ''.join(map(str.capitalize, self.listofheaders))

        self.collectheuristics = collectheuristics

    def reset(self):
        """
        reset all attributes to default values for a new problem
        """
        self.valuehistory = []

    def extractStatistic(self, line):
        
        # search for lines with at least 8 vertical bars - such lines are table lines
        if len(self.regular_exp.findall(line)) > 8:
        
            # parse all numbers from the table, including '-' and '--'. If there are too few or no numbers,
            # line is most certainly one of the less frequent table header lines and can be used to retrieve
            # the index of the columns, if not already done.
            listofnumbersintable = self.numericexpression.findall(line)
            if len(listofnumbersintable) > 4:
                try:
                    # parse values from the table
                    numberlist = [self.turnIntoFloat(listofnumbersintable[idx]) for idx in self.listofindices]
                    if self.collectheuristics >= 0:
                        heurdispchar = ''
                        if self.heuristicdispcharexp.match(line):
                            heurdispchar = line[0]
                        numberlist.insert(self.collectheuristics, heurdispchar)
                    values = tuple(numberlist)
                    
                    # remove the preceding values tuple from history if their first elements are equal
                    if self.collectheuristics != 0 and len(self.valuehistory) > 0 and self.valuehistory[-1][0] == values[0]:
                        self.valuehistory.pop(-1)
                    
                    # store newly found values
                    if self.collectheuristics != 0 or values[0] != '':
                        self.valuehistory.append(values)
                
                except ValueError:
                    return
                    # catch value errors,
            
            elif -1 in self.listofindices:
                # parse indices of columns corresponding to the headers
                splittedlinenowhitespace = list(map(str.strip, line.split('|')))
                self.listofindices = list(map(splittedlinenowhitespace.index, self.listofheaders))
    

    def execEndOfProb(self):
        """
        copies the aquired list of value tuples into testrun data
        """
        self.addData(self.datakey, self.valuehistory[:])
        self.reset()
