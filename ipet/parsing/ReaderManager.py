"""
The MIT License (MIT)

Copyright (c) 2018 Zuse Institute Berlin, www.zib.de

Permissions are granted as stated in the license file you have obtained
with this software. If you find the library useful for your purpose,
please refer to README.md for how to cite IPET.

@author: Gregor Hendel
"""
import os
import logging
import xml.etree.ElementTree as ElementTree
from .StatisticReader import ErrorFileReader, GapReader, TimeLimitReader, ListReader, \
    BestSolInfeasibleReader, MaxDepthReader, MetaDataReader, NodeNameReader, NodesReader, RootNodeFixingsReader, \
    SettingsFileReader, TimeToFirstReader, TimeToBestReader, ObjsenseReader, DateTimeReader, SolCheckerReader
from .StatisticReader_TableReader import TableReader, CustomTableReader
from .StatisticReader_VariableReader import VariableReader
from .StatisticReader_CustomReader import CustomReader
from .TraceFileReader import TraceFileReader
from ipet.concepts.Manager import Manager
from ipet.concepts.IPETNode import IpetNode
from ipet.parsing.Solver import SCIPSolver, CbcSolver, XpressSolver, GurobiSolver, \
    CplexSolver, FiberSCIPSolver, MatlabSolver, MosekSolver, MipclSolver, NuoptSolver, SasSolver
from ipet.misc import misc
# CbcSolver, CouenneSolver, \
#     XpressSolver, GurobiSolver, CplexSolver
from ipet import Key
from ipet.IPETError import IPETInconsistencyError
from ipet.Key import CONTEXT_ERRFILE, CONTEXT_LOGFILE

logger = logging.getLogger(__name__)

class ReaderManager(Manager, IpetNode):
    """
    acquires test run data. subclasses of manager, managing readers by their unique name
    """
    nodetag = "Readers"

    xmlfactorydict = {"ListReader":ListReader, "CustomReader":CustomReader, "CustomTableReader":CustomTableReader}

    context2string = {Key.CONTEXT_LOGFILE:"LogFile",
                      Key.CONTEXT_ERRFILE:"ErrFile"}

    def __init__(self, problemexpression = "@01", problemendexpression = "=ready="):
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
        self.solvers = []
        self.addSolvers()
        self.activeSolver = self.solvers[0]
        self.solverCanRead = True

    def getEditableAttributes(self):
        return ["problemexpression", "problemendexpression"]

    def addSolvers(self):
        for s in [SCIPSolver(),
                  CbcSolver(),
                  XpressSolver(),
                  GurobiSolver(),
                  CplexSolver(),
                  FiberSCIPSolver(),
                  MatlabSolver(),
                  MosekSolver(),
                  MipclSolver(),
                  NuoptSolver(),
                  SasSolver()
                  ]:
            self.addSolver(s)

    def addSolver(self, solver):
        self.solvers.append(solver)
        logger.debug("Added a solver: {}".format(solver.getName()))

    def getName(self):
        """
        Returns the name of the class
        """
        return "ReaderManager"

    def isActive(self) -> bool:
        """Return if this reader manager is active or not
        """
        return IpetNode.isActive(self)

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
        return sorted(children, key = lambda x:x.getName())

    def setTestRun(self, testrun):
        """
        changes the testrun for reading to the new testrun
        """
        logger.debug("Setting testrun to %s" % testrun.getName())
        self.testrun = testrun
        for reader in self.getManageables():
            reader.setTestRun(testrun)

    def addFileExtension2Context(self, extension, context):
        """
        Adds a new file context (associated to extension)
        """
        oldcontext = Key.fileextension2context.get(extension)
        # don't overwrite existing content
        if  oldcontext is not None and oldcontext != context:
            raise ValueError("context for file extension %s already set to %d" % (extension, oldcontext))
        Key.fileextension2context[extension] = context

    def getFileExtensions(self):
        """
        returns a list of all recognized file extensions by this Reader manager
        """
        return list(Key.fileextension2context.keys())
