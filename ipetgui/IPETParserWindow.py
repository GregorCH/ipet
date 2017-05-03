"""
The MIT License (MIT)

Copyright (c) 2016 Zuse Institute Berlin, www.zib.de

Permissions are granted as stated in the license file you have obtained
with this software. If you find the library useful for your purpose,
please refer to README.md for how to cite IPET.

@author: Gregor Hendel
"""
from .IpetMainWindow import IpetMainWindow
from PyQt4.QtGui import QLayout, QHBoxLayout
from PyQt4.Qt import QVBoxLayout, QWidget, QFrame, QTextEdit, QApplication, QFileDialog, QKeySequence, QTextBrowser, QComboBox, \
    QLabel, SIGNAL, QTextCursor
from .IPetTreeView import IpetTreeView
import sys
from .EditableBrowser import EditableBrowser
from .IPETApplicationTab import IPETApplicationTab
from ipet.parsing import ReaderManager
from ipet import misc
from ipet.parsing import CustomReader
from ipet.parsing import ListReader
from ipet.parsing import StatisticReader
from .EditableForm import OptionsComboBox
from . import ExperimentManagement

class IPETLogFileView(QWidget):
    StyleSheet = """
        QComboBox { color: darkblue; }
        QTextEdit { font-family : monospace;
                    font-size : 12px; }
        """


    """
    a view of a log file, with selection mechanisms for the desired test run and problem that should be shown
    """
    def __init__(self, parent = None):
        super(IPETLogFileView, self).__init__(parent)
        vlayout = QVBoxLayout(self)
        self.textbrowser = QTextEdit(self)
        self.textbrowser.setReadOnly(True)
        self.testrunselection = OptionsComboBox(self)
        self.problemselection = OptionsComboBox(self)
        vlayout.addWidget(self.textbrowser)
        self.setStyleSheet(self.StyleSheet)
        hlayout = QHBoxLayout()
        testrunselectionlabel = QLabel("Select a test run", self)
        problemselectionlabel = QLabel("Select an instance", self)
        testrunselectionlabel.setBuddy(self.testrunselection)
        problemselectionlabel.setBuddy(self.problemselection)
        for l,s in [(testrunselectionlabel, self.testrunselection),
                    (problemselectionlabel, self.problemselection)]:
            v = QVBoxLayout(self)
            v.addWidget(l)
            v.addWidget(s)
            hlayout.addLayout(v)
        vlayout.addLayout(hlayout)
        self.setLayout(vlayout)
        
        self.initConnections()

    def getProblem(self):
        problem = self.problemselection.currentText()
        return problem
    
    def getSelectedText(self):
        return self.textbrowser.textCursor().selection()
    
    def getLineSelectionIndex(self):
        c = self.textbrowser.textCursor()
        if c.anchor() < c.position():
            # normal left to right selection
            return (c.positionInBlock() - (c.selectionEnd() - c.selectionStart()) , 
                    c.positionInBlock())
        else:
            return (c.positionInBlock(), 
                    c.positionInBlock() + (c.selectionEnd() - c.selectionStart()))
    
    def getSelectedLine(self):
        cursor = self.textbrowser.textCursor()
        cursor.select(QTextCursor.LineUnderCursor)
        return str(cursor.selectedText())
    

    def getTestRun(self):
        testruntext = self.testrunselection.currentText()
        for t in ExperimentManagement.getExperiment().getTestRuns():
            if t.getName() == testruntext:
                return t
        return None
        
    def initConnections(self):
        for s in (self.testrunselection, self.problemselection):
            self.connect(s, SIGNAL("currentIndexChanged(int)"), self.updateView)
        
    def updateExperimentData(self):
        self.testrunselection.clear()
        self.problemselection.clear()
        
        testruns = ExperimentManagement.getExperiment().getTestRuns()
        problems = ExperimentManagement.getExperiment().getProblemIds()

        self.testrunselection.addItems([t.getName() for t in testruns])
        self.problemselection.addItems([p for p in problems])

    def updateView(self):
        selectedtestrun = self.getTestRun()
        selectedproblem = self.getProblem()
        if selectedtestrun is None:
            return
        outfile = selectedtestrun.getLogFile()

        with open(outfile, 'r') as in_file:
            linesstart = selectedtestrun.getProblemDataById(str(selectedproblem), "LineNumbers_BeginLogFile")
            linesend = selectedtestrun.getProblemDataById(str(selectedproblem), "LineNumbers_EndLogFile")
            self.text = []
            for idx, line in enumerate(in_file):
                if idx > linesend:
                    break
                elif idx >= linesstart:
                    self.text.append(line)
            self.text = "".join(self.text)
            self.textbrowser.setText(self.text)
            self.textbrowser.update()

