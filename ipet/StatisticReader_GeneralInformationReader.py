# -*- coding: utf-8 -*-
from StatisticReader import StatisticReader
import re
import os
class GeneralInformationReader(StatisticReader):
    '''
       this reader extracts general information from a log file, that is, the solver version, the used LP solver
       in case of SCIP and the settings
    '''
    name = 'GeneralInformationReader'
    regular_exp = ['loaded parameter file', 'default.set']
    actions = {}
    testrun = None

    versionkeys = {StatisticReader.SOLVERTYPE_SCIP : 'SCIP version',
                   StatisticReader.SOLVERTYPE_CPLEX : "Welcome to IBM(R) ILOG(R) CPLEX(R)",
                   StatisticReader.SOLVERTYPE_GUROBI : "Gurobi Optimizer version",
                   StatisticReader.SOLVERTYPE_CBC : "Version:",
                   StatisticReader.SOLVERTYPE_XPRESS : "FICO Xpress Optimizer",
                   StatisticReader.SOLVERTYPE_COUENNE : " Couenne  --  an Open-Source solver for Mixed Integer Nonlinear Optimization"}

    versionlineindices = {StatisticReader.SOLVERTYPE_SCIP : 2,
                          StatisticReader.SOLVERTYPE_CPLEX :-1,
                          StatisticReader.SOLVERTYPE_GUROBI :-1,
                          StatisticReader.SOLVERTYPE_CBC :-1,
                          StatisticReader.SOLVERTYPE_XPRESS: 4,
                          StatisticReader.SOLVERTYPE_COUENNE:-1}

    def __init__(self, testrun=None):
        self.testrun = testrun

    def extractStatistic(self, line):
        if self.testrun == None:
            return

        if re.search(self.versionkeys[StatisticReader.solvertype], line):
            self.testrun.addData(self.problemname, 'Solver', StatisticReader.solvertype)

            if StatisticReader.solvertype == StatisticReader.SOLVERTYPE_SCIP:
                self.__handleVersion(line)
            else:
                self.testrun.addData(self.problemname, 'Version', line.split()[self.versionlineindices[StatisticReader.solvertype]])
        elif  StatisticReader.solvertype == StatisticReader.SOLVERTYPE_SCIP:
            if line.startswith('loaded parameter file'):
#               loaded parameter file </nfs/optimi/kombadon/bzfhende/projects/scip-git/check/../settings/testmode.set>
                absolutesettingspath = line[len('loaded parameter file '):].strip('<>')
                self.testrun.addData(self.problemname, 'AbsolutePathSettings', absolutesettingspath)
                settings = os.path.basename(absolutesettingspath)
                settings = os.path.splitext(settings)[0]


        elif StatisticReader.solvertype == StatisticReader.SOLVERTYPE_CPLEX:
            if "CPLEX> Non-default parameters written to file" in line:
                self.testrun.addData(self.problemname, 'Settings', line.split('.')[-3])

    def __handleVersion(self, line):
        '''
        handles more than just the version

        SCIP version 3.1.0.1 [precision: 8 byte] [memory: block] [mode: debug] [LP solver: SoPlex 2.0.0.1] [GitHash: 825e268-dirty]
        '''
        version = line.split()[2]
        self.testrun.addData(self.problemname, 'Version', version)
        for keyword in ["mode", "LP solver", 'GitHash']:
            data = re.search(r"\[%s: ([\w .-]+)\]" % keyword, line)
            if data:
                self.testrun.addData(self.problemname, keyword if keyword != "LP solver" else "LPSolver", data.groups()[0])


