'''
Created on 26.03.2015

@author: bzfhende
'''
from PyQt4.QtGui import QMainWindow, QGridLayout, QFrame, QWidget, QLabel,\
    QApplication, QAction, QIcon, QKeySequence, QFileDialog, QLayout,\
    QSizePolicy, QVBoxLayout, QHBoxLayout
from qipet.IPetTreeView import IpetTreeView
from qipet.EditableForm import EditableForm
from PyQt4.QtCore import QString, Qt, SIGNAL
from ipet.IPETEvalTable import IPETEvaluation
import sys
from ipet import Misc

class IpetEvaluationEditorApp(QMainWindow):
    '''
    classdocs
    '''


    def __init__(self, parent=None):
        '''
        Constructor
        '''
        super(IpetEvaluationEditorApp, self).__init__(parent)
        
        self.setGeometry(300, 300, 800, 500)
        self.setWindowTitle("Evaluation Editor")
        thewidget = QWidget(self)
        self.treewidget = IpetTreeView(self)
        layout = QHBoxLayout()
        layout.addWidget(self.treewidget, 3)
        self.editframe = QFrame(thewidget)
        layout.addWidget(self.editframe, 2)

        self.editframelayout = QVBoxLayout()

        self.editframe.setLayout(self.editframelayout)
    
        thewidget.setLayout(layout)
        self.setCentralWidget(thewidget)
        self.evaluation = None
        self.statusBar().showMessage("Ready", 5000)
        self.filename = None
        
        self.initConnections()
        self.defineActions()
        
    def initConnections(self):
        self.connect(self.treewidget, SIGNAL("itemSelectionChanged()"), self.changeSelection)
        
    def setEvaluation(self, evaluation):
        self.evaluation = evaluation
        self.treewidget.populateTree(evaluation)
        self.changeSelection()
        
    def defineActions(self):
        menubar = self.menuBar()
        filemenu = menubar.addMenu("&File")
        
        filetoolbar = self.addToolBar("File")
        
        loadaction = self.createAction("&Load", self.loadEvaluation, QKeySequence.Open, icon="Load-icon", 
                                       tip="Load evaluation from XML file (current evaluation gets discarded)")
        saveaction = self.createAction("&Save", self.saveEvaluation, QKeySequence.Save, icon="disk-icon", 
                                       tip="Save evaluation to XML format")
        saveasaction = self.createAction("&Save as", self.saveEvaluationAs, QKeySequence.SaveAs, icon="disk-icon", 
                                       tip="Save evaluation to XML format")
        addcolaction = self.createAction("Add &Column", self.addColumn, "Alt+C", icon="Letter-C-violet-icon", 
                                         tip="Add new column as a child of the currently selected element")
        addfiltergroupaction = self.createAction("Add Filter &Group", self.addFilterGroup, "Alt+G", icon="Letter-F-blue-icon", 
                                         tip="Add new filter group as a child of the current evaluation")
        addfilteraction = self.createAction("Add &Filter", self.addFilter, "Alt+H", icon="Letter-F-lg-icon", 
                                            tip="Add filter as a child of the current filter group")
        addaggregationaction = self.createAction("Add &Aggregation", self.addAggregation, "Alt+A", icon="Letter-A-dg-icon", 
                                            tip="Add aggregation as a child for the current top level column")
        
        deletelementaction = self.createAction("&Delete Element", self.deleteElement, QKeySequence.Delete, "delete-icon", 
                                               tip="Delete currently selected element")
        filemenu.addAction(loadaction)
        filemenu.addAction(saveaction)
        filemenu.addAction(saveasaction)
        filetoolbar.addAction(saveaction)
        filetoolbar.addAction(loadaction)
        filetoolbar.addSeparator()
        filetoolbar.addAction(addcolaction)
        filetoolbar.addAction(addfiltergroupaction)
        filetoolbar.addAction(addfilteraction)
        filetoolbar.addAction(addaggregationaction)
        filetoolbar.addAction(deletelementaction)
        
        
    def addColumn(self):
        print "Add column"
        pass
    def addFilterGroup(self):
        print "Add filter group"
        pass
    
    def addFilter(self):
        print "Add filter"
        pass
    
    def addAggregation(self):
        print "Add aggregation"
        pass
    
    def deleteElement(self):
        print "Delete Action"
        
    def updateStatus(self, message):
        self.statusBar().showMessage(message, 5000)
        
        
    def loadEvaluation(self):
        thedir = unicode(".")
        filename = unicode(QFileDialog.getOpenFileName(self, caption=QString("%s - Load an evaluation"%QApplication.applicationName()),
                                               directory=thedir, filter=unicode("XML files (*.xml)")))
        if filename:
            try:
                ev = IPETEvaluation.fromXMLFile(filename)
                message = "Loaded evaluation from %s"%filename
                self.setEvaluation(ev)
            except Exception, e:
                message = "Error: Could not load evaluation from file %s"%filename
                
            self.updateStatus(message)
        
        pass
    
    def saveEvaluation(self):
        if self.filename is None:
            filename = unicode(QFileDialog.getSaveFileName(self, caption=QString("%s - Load an evaluation"%QApplication.applicationName()),
                                                           directory = unicode("."), filter=unicode("XML files (*.xml)")))
        else:
            filename = self.filename
        
        if not filename:
            return
        
        Misc.saveAsXML(self.evaluation, filename)
        self.filename = filename
        self.updateStatus("Saved evaluation to file %s"%filename)
        
    
    def saveEvaluationAs(self):
        filename = unicode(QFileDialog.getSaveFileName(self, caption=QString("%s - Load an evaluation"%QApplication.applicationName()),
                                                       directory = unicode("."), filter=unicode("XML files (*.xml)")))
        if not filename:
            return
        
        Misc.saveAsXML(self.evaluation, filename)    
        self.filename = filename
        self.updateStatus("Saved evaluation to file %s"%filename)
        
    def createAction(self, text, slot=None, shortcut=None, icon=None,
        tip=None, checkable=False, signal="triggered()"):
        action = QAction(text, self)
        if icon is not None:
            action.setIcon(QIcon("images/%s.png" % icon))
        if shortcut is not None:
            action.setShortcut(shortcut)
        if tip is not None:
            action.setToolTip(tip)
            action.setStatusTip(tip)
        if slot is not None:
            self.connect(action, SIGNAL(signal), slot)
        if checkable:
            action.setCheckable(True)
        return action
        
    def changeSelection(self):
        if len(self.treewidget.selectedItems()) > 0:
            item = self.treewidget.selectedItems()[0]
        else: item = None
        
        for i in reversed(range(self.editframelayout.count())): 
            self.editframelayout.itemAt(i).widget().close()
        if item:
            editframecontent = EditableForm(self.treewidget.item2editable[item], self.editframe)
            textlabel = QLabel(QString("<b>Edit attributes for %s</b>"%(self.treewidget.item2editable[item].getName())))
        else:
            editframecontent = QLabel(QString("Select an element from the evaluation"))
            textlabel = QLabel(QString("<b>No element selected</b>"))
            
        textlabel.setMaximumHeight(20)
        textlabel.setMinimumHeight(20)
        textlabel.setAlignment(Qt.AlignCenter)
        textlabel.setBuddy(editframecontent)
        self.editframelayout.addWidget(textlabel)
        self.editframelayout.addWidget(editframecontent)
        self.connect(editframecontent, SIGNAL(EditableForm.USERINPUT_SIGNAL), self.updateItem) 
        
    def updateItem(self):
        self.treewidget.updateSelectedItem()
        
    
if __name__ == "__main__":
    
    ev = IPETEvaluation.fromXMLFile("test/testevaluate.xml")
    
    app = QApplication(sys.argv)
    app.setApplicationName("Evaluation editor")
    mainwindow = IpetEvaluationEditorApp()
    mainwindow.setEvaluation(ev)
    mainwindow.show()
    
    sys.exit(app.exec_())  
        
    