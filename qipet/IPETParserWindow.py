'''
Created on 21.09.2016

@author: bzfhende
'''
from IpetMainWindow import IpetMainWindow
from PyQt4.QtGui import QLayout, QHBoxLayout
from PyQt4.Qt import QVBoxLayout, QWidget, QFrame, QTextEdit, QApplication, QFileDialog, QString, QKeySequence, QTextBrowser, QComboBox
from IPetTreeView import IpetTreeView
import sys
from qipet.EditableBrowser import EditableBrowser
from IPETApplicationTab import IPETApplicationTab
from ipet.parsing import ReaderManager
from ipet import misc
from ipet.parsing.StatisticReader_CustomReader import CustomReader
from ipet.parsing.StatisticReader import ListReader
from EditableForm import OptionsComboBox
import ExperimentManagement

class IPETLogFileView(QWidget):
    '''
    a view of a log file, with selection mechanisms for the desired test run and instance that should be shown
    '''
    def __init__(self, parent = None):
        super(IPETLogFileView, self).__init__(parent)
        vlayout = QVBoxLayout(self)
        self.textbrowser = QTextBrowser(self)
        self.testrunselection = OptionsComboBox(self)
        self.instanceselection = OptionsComboBox(self)
        vlayout.addWidget(self.textbrowser)
        hlayout = QHBoxLayout()
        hlayout.addWidget(self.testrunselection)
        hlayout.addWidget(self.instanceselection)
        vlayout.addLayout(hlayout)
        self.setLayout(vlayout)

    def getProblem(self):
        problem = self.instanceselection.currentText()
        return problem

    def getTestRun(self):
        testrun = self.testrunselection.currentText()



    def updateSelection(self):
        self.testrunselection.clear()
        self.instanceselection.clear()
        
        testruns = ExperimentManagement.getExperiment().getTestruns()
        problems = ExperimentManagement.getExperiment().getProblems()





class IPETParserWindow(IPETApplicationTab):

    naddedreaders = 0
    def __init__(self, parent = None):
        super(IPETApplicationTab, self).__init__(parent)

        vlayout = QVBoxLayout()
        self.editablebrowser = EditableBrowser()
        vlayout.addWidget(self.editablebrowser)
        vlayout.addWidget(IPETLogFileView(self))

        self.setLayout(vlayout)
        self.parser = None
        self.filename = None
        self.defineActions()

    def setParser(self, parser):
        self.editablebrowser.setRootElement(parser)
        self.parser = parser

    def defineActions(self):
        self.loadaction = self.createAction("&Load parser", self.loadParser, None, icon = "Load-icon",
                                       tip = "Load parser from XML file (current parser gets discarded)")
        self.saveaction = self.createAction("Save parser", self.saveParser, None, icon = "disk-icon",
                                        tip = "Save parser to a file")
        self.saveasaction = self.createAction("Save parser", self.saveParserAs, None, icon = "disk-icon",
                                        tip = "Save parser to a file of a specified name")

        self.addcustomreaderaction = self.createAction("Add Custom Reader", self.addCustomReader, None, icon = "3d-glasses-icon",
                                                       tip = "Add a custom reader to the parser")
        self.addlistreaderaction = self.createAction("Add List Reader", self.addListReader, "Alt+L", icon = "list-icon",
                                                      tip = "Add a list reader to this parser")

        self.deleteaction = self.createAction("Delete reader", self.editablebrowser.deleteElement, QKeySequence.Delete, "delete-Icon",
                                              tip = "Delete selected reader ")
        self.recollectdataaction = self.createAction("Recollect Data", self.recollectData, QKeySequence.Refresh, "Refresh-icon",
                                                     tip = "Recollect data with specified readers")


    def recollectData(self):
        self.updateStatus("This action is not yet supported")
        pass
    def getMenuActions(self):
        return (("&File", [self.loadaction, self.saveaction, self.saveasaction, self.recollectdataaction]), ("&Readers", [self.addcustomreaderaction, self.addlistreaderaction, self.deleteaction]))

    def getToolBarActions(self):
        return (("&File", [self.loadaction, self.saveaction, self.recollectdataaction]), ("&Readers", [self.addcustomreaderaction, self.addlistreaderaction, self.deleteaction]))

    def loadParser(self):
        thedir = unicode(".")
        filename = unicode(QFileDialog.getOpenFileName(self, caption = QString("%s - Load a parser" % QApplication.applicationName()),
                                               directory = thedir, filter = unicode("XML files (*.xml)")))
        if filename:
            try:
                parser = ReaderManager.fromXMLFile(filename)
                message = "Loaded parser from %s" % filename
                self.setParser(parser)
            except Exception:
                message = "Error: Could not load parser from file %s" % filename

            self.updateStatus(message)

    def addCustomReader(self):
        self.naddedreaders += 1
        reader = CustomReader("New Custom Reader %d" % self.naddedreaders, "regpattern", "datakey")
        self.editablebrowser.addNewElementAsChildOfSelectedElement(reader)

    def addListReader(self):
        self.naddedreaders += 1
        reader = ListReader("cleverRegpattern", name = "new List Reader %d" % self.naddedreaders)
        self.editablebrowser.addNewElementAsChildOfSelectedElement(reader)


    def saveParser(self):
        if self.filename is None:
            filename = unicode(QFileDialog.getSaveFileName(self, caption = QString("%s - Save a parser" % QApplication.applicationName()),
                                                           directory = unicode("."), filter = unicode("XML files (*.xml)")))
        else:
            filename = self.filename

        if not filename:
            return


        misc.saveAsXML(self.parser, filename)
        self.filename = filename
        self.updateStatus("Saved parser to file %s" % filename)


    def saveParserAs(self):
        filename = unicode(QFileDialog.getSaveFileName(self, caption = QString("%s - Save a parser" % QApplication.applicationName()),
                                                       directory = unicode("."), filter = unicode("XML files (*.xml)")))
        if not filename:
            return

        misc.saveAsXML(self.parser, filename)
        self.filename = filename
        self.updateStatus("Saved parser to file %s" % filename)
#
#     def enableOrDisableActions(self):
#         for action, addclass in zip([self.addcolaction, self.addfiltergroupaction, self.addfilteraction, self.addaggregationaction, self.addinstancenaction],
#                                     [IPETEvaluationColumn(), IPETFilterGroup(), IPETFilter(), Aggregation(), IPETInstance()]):
#             if self.browser.treewidget.currentItemAcceptsClassAsChild(addclass):
#                 action.setEnabled(True)
#             else:
#                 action.setEnabled(False)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    imw = IpetMainWindow()
    imw.setWindowTitle("Parser Window")

    app.setApplicationName("Evaluation editor")

    readermanager = ReaderManager.fromXMLFile("../scripts/readers-example.xml")

    parserwindow = IPETParserWindow()
    parserwindow.setParser(readermanager)
    imw.setCentralWidget(parserwindow)
    imw.populateMenu(parserwindow)
    imw.populateToolBar(parserwindow)

    imw.show()

    sys.exit(app.exec_())
