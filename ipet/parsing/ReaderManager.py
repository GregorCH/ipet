"""
The MIT License (MIT)

Copyright (c) 2016 Zuse Institute Berlin, www.zib.de

Permissions are granted as stated in the license file you have obtained
with this software. If you find the library useful for your purpose,
please refer to README.md for how to cite IPET.

@author: Gregor Hendel
"""
import os
import sys
import logging
import xml.etree.ElementTree as ElementTree
from .StatisticReader import ErrorFileReader, GapReader, TimeLimitReader, StatisticReader, ListReader, \
    BestSolInfeasibleReader, MaxDepthReader, NodesReader, RootNodeFixingsReader, \
    SettingsFileReader, TimeToFirstReader, TimeToBestReader, ObjsenseReader, DateTimeReader
from .StatisticReader_DualBoundHistoryReader import DualBoundHistoryReader, ParascipDualBoundHistoryReader
from .StatisticReader_PluginStatisticsReader import PluginStatisticsReader
from .StatisticReader_PrimalBoundHistoryReader import PrimalBoundHistoryReader
from .StatisticReader_VariableReader import VariableReader
from .StatisticReader_SoluFileReader import SoluFileReader
from .StatisticReader_CustomReader import CustomReader
from .TraceFileReader import TraceFileReader
from ipet.concepts.Manager import Manager
from ipet.concepts.IPETNode import IpetNode
from ipet.parsing.Solver import SCIPSolver
# CbcSolver, CouenneSolver, \
#     XpressSolver, GurobiSolver, CplexSolver
from ipet import Key

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

    def __init__(self, problemexpression="@01", problemendexpression="=ready="):
        """
        constructs a new reader Manager

        Parameters:
        -----------

        problemexpression : an expression that accompanies the start of a new problem in a log file context

        problemendexpression : an expression that signals the end of an problem in a log file context
        """
        Manager.__init__(self)
        # an ipet Node is always active
        IpetNode.__init__(self, True)
        self.problemexpression = problemexpression
        self.problemendexpression = problemendexpression
        self.addSolvers()
        self.activeSolver = self.solvers[0]
        self.solverCanRead = True
        
    def getEditableAttributes(self):
        return ["problemexpression", "problemendexpression"]
    
    def addSolvers(self):
        self.solvers = [SCIPSolver()]
