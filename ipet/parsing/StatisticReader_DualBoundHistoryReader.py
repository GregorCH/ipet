from StatisticReader import StatisticReader
import re
from ipet.misc import misc

class DualBoundHistoryReader(StatisticReader):
    '''
    reads the dual bound history out of a SCIP log file. returns a list of tuples (t,db) where t denotes the
    time when a new dual bound was reported, and db is the dual bound value. Every t and db should occur only once
    in the final list
    '''

    name = 'DualBoundHistoryReader'
    regular_exp =  re.compile('\|') # compile the regular expression to speed up reader
    datakey = 'dualboundhistory'
    dbindex = -1
    timeindex = 0


    def __init__(self):
        self.reset()


    def reset(self):
        '''
        reset all attributes to default values for a new problem
        '''
        self.dualboundlist = []
        self.lastdb = misc.FLOAT_INFINITY
        self.lasttime = -1

    def extractStatistic(self, line):
        '''
        search for lines with at least 15 vertical bars - such lines are table lines

        parse all numbers from the table, including '-' and '--'. If there are too few or no numbers,
         line is most certainly one of the less frequent table header lines and can be used to retrieve
         the index of the dual bound column
        '''
        if self.isTableLine(line):
            if self.dbindex == -1:
                # parse index of dual bound entry
                splittedlinenowhitespace = map(str.strip, line.split('|'))
                self.dbindex = splittedlinenowhitespace.index('dualbound')

            try:
                listofnumbersintable = self.tablenumericExpression.findall(line)
                # parse time and dual bound from the table
                time = float(listofnumbersintable[self.timeindex])
                dualbound = float(listofnumbersintable[self.dbindex])
                # store newly found (time, dual bound) tuple if it differs from the last dual bound
                if self.lastdb != dualbound:

                    # remove previous dual bound if time stamp is equal
                    if self.lasttime == time:
                        elembefore = self.dualboundlist.pop(-1)
                        assert self.lasttime == elembefore[0]

                    # store new dual bound
                    self.dualboundlist.append((time, dualbound))
                    self.lastdb = dualbound
                    self.lasttime = time
              
            except ValueError:
                return None
            except IndexError:
                return None
                # catch value errors, most likely because dual bound column displays '--'
#                print "Could not parse time and dual bound from line", line
#                print "numbers from line: ", listofnumbersintable
        
#           print "Dual Bound index set to ", self.dbindex
        
        # do not return anything since there might be more dual bounds to come
        return None
     
    def isTableLine(self, line):
        return (line.count('|') > 10)
     
    def execEndOfProb(self):
        '''
        returns a dual bound history list
        '''
        if self.dualboundlist != []:
            
            #only copy nonempty lists, otherwise Parascipdualboundhistoryreader and this one will overwrite each others data
            self.testrun.addData(self.problemname, self.datakey, self.dualboundlist[:])
        
        self.reset()
        
class ParascipDualBoundHistoryReader(DualBoundHistoryReader):
    name="ParascipDualBoundHistoryReader"
    parascipheader = "     Time          Nodes        Left   Solvers     Best Integer        Best Node"
    dbindex = 5
    intable = False
    
    def isTableLine(self, line):
        ''' overwrites in table method of Dual Bound History Reader
        '''
        if not self.intable and line.startswith(self.parascipheader):
            self.intable = True
            return False
        elif self.intable and line.startswith("SCIP Status"):
            self.intable = False
            return False
        else:
            return self.intable

    def reset(self):
        DualBoundHistoryReader.reset(self)
        self.intable = False
