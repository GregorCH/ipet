"""
The MIT License (MIT)

Copyright (c) 2016 Zuse Institute Berlin, www.zib.de

Permissions are granted as stated in the license file you have obtained
with this software. If you find the library useful for your purpose,
please refer to README.md for how to cite IPET.

@author: Gregor Hendel
"""
from .StatisticReader import StatisticReader, ListReader
from ipet.parsing.StatisticReader_CustomReader import CustomReader
import os
import re
import sys
from ipet.concepts.Manager import Manager
import xml.etree.ElementTree as ElementTree
# from .StatisticReader import PrimalBoundReader, DualBoundReader, ErrorFileReader, \
#     GapReader, SolvingTimeReader, TimeLimitReader, \
#     BestSolInfeasibleReader, MaxDepthReader, LimitReachedReader, ObjlimitReader, NodesReader, RootNodeFixingsReader, \
#     SettingsFileReader, TimeToFirstReader, TimeToBestReader, ObjsenseReader, DateTimeReader
from .StatisticReader import ErrorFileReader, \
    GapReader, TimeLimitReader, \
    BestSolInfeasibleReader, MaxDepthReader, NodesReader, RootNodeFixingsReader, \
    SettingsFileReader, TimeToFirstReader, TimeToBestReader, ObjsenseReader, DateTimeReader
from .StatisticReader_DualBoundHistoryReader import DualBoundHistoryReader, ParascipDualBoundHistoryReader
# from .StatisticReader_GeneralInformationReader import GeneralInformationReader
from .StatisticReader_PluginStatisticsReader import PluginStatisticsReader
from .StatisticReader_PrimalBoundHistoryReader import PrimalBoundHistoryReader
from .StatisticReader_VariableReader import VariableReader
from .StatisticReader_SoluFileReader import SoluFileReader
from .TraceFileReader import TraceFileReader
import logging
from ipet.concepts.IPETNode import IpetNode
from ipet.parsing.Solver import SCIPSolver, CbcSolver, CouenneSolver, \
    XpressSolver, GurobiSolver, CplexSolver
from ipet.parsing import Key
# from .Solver import SCIPSolver

