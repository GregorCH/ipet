from StatisticReader import StatisticReader, ListReader
from StatisticReader_CustomReader import CustomReader
import os
import re
from Manager import Manager
from ipet.IPETMessageStream import Message
import xml.etree.ElementTree as ElementTree

class ReaderManager(Manager):
    '''
    acquires test run data. subclasses of manager, managing readers by their unique name
    '''
    problemexpression = re.compile(r'^@01')
    extensions = [".mps", ".cip", ".fzn", ".pip", ".lp"]
    INSTANCE_END_EXPRESSION = re.compile('^=ready=')

    solvertype_recognition = {StatisticReader.SOLVERTYPE_SCIP:"SCIP version ",
                              StatisticReader.SOLVERTYPE_GUROBI:"Gurobi Optimizer version",
                              StatisticReader.SOLVERTYPE_CPLEX:"Welcome to IBM(R) ILOG(R) CPLEX(R) Interactive Optimizer",
                              StatisticReader.SOLVERTYPE_XPRESS:"FICO Xpress Optimizer",
                              StatisticReader.SOLVERTYPE_CBC:"Welcome to the CBC MILP Solver",
                              StatisticReader.SOLVERTYPE_COUENNE:" Couenne  --  an Open-Source solver for Mixed Integer Nonlinear Optimization"
                              }


    othersolvers = [solver for solver in solvertype_recognition.keys() if solver != StatisticReader.solvertype]


    xmlfactorydict = {"ListReader":ListReader, "CustomReader":CustomReader}

    def setTestRun(self, testrun):
        self.testrun = testrun
        self.filestrings = testrun.filenames
        for reader in self.getManageables():
            reader.setTestRun(testrun)

    def getNReaders(self):
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

    def updateProblemName(self, line):

        if self.problemexpression.match(line):
            fullname = line.split()[1]
            namewithextension = os.path.basename(fullname);
            namewithextension = os.path.splitext(namewithextension)[0]
            for extension in self.extensions:
                namewithextension = namewithextension.split(extension)[0]
            StatisticReader.setProblemName(namewithextension)
            if namewithextension in self.testrun.getProblems():
                self.testrun.deleteProblemData(namewithextension)
            self.testrun.addData(namewithextension, 'Settings', self.testrun.getSettings())

    def endOfInstanceReached(self, line):
        if ReaderManager.INSTANCE_END_EXPRESSION.match(line):
            return True
        else:
            return False

    def checkSolverType(self, line):
        changed = False
        for key in ReaderManager.othersolvers:
            if line.startswith(ReaderManager.solvertype_recognition[key]):
                changed = True
                StatisticReader.changeSolverType(key)
                ReaderManager.othersolvers = [solver for solver in ReaderManager.solvertype_recognition.keys() if solver != StatisticReader.solvertype]
                break
        if changed:
            print "changed solver type to", StatisticReader.solvertype

    def collectData(self):
        assert(self.testrun != None)
        readers = self.getManageables(True)

        for filestring in self.filestrings:
            f = None
            try:
                f = open(filestring, 'r')
            except IOError:
                print 'File', filestring, "doesn't exist!"
                continue


            for line in f:
                self.updateProblemName(line)
                self.checkSolverType(line)
                if self.endOfInstanceReached(line):
                    for reader in readers:
                        reader.execEndOfProb()
                    else:
                        self.notify(Message("%s" % StatisticReader.problemname, Message.MESSAGETYPE_INFO))
                else:
                    for reader in readers:
                        reader.extractStatistic(line)


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


if __name__ == "__main__":
    #rm = ReaderManager()
    #rm.registerReader(ListReader("[nf]Genios_\w*"))
    #rm.registerReader(CustomReader(name="Me", activateexpression="@01", regpattern="SolvingTime", datakey="MyStime"))
    #el = rm.toXMLElem()
    #from xml.dom.minidom import parseString
    #dom = parseString(ElementTree.tostring(el))
    #with open("myfile.xml", 'w') as myfile:
        #myfile.write(dom.toprettyxml())

    rm2 = ReaderManager.fromXMLFile("/nfs/optimi/kombadon/bzfhende/projects/sap-data/phase_2/DLScip/check/sap-readers.xml")
    for r in rm2.getManageables():
        print r.attributesToDict()

