'''
Created on 26.03.2015

@author: bzfhende
'''
from PyQt4.QtGui import QFrame, QWidget, QLabel,\
    QApplication, QKeySequence, QFileDialog, \
    QVBoxLayout, QHBoxLayout
from qipet.IPetTreeView import IpetTreeView
from qipet.EditableForm import EditableForm
from PyQt4.QtCore import QString, Qt, SIGNAL
from ipet.evaluation.IPETEvalTable import IPETEvaluation, IPETEvaluationColumn
import sys
from ipet.misc import misc
from ipet.evaluation.Aggregation import Aggregation
from ipet.evaluation.IPETFilter import IPETFilterGroup, IPETInstance
from ipet.evaluation.IPETFilter import IPETFilter
from qipet.IpetMainWindow import IpetMainWindow
from EditableBrowser import EditableBrowser
from IPETApplicationTab import IPETApplicationTab
from EditableBrowser import EditableBrowser
from PyQt4.Qt import QLayout

class EvaluationEditorWindow(IPETApplicationTab):
    addedcolumns = 0
    addedfiltergroups = 0
    addedfilters = 0
    addedaggregations = 0
    addedinstances = 0

    def __init__(self, parent=None):
        '''
        Constructor
        '''
        super(EvaluationEditorWindow, self).__init__(parent)
        
        self.browser = EditableBrowser(self)
        self.evaluation = None
        self.filename = None
        layout = QHBoxLayout()
        layout.addWidget(self.browser)
        layout.setSizeConstraint(QLayout.SetMaximumSize)
        self.setLayout(layout)
        

        self.defineActions()
        self.initConnections()
        
    def initConnections(self):
        self.connect(self.browser, SIGNAL(EditableBrowser.ITEMEVENT), self.enableOrDisableActions)

    def setEvaluation(self, evaluation):
        self.browser.setRootElement(evaluation)
        self.evaluation = evaluation
        
    def defineActions(self):
        
        self.loadaction = self.createAction("&Load", self.loadEvaluation, QKeySequence.Open, icon = "Load-icon",
                                       tip="Load evaluation from XML file (current evaluation gets discarded)")
        self.saveaction = self.createAction("&Save", self.saveEvaluation, QKeySequence.Save, icon = "disk-icon",
                                       tip="Save evaluation to XML format")
        self.saveasaction = self.createAction("&Save as", self.saveEvaluationAs, QKeySequence.SaveAs, icon = "disk-icon",
                                       tip="Save evaluation to XML format")
        self.addcolaction = self.createAction("Add &Column", self.addColumn, "Alt+C", icon="Letter-C-violet-icon", 
                                         tip="Add new column as a child of the currently selected element")
        self.addfiltergroupaction = self.createAction("Add Filter &Group", self.addFilterGroup, "Alt+G", icon="Letter-G-gold-icon", 
                                         tip="Add new filter group as a child of the current evaluation")
        self.addfilteraction = self.createAction("Add &Filter", self.addFilter, "Alt+H", icon="Letter-F-lg-icon", 
                                            tip="Add filter as a child of the current filter group")
        self.addaggregationaction = self.createAction("Add &Aggregation", self.addAggregation, "Alt+A", icon="Letter-A-dg-icon", 
                                            tip="Add aggregation as a child for the current top level column")
        self.addinstancenaction = self.createAction("Add &Instance", self.addInstance, "Alt+I", icon="Letter-I-blue-icon", 
                                            tip="Add instance as child of the current filter")
        
        self.deletelementaction = self.createAction("&Delete Element", self.browser.deleteElement, QKeySequence.Delete, "delete-icon",
                                               tip="Delete currently selected element")

    def getMenuActions(self):
        return (("&File", [self.loadaction, self.saveaction, self.saveasaction]),)
    
    def getToolBarActions(self):
        return (("File", [self.saveaction, self.loadaction]),
                ("Evaluation", [self.addcolaction,
                                self.addfiltergroupaction,
                                self.addfilteraction,
                                self.addaggregationaction,
                                self.addinstancenaction,
                                self.deletelementaction]
                 ),
                )

    def addColumn(self):
        self.updateStatus("Add column")
        self.addedcolumns += 1
        newcolname = "New Column %d"%self.addedcolumns 
        newcol = IPETEvaluationColumn(name=newcolname)
        self.browser.addNewElementAsChildOfSelectedElement(newcol)
        
    def addFilterGroup(self):
        self.updateStatus("Add filter group")
        self.addedfiltergroups += 1
        newfiltergroupname = "New Group %d"%self.addedfiltergroups
        newfiltergroup = IPETFilterGroup(newfiltergroupname)

        self.browser.addNewElementAsChildOfSelectedElement(newfiltergroup)
        
    
    def addFilter(self):
        self.updateStatus("Add filter")
        self.addedfilters += 1

        newfilter = IPETFilter(expression1 = "CHANGE", expression2 = "CHANGE")
        print newfilter.getName()
        self.browser.addNewElementAsChildOfSelectedElement(newfilter)


    def addAggregation(self):
        self.updateStatus("Add aggregation")
        self.addedaggregations += 1
        newaggregationname = "New Aggregation %d"%self.addedaggregations
        newaggregation = Aggregation(newaggregationname)

        self.browser.addNewElementAsChildOfSelectedElement(newaggregation)

    def addInstance(self):
        self.updateStatus("Add instance")
        self.addedinstances += 1
        newinstancename = "new Instance %d"%self.addedinstances
        newinstance = IPETInstance(newinstancename)
        
        self.browser.addNewElementAsChildOfSelectedElement(newinstance)
        
    def loadEvaluation(self):
        thedir = unicode(".")
        filename = unicode(QFileDialog.getOpenFileName(self, caption=QString("%s - Load an evaluation"%QApplication.applicationName()),
                                               directory=thedir, filter=unicode("XML files (*.xml)")))
        if filename:
            try:
                ev = IPETEvaluation.fromXMLFile(filename)
                message = "Loaded evaluation from %s"%filename
                self.setEvaluation(ev)
            except Exception:
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
        
        misc.saveAsXML(self.evaluation, filename)
        self.filename = filename
        self.updateStatus("Saved evaluation to file %s"%filename)
        
    
    def saveEvaluationAs(self):
        filename = unicode(QFileDialog.getSaveFileName(self, caption=QString("%s - Load an evaluation"%QApplication.applicationName()),
                                                       directory = unicode("."), filter=unicode("XML files (*.xml)")))
        if not filename:
            return
        
        misc.saveAsXML(self.evaluation, filename)
        self.filename = filename
        self.updateStatus("Saved evaluation to file %s"%filename)
        
    def enableOrDisableActions(self):
        for action, addclass in zip([self.addcolaction, self.addfiltergroupaction, self.addfilteraction, self.addaggregationaction, self.addinstancenaction],
                                    [IPETEvaluationColumn(), IPETFilterGroup(), IPETFilter(), Aggregation(), IPETInstance()]):
            if self.browser.treewidget.currentItemAcceptsClassAsChild(addclass):
                action.setEnabled(True)
            else:
                action.setEnabled(False)



class IpetEvaluationEditorApp(IpetMainWindow):
    '''
    classdocs
    '''

    def __init__(self, parent = None):
        super(IpetEvaluationEditorApp, self).__init__(parent)
        self.evaluationeditorwindow = EvaluationEditorWindow()
        self.populateMenu(self.evaluationeditorwindow)
        self.populateToolBar(self.evaluationeditorwindow)
        self.setCentralWidget(self.evaluationeditorwindow)

    def setEvaluation(self, evaluation):
        self.evaluationeditorwindow.setEvaluation(evaluation)




        
    def setExperiment(self, experiment):
        EditableForm.extendAvailableOptions("datakey", experiment.getDatakeys())

    
if __name__ == "__main__":
    
    app = QApplication(sys.argv)
    app.setApplicationName("Evaluation editor")
    mainwindow = IpetEvaluationEditorApp()
    ev = IPETEvaluation.fromXMLFile("../test/testevaluate.xml")
    mainwindow.setEvaluation(ev)
    mainwindow.show()
    
    sys.exit(app.exec_())
        
    