class IPETParserWindow(IPETApplicationTab):

    naddedreaders = 0
    def __init__(self, parent = None):
        super(IPETApplicationTab, self).__init__(parent)

        vlayout = QVBoxLayout()
        self.editablebrowser = EditableBrowser()
        vlayout.addWidget(self.editablebrowser)
        self.logfileview = IPETLogFileView(self)
        vlayout.addWidget(self.logfileview)

        self.setLayout(vlayout)
        self.parser = None
        self.filename = None
        self.defineActions()
        
        self.setParser(ExperimentManagement.getExperiment().getReaderManager())
        
        self.logfileview.updateExperimentData()

    def setParser(self, parser):
        self.editablebrowser.setRootElement(parser)
        self.parser = parser

    def defineActions(self):
        self.loadaction = self.createAction("&Load parser", self.loadParser, None, icon = "Load-icon",
                                       tip = "Load parser from XML file (current parser gets discarded)")
        self.saveaction = self.createAction("Save parser", self.saveParser, None, icon = "disk-icon",
                                        tip = "Save parser to a file")
        self.saveasaction = self.createAction("Save parser as", self.saveParserAs, None, icon = "disk-icon",
                                        tip = "Save parser to a file of a specified name")

        self.addcustomreaderaction = self.createAction("Add Custom Reader", self.addCustomReader, None, icon = "3d-glasses-icon",
                                                       tip = "Add a custom reader to the parser")
        self.addlistreaderaction = self.createAction("Add List Reader", self.addListReader, "Alt+L", icon = "list-icon",
                                                      tip = "Add a list reader to this parser")

        self.deleteaction = self.createAction("Delete reader", self.editablebrowser.deleteElement, QKeySequence.Delete, "delete-icon",
                                              tip = "Delete selected reader ")
        self.recollectdataaction = self.createAction("Parse experimental Data", self.recollectData, QKeySequence.Refresh, "Refresh-icon",
                                                     tip = "Parse experimental data")
        
        self.loadlogfilesaction = self.createAction("&Load Output Files", self.loadOutputFiles, QKeySequence.Open, icon="Load-icon",
                                       tip="Load log files for the different contexts, or readily parsed test runs")
        
    def loadOutputFiles(self):
        thedir = str(".")
        filenames = QFileDialog.getOpenFileNames(self, caption = "%s - Load Output Files" % QApplication.applicationName(),
                                               directory=thedir, filter=str("All files (*.out)"))
        if filenames:
            loadedtrs = 0
            notloadedtrs = 0
            for filename in filenames:
                try:
                    ExperimentManagement.getExperiment().addOutputFile(str(filename))
                    
                    loadedtrs += 1
                except Exception as e:
                    self.updateStatus(e)
                    notloadedtrs += 1

            message = "Loaded %d/%d output files"%(loadedtrs, loadedtrs + notloadedtrs)
            self.logfileview.updateExperimentData()
            self.updateStatus(message)


    def recollectData(self):
        ExperimentManagement.addReaders(self.parser)
        ExperimentManagement.getExperiment().collectData()
        self.logfileview.updateExperimentData()
        self.updateStatus("Data collection finished")

    def getMenuActions(self):
        return (("&File", [self.loadaction, self.saveaction, self.saveasaction]),
                ("&Readers", [self.addcustomreaderaction, self.addlistreaderaction, self.deleteaction]),
                ("Experiment", [self.loadlogfilesaction, self.recollectdataaction]))

    def getToolBarActions(self):
        return (("&File", [self.loadaction, self.saveaction, self.recollectdataaction]), ("&Readers", [self.addcustomreaderaction, self.addlistreaderaction, self.deleteaction]))

    def loadParser(self):
        thedir = str(".")
        filename = str(QFileDialog.getOpenFileName(self, caption = "%s - Load a parser" % QApplication.applicationName(),
                                               directory = thedir, filter = str("XML files (*.xml)")))
        if filename:
            try:
                parser = ReaderManager.fromXMLFile(filename)
                message = "Loaded parser from %s" % filename
                self.setParser(parser)
            except Exception:
                message = "Error: Could not load parser from file %s" % filename

            self.updateStatus(message)
            
    def getTextSelectionHint(self):
        selectedline = self.logfileview.getSelectedLine()
        indices = self.logfileview.getLineSelectionIndex()
        startofline = selectedline[:indices[0]]
        lineincludingselection = selectedline[:indices[1]]
        
        ne = StatisticReader.numericExpression
        nhitsstartofline = len(ne.findall(startofline))
        nhitslineincludingselection = len(ne.findall(lineincludingselection))
        
        # the first word in the line is the text hint for the data key
        datakeytexthint = ne.split(lineincludingselection, 1)[0]
        return (datakeytexthint, nhitsstartofline, nhitslineincludingselection)

    def addCustomReader(self):
        oldnaddedreaders = self.naddedreaders
        hint, a, b = self.getTextSelectionHint()
        
        if a == b:
            self.naddedreaders += 1
            reader = CustomReader("New Custom Reader %d" % self.naddedreaders, "regpattern", "datakey")
            self.editablebrowser.addNewElementAsChildOfRootElement(reader)
            self.updateStatus("Line selection does not contain numeric, parsable information, added 1 reader")
            return
        
        # prepare the base data key from the hint    
        hint = hint.rstrip(" :")
        datakeytexthint = "".join(hint.split())        
        for specialchar in ".<>#():+/":
            datakeytexthint = datakeytexthint.replace(specialchar, '')
            
        # add data key for all selected numbers from this line
        for i in range(a,b):
            datakey = datakeytexthint + str(i)
            regpattern = hint
            readername = None
            reader = CustomReader(readername, regpattern=regpattern, datakey=datakey, index=i)
            try:
                self.editablebrowser.addNewElementAsChildOfRootElement(reader)
                self.naddedreaders += 1
            except KeyError:
                pass
        
        self.updateStatus("Added %d/%d readers for selected line" % (self.naddedreaders - oldnaddedreaders, b - a))
        
    def addListReader(self):
        self.naddedreaders += 1
        reader = ListReader("cleverRegpattern", name = "new List Reader %d" % self.naddedreaders)
        self.editablebrowser.addNewElementAsChildOfRootElement(reader)


    def saveParser(self):
        if self.filename is None:
            filename = str(QFileDialog.getSaveFileName(self, caption = "%s - Save a parser" % QApplication.applicationName(),
                                                           directory = str("."), filter = str("XML files (*.xml)")))
        else:
            filename = self.filename

        if not filename:
            return


        misc.saveAsXML(self.parser, filename)
        self.filename = filename
        self.updateStatus("Saved parser to file %s" % filename)


    def saveParserAs(self):
        filename = str(QFileDialog.getSaveFileName(self, caption = "%s - Save a parser" % QApplication.applicationName(),
                                                       directory = str("."), filter = str("XML files (*.xml)")))
        if not filename:
            return

        misc.saveAsXML(self.parser, filename)
        self.filename = filename
        self.updateStatus("Saved parser to file %s" % filename)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    imw = IpetMainWindow()
    imw.setWindowTitle("Parser Window")

    app.setApplicationName("Parser Window")

    readermanager = ReaderManager.fromXMLFile("../scripts/readers-example.xml")
    ExperimentManagement.addOutputFiles(['../test/check.short.scip-3.1.0.1.linux.x86_64.gnu.dbg.spx.opt85.testmode.out'])
    ExperimentManagement.getExperiment().collectData()
    parserwindow = IPETParserWindow()
    parserwindow.setParser(readermanager)
    imw.setCentralWidget(parserwindow)
    imw.populateMenu(parserwindow)
    imw.populateToolBar(parserwindow)

    imw.show()

    sys.exit(app.exec_())