#
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
             ErrorFileReader(),
             GapReader(),
             MaxDepthReader(),
             MetaDataReader(),
             NodeNameReader(),
             NodesReader(),
             ObjsenseReader(),
             TableReader(),
             VariableReader(),
             RootNodeFixingsReader(),
             SettingsFileReader(),
             SolCheckerReader(),
             TimeLimitReader(),
             TimeToFirstReader(),
             TimeToBestReader(),
             TraceFileReader()
             ])

    def updateLineNumberData(self, linenumber, currentcontext, prefix):
        """
        Saves the information about in what lines to find relevant information
        """
        contextstring = self.context2string.get(currentcontext)
        if contextstring is None:
            return
        self.testrun.addData("%s%s" % (prefix, contextstring), linenumber)

    def getProblemName(self, line):
        """
        Returns name of problem, which is read from a line beginning with a problemexpression (@01)
        """

        fullpath = line.split()[1]
        namewithextension = os.path.basename(fullpath)
        if namewithextension.endswith("gz"):
            namewithextension = os.path.splitext(namewithextension)[0]
        namewithoutextension = os.path.splitext(namewithextension)[0]

        # now name without extension
        return namewithoutextension, fullpath

    def finishProblemParsing(self, line, filecontext, readers):
        """
        only for error and logfiles: the lineinformation is written and the datacollection
        is being finalized, active solver is being reset
        """
        if filecontext in [Key.CONTEXT_ERRFILE, Key.CONTEXT_LOGFILE] and not self.testrun.emptyCurrentProblemData():
            self.updateLineNumberData(line[0], filecontext, "LineNumbers_End")
            for reader in readers:
                reader.execEndOfProb()

            self.testrun.finalizeCurrentCollection(self.activeSolver, filecontext)
            self.activeSolver.reset()

    def updateProblemName(self, line, currentcontext, readers):
        """
        sets up data structures for a new problem if necessary
        """
        self.updateLineNumberData(line[0], currentcontext, "LineNumbers_Begin")

        problemname, problempath = self.getProblemName(line[1])
        oldname = self.testrun.getProblemDataById(self.testrun.currentproblemid, Key.ProblemName)
        # if oldname is not None then the .out file was already parsed
        # and we are currently parsing the .err file. Check if the problemname
        # is contained in the line.
        if (oldname is not None) and ("_{}.".format(oldname) not in line[1]) and not (oldname == problemname):
            raise IPETInconsistencyError("Inconsistency in order of instances in .out and .err file: {} does not correspond to {}.".format(problemname, oldname))

        self.testrun.addData(Key.ProblemName, problemname)
        self.testrun.addData(Key.LogFileName, self.testrun.getCurrentLogfilename())
        self.testrun.addData(Key.Path, problempath)

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
#
    def readSolverType(self):
        """
        check the solver type for a given log file
        """
        lines = []
        for i, line in self.testrun:
            lines.append(line)
            for solver in self.solvers:
                if solver.recognizeOutput(line):
                    self.activeSolver = solver
                    self.testrun.iterationAddConsumedStdinput(lines)
                    return
        # raise ValueError("Input does not have a recognized format.")

    def collectData(self):
        """
        runs data collection on the specified testrun
        """
        assert(self.testrun != None)

        self.testrun.iterationPrepare()
        while self.testrun.iterationNextFile():
            self.readSolverType()

            context = misc.filenameGetContext(self.testrun.iterationGetCurrentFile())
            readers = [r for r in self.getManageables(True) if r.supportsContext(context)]

            line = (0, "")
            for line in self.testrun:
                if self.startOfProblemReached(line[1]):
                    if context in [CONTEXT_ERRFILE, CONTEXT_LOGFILE]:
                        # .errfiles do not contain problemdexpression ==ready==
                        self.finishProblemParsing(line, context, readers)

                    try:
                        self.updateProblemName(line, context, readers)
                    except IPETInconsistencyError as e:
                        logger.warning(e.msg)
                        if context == CONTEXT_ERRFILE:
                            logger.warning("Skipping parsing of the rest of the .err file.")
                            break

                if self.endOfProblemReached(line[1]):
                    self.finishProblemParsing(line, context, readers)
                else:
                    if context == CONTEXT_LOGFILE:
                        self.activeSolver.readLine(line[1])
                    for reader in readers:
                        reader.operateOnLine(line[1])

            # in case solver crashed, make sure that parsing is finished
            self.finishProblemParsing(line, context, readers)
            self.testrun.finishedReadingFile(self.activeSolver, context = context)

        self.testrun.iterationCleanUp()
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
    def getNodeTag():
        """
        returns the name of the Readermanager
        """
        return ReaderManager.nodetag

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

