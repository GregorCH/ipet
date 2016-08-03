from StatisticReader import StatisticReader, ListReader
from StatisticReader_CustomReader import CustomReader
import os
import re
from Manager import Manager
from ipet.IPETMessageStream import Message
import xml.etree.ElementTree as ElementTree

class ReaderManager(Manager):
    """
    acquires test run data. subclasses of manager, managing readers by their unique name
    """
    problemexpression = re.compile(r'^@01')
    extensions = [".mps", ".cip", ".fzn", ".pip", ".lp"]
    INSTANCE_END_EXPRESSION = re.compile('^=ready=')

    solvertype_recognition = {
                              StatisticReader.SOLVERTYPE_SCIP:"SCIP version ",
                              StatisticReader.SOLVERTYPE_GUROBI:"Gurobi Optimizer version",
                              StatisticReader.SOLVERTYPE_CPLEX:"Welcome to IBM(R) ILOG(R) CPLEX(R) Interactive Optimizer",
                              StatisticReader.SOLVERTYPE_XPRESS:"FICO Xpress Optimizer",
                              StatisticReader.SOLVERTYPE_CBC:"Welcome to the CBC MILP Solver",
                              StatisticReader.SOLVERTYPE_COUENNE:" Couenne  --  an Open-Source solver for Mixed Integer Nonlinear Optimization"
                              }
    """recognition patterns to distinguish between solver types"""

    othersolvers = [solver for solver in solvertype_recognition.keys() if solver != StatisticReader.solvertype]
    

    fileextension2context = {
                             ".err" : StatisticReader.CONTEXT_ERRFILE,
                             ".out" : StatisticReader.CONTEXT_LOGFILE,
                             ".set" : StatisticReader.CONTEXT_SETFILE,
                             ".solu": StatisticReader.CONTEXT_SOLUFILE
                             }
    """map for file extensions to the file contexts to specify the relevant readers"""

    context2Sortkey = {
                       StatisticReader.CONTEXT_ERRFILE : 2,
                       StatisticReader.CONTEXT_LOGFILE : 1,
                       StatisticReader.CONTEXT_SETFILE : 3,
                       StatisticReader.CONTEXT_SOLUFILE : 4
                       }
    """ defines a sorting order for file contexts """


    xmlfactorydict = {"ListReader":ListReader, "CustomReader":CustomReader}

    def setTestRun(self, testrun):
        """
        changes the testrun for reading to the new testrun
        """
        self.testrun = testrun
        self.filestrings = testrun.filenames
        for reader in self.getManageables():
            reader.setTestRun(testrun)

    def addFileExtension2Context(self, extension, context):
        oldcontext = self.fileextension2context.get(extension)
        if  oldcontext is not None and oldcontext != context:
            raise ValueError("context for file extension %s already set to %d" % (extension, oldcontext))
        self.fileextension2context[extension] = context

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

    def updateLineNumberData(self, linenumber, problemname, currentcontext, prefix):
        context2string = {StatisticReader.CONTEXT_LOGFILE:"LogFile",
                          StatisticReader.CONTEXT_ERRFILE:"ErrFile"}
        if problemname is None:
            return
        contextstring = context2string.get(currentcontext)
        if contextstring is None:
            return
        self.testrun.addData(problemname, "%s%s" % (prefix, contextstring), linenumber)


    def updateProblemName(self, line, currentcontext, readers):
        '''
        sets up data structures for a new problem instance if necessary
        '''

        if self.problemexpression.match(line[1]):
            
            if StatisticReader.getProblemName() is not None:
                for reader in readers:
                    reader.execEndOfProb()
                    
            fullname = line[1].split()[1]
            namewithextension = os.path.basename(fullname);
            namewithextension = os.path.splitext(namewithextension)[0]
            for extension in self.extensions:
                namewithextension = namewithextension.split(extension)[0]
            StatisticReader.setProblemName(namewithextension)


            # overwrite previous output information from a log file
            if namewithextension in self.testrun.getProblems() and currentcontext == StatisticReader.CONTEXT_LOGFILE:
                self.testrun.deleteProblemData(namewithextension)

            self.updateLineNumberData(line[0], StatisticReader.getProblemName(), currentcontext, "LineNumbers_Begin")
            self.testrun.addData(namewithextension, 'Settings', self.testrun.getSettings())

    def endOfInstanceReached(self, line):
        if ReaderManager.INSTANCE_END_EXPRESSION.match(line):
            return True
        else:
            return False

    def readSolverType(self, filename):
        '''
        check the solver type for a given log file
        '''

        with open(filename, "r") as currentfile:
            for line in currentfile:
                for key in ReaderManager.solvertype_recognition.keys():
                    if line.startswith(ReaderManager.solvertype_recognition[key]):
                        StatisticReader.changeSolverType(key)
                        ReaderManager.othersolvers = [solver for solver in ReaderManager.solvertype_recognition.keys() \
                                                      if solver != StatisticReader.solvertype]
                        return

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

        # sort the files by context
        self.filestrings = sorted(self.filestrings, key = lambda x:self.sortingKeyContext(self.filenameGetContext(x)))

        for filename in self.filestrings:
            f = None
            try:
                f = open(filename, 'r')
            except IOError:
                print 'File', filename, "doesn't exist!"
                continue

            # only enable readers that support the file context
            filecontext = self.filenameGetContext(filename)
            readers = [r for r in self.getManageables(True) if r.supportsContext(filecontext)]

            # search the file for information about the type of the solver
            self.readSolverType(filename)

            # reset the problem name before a new problem is read in
            StatisticReader.setProblemName(None)

            # we enumerate the file so that line is a tuple (idx, line) that contains the line content and its number
            for line in enumerate(f):
                self.updateProblemName(line, filecontext, readers)
                if self.endOfInstanceReached(line[1]):
                    self.updateLineNumberData(line[0], StatisticReader.getProblemName(), filecontext, "LineNumbers_End")
                    self.notify(Message("%s" % StatisticReader.problemname, Message.MESSAGETYPE_INFO))
                else:
                    for reader in readers:
                        reader.extractStatistic(line[1])

            else:
                if StatisticReader.getProblemName() is not None:
                    for reader in readers:
                        reader.execEndOfProb()



            f.close()
        # print("Collection of data finished")
        return 1

    ### XML IO methods
    def toXMLElem(self):
        me = ElementTree.Element('Readers')
        readers = self.getManageables(False)
        for reader in readers:
            if reader.__class__ in ReaderManager.xmlfactorydict.values():
                readerattrs = reader.attributesToDict()
                readerstrattrs = {key:str(val) for key, val in readerattrs.iteritems()}
                for key in ReaderManager.xmlfactorydict.keys():
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
        if elem.tag == 'Readers':
            rm = ReaderManager()
        for child in elem:
            reader = ReaderManager.xmlfactorydict[child.tag](**child.attrib)
            rm.registerReader(reader)
        return rm




