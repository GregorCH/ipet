'''
The MIT License (MIT)

Copyright (c) 2016 Zuse Institute Berlin, www.zib.de

Permissions are granted as stated in the license file you have obtained
with this software. If you find the library useful for your purpose,
please refer to README.md for how to cite IPET.

@author: Gregor Hendel
'''
from .StatisticReader import StatisticReader
import re

class PrimalBoundHistoryReader(StatisticReader):
    name = 'PrimalBoundHistoryReader'
    regular_exp = re.compile('^\s+time\s+\| .* \|\s+primalbound\s+\|\s+gap')
    ugtableexp = re.compile('^\s+Time\s+Nodes')
    columnwidth = 20
    datakey = 'PrimalBoundHistory'
    columnheaderstr = 'PrimalBoundHistory'.rjust(columnwidth)
    inTable = False
    lastPrimalBound = '--'
    listOfPoints = []
    easyCPLEX = True
    totalnumberofsols = 0
    heurdispcharexp = re.compile('^[^ \d]')
    heurdispcharexpugmode = re.compile('^\*')
    """ all lines starting with a non-whitespace and non-digit character """

    shorttablecheckexp = re.compile('s\|')
    firstsolexp = re.compile('^  First Solution   :')

    testnumberofsols = 0
    gurobiextralist = []

    ugmode = False

    def extractStatistic(self, line):
        if StatisticReader.solvertype == StatisticReader.SOLVERTYPE_SCIP:
            # is the line a column header ?

            if not self.inTable:
                if self.regular_exp.search(line):

                    self.inTable = True
                elif self.ugtableexp.match(line):
                    self.inTable = True
                    self.ugmode = True

            elif line.startswith("SCIP Status") and self.inTable:
                self.inTable = False
                self.ugmode = False

            # history reader should be in a table. check if a display char indicates a new primal bound
            elif self.inTable and self.heurdispcharexp.match(line) and not self.ugmode or \
		 self.inTable and self.heurdispcharexpugmode.match(line) and self.ugmode:

                if not (self.shorttablecheckexp.search(line) or self.ugmode):
                    return

                if not self.ugmode:
                    allmatches = self.numericExpression.findall(line[:line.rindex("|")])
                else:
                    allmatches = self.numericExpression.findall(line)[:5]

                if len(allmatches) == 0:
                    return

                pointInTime = allmatches[0]
                PrimalBound = allmatches[-1]

                # in the case of ugscip, we reacted on a disp char, so no problem at all.
                if PrimalBound != self.lastPrimalBound:
                    self.lastPrimalBound = PrimalBound
                    self.listOfPoints.append((float(pointInTime), float(PrimalBound)))

            elif not self.inTable and self.firstsolexp.match(line):
                matches = self.numericExpression.findall(line)
                PrimalBound = matches[0]
                pointInTime = matches[3]
                if len(self.listOfPoints) == 0:
                    self.listOfPoints = [(float(pointInTime), float(PrimalBound))]
                elif float(pointInTime) <= self.listOfPoints[0][0]:
                    self.listOfPoints.insert(0, (float(pointInTime), float(PrimalBound)))
                else:
                    self.listOfPoints.insert(0, (self.listOfPoints[0][0], float(PrimalBound)))

        elif StatisticReader.solvertype == StatisticReader.SOLVERTYPE_GUROBI:
            if "Found heuristic solution" in line:
                self.gurobiextralist.append(line.split()[-1])
            if "Expl Unexpl |  Obj  Depth" in line:
                self.inTable = True
            elif self.inTable and line.endswith("s\n") and self.gurobiextralist != []:
#              print "+++++++++++++++++++++"
                pointInTime = line.split()[-1].strip("s")
                self.listOfPoints.append((float(pointInTime), float(self.gurobiextralist[-1])))
                self.gurobiextralist = []
            elif self.inTable and line.startswith("H") or line.startswith("*"):
                self.readBoundAndTime(line, -5, -1, timestripchars="s")

            elif "Cutting planes:" in line and self.inTable:
                self.inTable = False
            elif self.gurobiextralist != [] and "Explored " in line:
#              print "-------------------------"
                pointInTime = line.split()[-2]
                self.listOfPoints.append((float(pointInTime), float(self.gurobiextralist[-1])))
                self.gurobiextralist = []

            return None

        elif StatisticReader.solvertype == StatisticReader.SOLVERTYPE_CBC or StatisticReader.solvertype == StatisticReader.SOLVERTYPE_COUENNE:
            if "Integer solution of " in line:
                self.readBoundAndTime(line, 4, -2, timestripchars="(")

            return None

        elif StatisticReader.solvertype == StatisticReader.SOLVERTYPE_XPRESS:
            if "BestSoln" in line:
                self.xpresscutidx = line.index("BestSoln") + len("BestSoln")
            elif line.startswith("+") or line.startswith("*"):
                self.readBoundAndTime(line, -1, -1, cutidx=self.xpresscutidx)
            elif line.startswith(" *** Heuristic solution found: "):
                self.readBoundAndTime(line, -4, -2)

        elif StatisticReader.solvertype == StatisticReader.SOLVERTYPE_CPLEX:
            if "Solution pool: " in line:
                self.testnumberofsols = int(line.split()[2])
                # assert len(self.listOfPoints) >= self.testnumberofsols
            if self.easyCPLEX and "Found incumbent of value" in line:
                splitline = line.split()
                self.readBoundAndTime(line, splitline.index("Found") + 4, splitline.index("Found") + 6)
            elif not self.easyCPLEX:
                if "Welcome to IBM(R) ILOG(R) CPLEX(R)" in line:
                    self.lastelapsedtime = 0.0
                    self.nnodessincelastelapsedtime = 0
                    self.lastnnodes = 0
                    self.cpxprimals = []

                if "   Node  Left     Objective  IInf  Best Integer    Best Bound    ItCnt     Gap" in line:
                    self.inTable = True

                    self.cpxbestintegeridx = line.index("Best Integer") + 11

                elif self.inTable and ("cuts applied:" in line or "Root node processing" in line):
                    self.inTable = False
                elif self.inTable and "Repeating presolve." in line:
                    self.inTable = False
                elif self.inTable and len(line) > 0 and line.startswith(" ") or line.startswith("*"):
                    if line == "\n":
                        return None
                    nodeinlineidx = 7
                    while line[nodeinlineidx] != " " and line[nodeinlineidx] != "+":
                        nodeinlineidx += 1
                    print(line)
                    nnodes = int(line[:nodeinlineidx].split()[-1].strip('*+')) + 1
                    if line.startswith("*") or line.startswith("+"):
                        print(line)
                        primalbound = float(line.split()[-4])
                        print(primalbound, nnodes)
                        self.cpxprimals.append((nnodes, primalbound))
                    self.lastnnodes = nnodes
                elif "Elapsed time = " in line:
                    thetime = float(line.split()[3])
                    self.processCpxprimals(thetime)

                    self.nnodessincelastelapsedtime = self.lastnnodes
                    self.lastelapsedtime = thetime

                elif "Solution time =" in line:
                    thetime = float(line.split()[3])
                    self.processCpxprimals(thetime)

        return None

    def readBoundAndTime(self, line, boundidx, timeidx, timestripchars="", cutidx= -1):
        splitline = line.split()

        primalbound = line[:cutidx].split()[boundidx]

        pointInTime = splitline[timeidx].strip(timestripchars)

#         print line
#         print pointInTime, primalbound


        self.lastPrimalBound = primalbound
        self.listOfPoints.append((float(pointInTime), float(primalbound)))

    def processCpxprimals(self, currenttime):
        solvednodes = (self.lastnnodes - self.nnodessincelastelapsedtime)
        timespentonnode = (currenttime - self.lastelapsedtime) / max(1.0, float(solvednodes))
        assert currenttime >= self.lastelapsedtime
        for node, bound in self.cpxprimals:
            estimatedtime = self.lastelapsedtime + (node - self.nnodessincelastelapsedtime) * timespentonnode

            if bound != self.lastPrimalBound:
                self.lastPrimalBound = bound
                if len(self.listOfPoints) > 0:
                    othertime, _ = self.listOfPoints[-1]
                    assert othertime <= estimatedtime
                    self.listOfPoints.append((float(estimatedtime), float(bound)))

        self.cpxprimals = []

    def execEndOfProb(self):
        self.inTable = False
        self.testnumberofsols = 0
        theList = self.listOfPoints[:]
        self.listOfPoints = []
        self.lastPrimalBound = '--'
        PrimalBoundHistoryReader.totalnumberofsols += len(theList)
        # print " solutions added:", PrimalBoundHistoryReader.totalnumberofsols
        #print self.problemname, theList
        self.addData(self.datakey, theList)