class ReaderManager(Manager, IpetNode):
    """
    acquires test run data. subclasses of manager, managing readers by their unique name
    """
    extensions = [".mps", ".cip", ".fzn", ".pip", ".lp", ".gms", ".dat"]
    nodetag = "Readers"

    fileextension2context = {
                             ".err" : StatisticReader.CONTEXT_ERRFILE,
                             ".out" : StatisticReader.CONTEXT_LOGFILE,
                             ".set" : StatisticReader.CONTEXT_SETFILE,
                             ".solu": StatisticReader.CONTEXT_SOLUFILE,
                             ".trc" : StatisticReader.CONTEXT_TRACEFILE
                             }
    """map for file extensions to the file contexts to specify the relevant readers"""

    context2Sortkey = {
                       StatisticReader.CONTEXT_ERRFILE : 2,
                       StatisticReader.CONTEXT_LOGFILE : 1,
                       StatisticReader.CONTEXT_SETFILE : 3,
                       StatisticReader.CONTEXT_SOLUFILE : 4,
                       StatisticReader.CONTEXT_TRACEFILE : 5
                       }
    """ defines a sorting order for file contexts """

    xmlfactorydict = {"ListReader":ListReader, "CustomReader":CustomReader}

    def __init__(self, problemexpression = "@01", problemendexpression = "=ready="):
        """
        constructs a new reader Manager

        Parameters:
        -----------

        problemexpression : an expression that accompanies the start of a new instance in a log file context

        problemendexpression : an expression that signals the end of an instance in a log file context
        """
        Manager.__init__(self)
        # an ipet Node is always active
        IpetNode.__init__(self, True)
        self.problemexpression = problemexpression
        self.problemendexpression = problemendexpression
        self.addSolvers()
        self.activeSolver = self.solvers[0]
        # There also exist the following class params:
        # self.testrun
        # self.filestrings

    def getEditableAttributes(self):
        return ["problemexpression", "problemendexpression"]
    
    def addSolvers(self):
        self.solvers = [SCIPSolver(),
                        CbcSolver(),
                        CouenneSolver(),
                        XpressSolver(),
                        GurobiSolver(),
                        CplexSolver()]

    def getName(self):
        return "ReaderManager"

    def addChild(self, child):
        self.registerReader(child)

    def removeChild(self, child):
        self.deleteManageable(child)

    def acceptsAsChild(self, child):
        return child.__class__() in list(self.xmlfactorydict.values())

    def getChildren(self):
        return sorted([m for m in self.getManageables(False) if m.__class__ in list(self.xmlfactorydict.values())], key = lambda x:x.getName())

    @staticmethod
    def getNodeTag():
        return ReaderManager.nodetag

    def setTestRun(self, testrun):
        """
        changes the testrun for reading to the new testrun
        """
        logging.debug("Setting testrun to %s" % testrun.getName())
        self.testrun = testrun
        self.filestrings = testrun.filenames
        for reader in self.getManageables():
            reader.setTestRun(testrun)

    def addFileExtension2Context(self, extension, context):
        oldcontext = self.fileextension2context.get(extension)
        if  oldcontext is not None and oldcontext != context:
            raise ValueError("context for file extension %s already set to %d" % (extension, oldcontext))
        self.fileextension2context[extension] = context

    def getFileExtensions(self):
        """
        returns a list of all recognized file extensions by this Reader manager
        """
        return list(self.fileextension2context.keys())

    def addLogFileExtension(self, extension):
        """
        adds a new log file extension to the log file contexts
        """
        self.addFileExtension2Context(extension, StatisticReader.CONTEXT_LOGFILE)

    def addErrorFileExtension(self, extension):
        """
        adds a new error file extension to the error file contexts
        """
        self.addFileExtension2Context(extension, StatisticReader.CONTEXT_ERRFILE)

    def addSettingsFileExtension(self, extension):
        """
        adds a new settings file extension to settings file contexts
        """
        self.addFileExtension2Context(extension, StatisticReader.CONTEXT_SETFILE)

    def addSoluFileExtension(self, extension):
        """
        adds a new solu file extension to solu file contexts
        """
        self.addFileExtension2Context(extension, StatisticReader.CONTEXT_SOLUFILE)

    def getNReaders(self):
        """
        returns the number of readers
        """
        return len(self.countManageables())

    def hasReader(self, reader):
        listofnames = [installedreader.getName() for installedreader in self.getManageables()]
        if reader.getName() in listofnames:
            return True
        else:
            return False

    def registerReader(self, reader):
        self.addAndActivate(reader)

    def registerListOfReaders(self, readers):
        for reader in readers:
            self.addAndActivate(reader)

    def registerDefaultReaders(self):
        self.registerListOfReaders([
             BestSolInfeasibleReader(),
             DateTimeReader(),
#              DualBoundReader(),
             DualBoundHistoryReader(),
             ErrorFileReader(),
             ParascipDualBoundHistoryReader(),
             GapReader(),
#              GeneralInformationReader(),
             MaxDepthReader(),
#              LimitReachedReader(),
             NodesReader(),
             ObjsenseReader(),
             PluginStatisticsReader(),
             PrimalBoundHistoryReader(),
#              PrimalBoundReader(),
             VariableReader(),
             RootNodeFixingsReader(),
             SettingsFileReader(),
#             SolvingTimeReader(),
             SoluFileReader(),
             TimeLimitReader(),
             TimeToFirstReader(),
             TimeToBestReader(),
             TraceFileReader()
             ])

    def updateLineNumberData(self, linenumber, currentcontext, prefix):
        context2string = {StatisticReader.CONTEXT_LOGFILE:"LogFile",
                          StatisticReader.CONTEXT_ERRFILE:"ErrFile"}
        contextstring = context2string.get(currentcontext)
        if contextstring is None:
            return
        self.testrun.addData("%s%s" % (prefix, contextstring), linenumber)

    def getProblemName(self, line):
        fullname = line.split()[1]
        namewithextension = os.path.basename(fullname)
        # FARI Shouldn't this be something like ".gz"?
        if namewithextension.endswith("gz"):
            namewithextension = os.path.splitext(namewithextension)[0]
        for extension in self.extensions:
            if namewithextension.endswith(extension):
                namewithextension = os.path.splitext(namewithextension)[0]

        # now name without extension
        return namewithextension

    def finishProblemParsing(self, line, filecontext, readers):
        if filecontext in [StatisticReader.CONTEXT_ERRFILE, StatisticReader.CONTEXT_LOGFILE] and not self.testrun.instanceDataEmpty():
            self.updateLineNumberData(line[0], filecontext, "LineNumbers_End")
            for reader in readers:
                reader.execEndOfProb()

            if filecontext == StatisticReader.CONTEXT_LOGFILE and not self.endOfProblemReached(line[1]):
                logging.warning("Malformatted log output, probably a missing expression %s" % \
                               (self.problemendexpression))
            self.testrun.finalizeInstanceCollection(self.activeSolver)
            self.activeSolver.reset()

    def updateProblemName(self, line, currentcontext, readers):
        """
        sets up data structures for a new problem instance if necessary
        """
        problemname = self.getProblemName(line[1])

        self.testrun.addData(Key.ProblemName, problemname)
        # FARIDO what do we do here if we are reading from stdin?
        # self.testrun.addData('Settings', self.testrun.getSettings())
        self.updateLineNumberData(line[0], currentcontext, "LineNumbers_Begin")

    def endOfProblemReached(self, line):
        if line.startswith(self.problemendexpression):
            return True
        else:
            return False

    def startOfProblemReached(self, line):
        if line.startswith(self.problemexpression):
            return True
        else:
            return False

    def readSolverType(self, filename):
        """
        check the solver type for a given log file
        """
        with open(filename, "r") as currentfile:
            self.readSolverTypeDirectly(currentfile)

    def readSolverTypeDirectly(self, f):
        """
        check the solver type for a given log file
        """
        lines = []
        for line in f:
            lines.append(line)
            for solver in self.solvers:
                if line.startswith(solver.recognition_pattern):
                    self.activeSolver = solver
                    return lines

    def sortingKeyContext(self, context):
        try:
            return self.context2Sortkey[context]
        except IndexError:
            raise IndexError("Unknown context %d" % context)

    def filenameGetContext(self, filename):
        extension = os.path.splitext(os.path.basename(filename))[1]
        return self.fileextension2context[extension]

    def collectData(self):
        """
        runs data collection on the specified test run
        """
        assert(self.testrun != None)

        # sort the files by context, for example: outfiles should be read before solufiles
        if not self.testrun.inputfromstdin:
            self.filestrings = sorted(self.filestrings, key=lambda x:self.sortingKeyContext(self.filenameGetContext(x)))

        for filename in self.filestrings:
            f = None
            if self.testrun.inputfromstdin:
                f = sys.stdin.readlines()
            else:
                try:
                    f = open(filename, 'r')
                except IOError:
                    print('File', filename, "doesn't exist!")
                    continue

            # only enable readers that support the file context
            # Default to .out for stdinput, then change if needed
            filecontext = self.fileextension2context[".out"]
            if not self.testrun.inputfromstdin:
                filecontext = self.filenameGetContext(filename)
            readers = [r for r in self.getManageables(True) if r.supportsContext(filecontext)]

            # we enumerate the file so that line is a tuple (idx, line) that contains the line content and its number
            line = (0,"")
            startindex = 0
            # FARIDO How to do this better?
            # search the file for information about the type of the solver
            if self.testrun.inputfromstdin:
                # since we have can reach the lines from stdin only once, we have to save them
                consumedlines = self.readSolverTypeDirectly(f)
                for line in enumerate(consumedlines):
                    if self.startOfProblemReached(line[1]):
                        self.updateProblemName(line, filecontext, readers)
                        
                    if self.endOfProblemReached(line[1]):
                        self.finishProblemParsing(line, filecontext, readers)
                            
                    else:
                        self.activeSolver.readline(line[1])
                        for reader in readers:
                            reader.operateOnLine(line[1])
                startindex = len(consumedlines)
            else:
                self.readSolverType(filename)
                
            for line in enumerate(f, startindex):
                if self.startOfProblemReached(line[1]):
                    self.updateProblemName(line, filecontext, readers)
                
                if self.endOfProblemReached(line[1]):
                    self.finishProblemParsing(line, filecontext, readers)
                        
                else:
                    self.activeSolver.readline(line[1])
                    for reader in readers:
                        reader.operateOnLine(line[1])
            
            self.finishProblemParsing(line, filecontext, readers)
            
            if not self.testrun.inputfromstdin:
                f.close()
            self.testrun.finishedReadingFile(self.activeSolver)
        # print("Collection of data finished")
        return 1
    
    ### XML IO methods
    def toXMLElem(self):
        me = ElementTree.Element(ReaderManager.getNodeTag())
        readers = self.getManageables(False)
        for reader in readers:
            if reader.__class__ in list(ReaderManager.xmlfactorydict.values()):
                readerattrs = reader.attributesToDict()
                readerstrattrs = {key:str(val) for key, val in readerattrs.items()}
                for key in list(ReaderManager.xmlfactorydict.keys()):
                    if reader.__class__ is ReaderManager.xmlfactorydict[key]:
                        break
                me.append(ElementTree.Element(key, readerstrattrs))
        return me

    @staticmethod
    def fromXML(xmlstring):
        tree = ElementTree.fromstring(xmlstring)
        return ReaderManager.processXMLElem(tree)

    @staticmethod
    def fromXMLFile(xmlfilename):
        tree = ElementTree.parse(xmlfilename)
        return ReaderManager.processXMLElem(tree.getroot())

    @staticmethod
    def processXMLElem(elem):
        # FARI1 what if not? rm undefined?
        if elem.tag == ReaderManager.getNodeTag():
            rm = ReaderManager()
        for child in elem:
            reader = ReaderManager.xmlfactorydict[child.tag](**child.attrib)
            rm.registerReader(reader)
        return rm