#                         CbcSolver(),
#                         CouenneSolver(),
#                         XpressSolver(),
#                         GurobiSolver(),
#                         CplexSolver()]

    def getName(self):
        """
        Returns the name of the class
        """
        return "ReaderManager"

    def addChild(self, child):
        """
        adds a new reader as child
        """
        self.registerReader(child)

    def removeChild(self, child):
        """
        removes a reader
        """
        self.deleteManageable(child)

    def acceptsAsChild(self, child):
        """
        only accepts certain reader as children 
        """
        return child.__class__() in list(self.xmlfactorydict.values())

    def getChildren(self):
        """
        returns a sortet list of all readers
        """
        children = [m for m in self.getManageables(False) if m.__class__ in list(self.xmlfactorydict.values())]
        return sorted(children, key=lambda x:x.getName())

    @staticmethod
    def getNodeTag():
        """
        returns the name of the Readermanager
        """
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
        """
        Adds a new file context (associated to extension)
        """
        oldcontext = self.fileextension2context.get(extension)
        # don't overwrite existing content
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
        adds a new log file extension to the log file context
        """
        self.addFileExtension2Context(extension, StatisticReader.CONTEXT_LOGFILE)

    def addErrorFileExtension(self, extension):
        """
        adds a new error file extension to the error file context
        """
        self.addFileExtension2Context(extension, StatisticReader.CONTEXT_ERRFILE)

    def addSettingsFileExtension(self, extension):
        """
        adds a new settings file extension to settings file context
        """
        self.addFileExtension2Context(extension, StatisticReader.CONTEXT_SETFILE)

    def addSoluFileExtension(self, extension):
        """
        adds a new solu file extension to solu file context
        """
        self.addFileExtension2Context(extension, StatisticReader.CONTEXT_SOLUFILE)

    def getNReaders(self):
        """
        returns the number of readers
        """
        return len(self.countManageables())

    def hasReader(self, reader):
        """
        Returns True if given reader is being managed at the moment
        """
        listofnames = [installedreader.getName() for installedreader in self.getManageables()]
        if reader.getName() in listofnames:
            return True
        else:
            return False

    def registerReader(self, reader):
        """
        Registration and activation of a reader
        """
        self.addAndActivate(reader)

    def registerListOfReaders(self, readers):
        """
        Registration of custom readers
        """
        for reader in readers:
            self.addAndActivate(reader)

    def registerDefaultReaders(self):
        """
        Registration of all default readers
        """
        self.registerListOfReaders([
             BestSolInfeasibleReader(),
             DateTimeReader(),
             DualBoundHistoryReader(),
             ErrorFileReader(),
             ParascipDualBoundHistoryReader(),
             GapReader(),
             MaxDepthReader(),
             NodesReader(),
             ObjsenseReader(),
             PluginStatisticsReader(),
             PrimalBoundHistoryReader(),
             VariableReader(),
             RootNodeFixingsReader(),
             SettingsFileReader(),
             SoluFileReader(),
             TimeLimitReader(),
             TimeToFirstReader(),
             TimeToBestReader(),
             TraceFileReader()
             ])

    def updateLineNumberData(self, linenumber, currentcontext, prefix):
        """
        Saves the information about in what lines to find relevant information 
        """
        context2string = {StatisticReader.CONTEXT_LOGFILE:"LogFile",
                          StatisticReader.CONTEXT_ERRFILE:"ErrFile"}
        contextstring = context2string.get(currentcontext)
        if contextstring is None:
            return
        self.testrun.addData("%s%s" % (prefix, contextstring), linenumber)

    def getProblemName(self, line):
        """
        tries to return name of problem, which is read via the line that is beginning with @1
        """
        
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
        """
        only for error and logfiles: the lineinformation is written and the datacollection 
        is being finalized, active solver is being reset
        """
        if filecontext in [StatisticReader.CONTEXT_ERRFILE, StatisticReader.CONTEXT_LOGFILE] and not self.testrun.emptyCurrentProblemData():
            self.updateLineNumberData(line[0], filecontext, "LineNumbers_End")
            for reader in readers:
                reader.execEndOfProb()

            if filecontext == StatisticReader.CONTEXT_LOGFILE and not self.endOfProblemReached(line[1]):
                logging.warning("Malformatted log output, probably a missing expression %s" % \
                               (self.problemendexpression))
            self.testrun.finalizeCurrentCollection(self.activeSolver)
            self.activeSolver.reset()

    def updateProblemName(self, line, currentcontext, readers):
        """
        sets up data structures for a new problem if necessary
        """
        problemname = self.getProblemName(line[1])

        self.testrun.addData(Key.ProblemName, problemname)
        # FARIDO what do we do here if we are reading from stdin?
        # self.testrun.addData('Settings', self.testrun.getSettings())
        self.updateLineNumberData(line[0], currentcontext, "LineNumbers_Begin")

    def endOfProblemReached(self, line):
        """
        Returns a boolean which is True is the line implies the end of the current problem
        """
        return line.startswith(self.problemendexpression)

    def startOfProblemReached(self, line):
        """
        Returns a boolean which is True is the line implies the start of a new problem
        """
        return line.startswith(self.problemexpression)

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
                if solver.recognizeOutput(line):
                    self.activeSolver = solver
                    return lines
        #raise ValueError("Input does not have a recognized format.")

    def sortingKeyContext(self, context):
        """
        returns sortkey belonging to context
        """
        try:
            return self.context2Sortkey[context]
        except IndexError:
            raise IndexError("Unknown context %d" % context)

    def filenameGetContext(self, filename):
        """
        get filecontext via fileextension
        """
        extension = os.path.splitext(os.path.basename(filename))[1]
        return self.fileextension2context[extension]

    def collectData(self):
        """
        runs data collection on the specified test run
        """
        assert(self.testrun != None)

        # sort the files by context, for example: outfiles should be read before solufiles
        if not self.testrun.readsFromStdin():
            self.filestrings = sorted(self.filestrings, key=lambda x:self.sortingKeyContext(self.filenameGetContext(x)))

        for filename in self.filestrings:
            f = None
            if self.testrun.readsFromStdin():
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
            if not self.testrun.readsFromStdin():
                filecontext = self.filenameGetContext(filename)
                self.solverCanRead = self.activeSolver.isSolverInstance(filecontext)
            readers = [r for r in self.getManageables(True) if r.supportsContext(filecontext)]
            
            
            # we enumerate the file so that line is a tuple (idx, line) that contains the line content and its number
            line = (0, "")
            startindex = 0
            # FARIDO How to do this better?
            # search the file for information about the type of the solver
            if self.testrun.readsFromStdin() and self.solverCanRead:
                # since we can read the lines from stdin only once, we have to save them
                try:
                    consumedlines = self.readSolverTypeDirectly(f)
                except ValueError as e:
                    print(e.msg())
                    continue
                for line in enumerate(consumedlines):
                    if self.startOfProblemReached(line[1]):
                        self.updateProblemName(line, filecontext, readers)
                        
                    if self.endOfProblemReached(line[1]):
                        self.finishProblemParsing(line, filecontext, readers)
                            
                    else:
                        self.activeSolver.readLine(line[1])
                        for reader in readers:
                            reader.operateOnLine(line[1])
                startindex = len(consumedlines)
            elif self.solverCanRead:
                self.readSolverType(filename)
                
            for line in enumerate(f, startindex):
                if self.startOfProblemReached(line[1]):
                    self.updateProblemName(line, filecontext, readers)
                
                if self.endOfProblemReached(line[1]):
                    self.finishProblemParsing(line, filecontext, readers)
                        
                else:
                    if self.solverCanRead:
                        self.activeSolver.readLine(line[1])
                    for reader in readers:
                        reader.operateOnLine(line[1])
            
            self.finishProblemParsing(line, filecontext, readers)
            
            if not self.testrun.readsFromStdin():
                f.close()
            self.testrun.finishedReadingFile(self.activeSolver)
        return 1
    
    # ## XML IO methods
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
        if elem.tag == ReaderManager.getNodeTag():
            rm = ReaderManager()
        for child in elem:
            reader = ReaderManager.xmlfactorydict[child.tag](**child.attrib)
            rm.registerReader(reader)
        return rm

