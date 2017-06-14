"""
The MIT License (MIT)

Copyright (c) 2016 Zuse Institute Berlin, www.zib.de

Permissions are granted as stated in the license file you have obtained
with this software. If you find the library useful for your purpose,
please refer to README.md for how to cite IPET.

@author: Gregor Hendel
"""
from .StatisticReader import StatisticReader
from ipet import Key
import re
import numpy as np

class SoluFileReader(StatisticReader):
    """A reader for solu file context information
    """
    name = 'SoluFileReader'
    actions = {}
    datakeys = [Key.OptimalValue, Key.SolutionFileStatus]
    statistics = {}
    columnwidth = 12
    columnheaderstr = 'SoluFile'.rjust(columnwidth)
    context = Key.CONTEXT_SOLUFILE

    def setTestRun(self, testrun):
        self.testrun = testrun
        if testrun != None:
            self.statistics = self.testrun.data

    def extractStatistic(self, line):
        assert self.testrun != None
        match = re.match("^=([a-zA-Z]+)=", line)
        if match:
            method = getattr(self, "new" + match.groups(0)[0] + "Problem")
            method(line)
        else:
            return None

    def storeToStatistics(self, problemname, objval, status):
        if self.testrun.hasProblemName(problemname):
            self.testrun.addDataByName(self.datakeys, [float(objval), status], problemname)

    def newoptProblem(self, line):
        splittedline = line.split()
        assert splittedline[0] == '=opt='
        problem = splittedline[1]
        objval = splittedline[2]

        self.storeToStatistics(problem, objval, status='opt')

    def newinfProblem(self, line):
        splittedline = line.split()
        assert splittedline[0] == '=inf='
        problem = splittedline[1]
        objval = np.nan

        self.storeToStatistics(problem, objval, status='inf')

    def newunknProblem(self, line):
        splittedline = line.split()
        assert splittedline[0] == '=unkn='
        problem = splittedline[1]
        objval = np.nan

        self.storeToStatistics(problem, objval, status='unkn')


    def newbestProblem(self, line):
        splittedline = line.split()
        assert splittedline[0] == '=best='
        problem = splittedline[1]
        objval = splittedline[2]

        self.storeToStatistics(problem, objval, status='best')

    def newcutProblem(self, line):
        splittedline = line.split()
        assert splittedline[0] == '=cut='
        problem = splittedline[1]
        objval = splittedline[2]

        self.storeToStatistics(problem, objval, status='cut')

    def newfeasProblem(self, line):
        splittedline = line.split()
        assert splittedline[0] == '=feas='
        problem = splittedline[1]
        objval = np.nan

        self.storeToStatistics(problem, objval, status='feas')

    def newbestdualProblem(self, line):
        splittedline = line.split()
        assert splittedline[0] == '=bestdual='
        problem = splittedline[1]
        dualval = splittedline[2]

        self.storeToStatistics(problem, dualval, status='bestdual')
