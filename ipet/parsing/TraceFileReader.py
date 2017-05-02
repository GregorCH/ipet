"""
The MIT License (MIT)

Copyright (c) 2016 Zuse Institute Berlin, www.zib.de

Permissions are granted as stated in the license file you have obtained
with this software. If you find the library useful for your purpose,
please refer to README.md for how to cite IPET.

@author: Gregor Hendel
"""
from .StatisticReader import StatisticReader
from ipet.misc import FLOAT_INFINITY
import logging
class TraceFileReader(StatisticReader):
    """
    classdocs
    """
    active = False
    context = StatisticReader.CONTEXT_TRACEFILE
    tracefilestartexpression = "* Trace Record Definition"
    input = "InputFileName,ModelType,SolverName,OptionFile,Direction,NumberOfEquations,NumberOfVariables,NumberOfDiscreteVariables,NumberOfNonZeros,NumberOfNonlinearNonZeros," + \
            "ModelStatus,SolverStatus,ObjectiveValue,ObjectiveValueEstimate,SolverTime,ETSolver,NumberOfIterations,NumberOfNodes"
    datakeys = input.split(",")[1:]
    
    floatmap = {"NA":None,
                "-INF":-FLOAT_INFINITY,
                "+INF":+FLOAT_INFINITY
                }

    def prepareData(self, value):
        value = self.floatmap.get(value, value)
        if value is None:
            return None

        for datatype in (int, float):
            try:
                return datatype(value)
            except ValueError:
                pass

        return value

    def extractStatistic(self, line):
        # FARIDO What do we do here? How does this kind of trace file look like?
        if line.startswith(self.tracefilestartexpression):
            self.active = True
        elif self.active and not line.startswith("*"):
            splitline = line.split(",")
            probname = splitline[0]
            datavalues = list(map(self.prepareData, splitline[1:]))

            logging.debug("Trace File Reader adds data for problem %s", probname)
            self.testrun.addData(probname, self.datakeys, datavalues)



