"""
The MIT License (MIT)

Copyright (c) 2018 Zuse Institute Berlin, www.zib.de

Permissions are granted as stated in the license file you have obtained
with this software. If you find the library useful for your purpose,
please refer to README.md for how to cite IPET.

@author: Gregor Hendel
"""
from PyQt4.QtGui import QFrame, QWidget, QLabel,\
    QApplication, QKeySequence, QFileDialog, \
    QVBoxLayout, QHBoxLayout
from .IPetTreeView import IpetTreeView
from .EditableForm import EditableForm
from PyQt4.QtCore import Qt, SIGNAL
from PyQt4.Qt import QLayout, QTabWidget
from ipet.evaluation.IPETEvalTable import IPETEvaluation, IPETEvaluationColumn
import sys
from ipet.misc import misc
from ipet.evaluation.Aggregation import Aggregation
from ipet.evaluation.IPETFilter import IPETFilterGroup, IPETValue
from ipet.evaluation.IPETFilter import IPETFilter
from .IpetMainWindow import IpetMainWindow
from .EditableBrowser import EditableBrowser
from .IPETApplicationTab import IPETApplicationTab
from .SimpleQIPETDataView import IPETDataTableView
from . import ExperimentManagement

class EvaluationEditorWindow(IPETApplicationTab):
    addedcolumns = 0
    addedfiltergroups = 0
    addedfilters = 0
    addedaggregations = 0
    addedinstances = 0

    def __init__(self, parent=None):
        """
        Constructor
        """
        super(EvaluationEditorWindow, self).__init__(parent)

        self.browser = EditableBrowser(self)
        self.evaluation = None
        self.filename = None
        self.lastfiltergroup = None
        vlayout = QVBoxLayout()
        layout = QHBoxLayout()
        layout.addWidget(self.browser)
        layout.setSizeConstraint(QLayout.SetMaximumSize)
        vlayout.addLayout(layout)
        tabwidget = QTabWidget(self)
        self.tableview = IPETDataTableView(None, self)
        self.aggtableview = IPETDataTableView(None, self)
        tabwidget.addTab(self.tableview, ("Instances"))
        tabwidget.addTab(self.aggtableview, ("Aggregated"))
        vlayout.addWidget(tabwidget)
        self.setLayout(vlayout)

        self.defineActions()
        self.initConnections()
        self.passGroupToTableViews()

    def initConnections(self):
        self.connect(self.browser, SIGNAL(EditableBrowser.ITEMEVENT), self.itemChanged)

    def setEvaluation(self, evaluation):
        self.browser.setRootElement(evaluation)
        self.evaluation = evaluation
        EditableForm.extendAvailableOptions("datakey", [col.getName() for col in evaluation.getActiveColumns()])

    def defineActions(self):

        self.loadaction = self.createAction("&Load evaluation", self.loadEvaluation, QKeySequence.Open, icon = "Load-icon",
                                       tip="Load evaluation from XML file (current evaluation gets discarded)")
        self.saveaction = self.createAction("&Save evaluation", self.saveEvaluation, QKeySequence.Save, icon = "disk-icon",
                                       tip="Save evaluation to XML format")
        self.saveasaction = self.createAction("&Save evaluation as", self.saveEvaluationAs, QKeySequence.SaveAs, icon = "disk-icon",
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
        self.reevaluateaction = self.createAction("Reevaluate", self.reevaluate, "F5", icon="reevaluate-icon",
                                        tip="Reevaluate the current evaluation on the _experiment")

    def getMenuActions(self):
        return (("&File", [self.loadaction, self.saveaction, self.saveasaction]),("&Data", [self.reevaluateaction]))

    def getToolBarActions(self):
        return (("File", [self.saveaction, self.loadaction]),
                ("Evaluation", [self.addcolaction,
                                self.addfiltergroupaction,
                                self.addfilteraction,
                                self.addaggregationaction,
                                self.addinstancenaction,
                                self.deletelementaction]
                 ),
                ("Data", [self.reevaluateaction])
                )

    def addColumn(self):
        self.updateStatus("Add column")
        self.addedcolumns += 1
        newcolname = "New Column %d"%self.addedcolumns
        newcol = IPETEvaluationColumn(name=newcolname)
        self.browser.addNewElementAsChildOfSelectedElement(newcol)
        EditableForm.extendAvailableOptions("datakey", [col.getName() for col in self.evaluation.getActiveColumns()])

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
        newinstance = IPETValue(newinstancename)

        self.browser.addNewElementAsChildOfSelectedElement(newinstance)

    def loadEvaluation(self):
        thedir = str(".")
        filename = str(QFileDialog.getOpenFileName(self, caption=("%s - Load an evaluation"%QApplication.applicationName()),
                                               directory=thedir, filter=str("XML files (*.xml)")))
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
            filename = str(QFileDialog.getSaveFileName(self, caption=("%s - Save current evaluation"%QApplication.applicationName()),
                                                           directory = str("."), filter=str("XML files (*.xml)")))
        else:
            filename = self.filename

        if not filename:
            return

        misc.saveAsXML(self.evaluation, filename)
        self.filename = filename
        self.updateStatus("Saved evaluation to file %s"%filename)


    def saveEvaluationAs(self):
        filename = str(QFileDialog.getSaveFileName(self, caption=("%s - Save current evaluation"%QApplication.applicationName()),
                                                       directory = str("."), filter=str("XML files (*.xml)")))
        if not filename:
            return

        misc.saveAsXML(self.evaluation, filename)
        self.filename = filename
        self.updateStatus("Saved evaluation to file %s"%filename)

    def enableOrDisableActions(self):
        for action, addclass in zip([self.addcolaction, self.addfiltergroupaction, self.addfilteraction, self.addaggregationaction, self.addinstancenaction],
                                    [IPETEvaluationColumn(), IPETFilterGroup(), IPETFilter(), Aggregation(), IPETValue()]):
            if self.browser.treewidget.currentItemAcceptsClassAsChild(addclass):
                action.setEnabled(True)
            else:
                action.setEnabled(False)

    def itemChanged(self):
        self.enableOrDisableActions()
        self.passGroupToTableViews()

    def setDataFrames(self, tableviewdf, aggtableviewdf):
        """
        sets both data frames and formatters for the views
        """
        self.tableview.setDataFrame(tableviewdf, self.evaluation.getColumnFormatters(tableviewdf))
        self.aggtableview.setDataFrame(aggtableviewdf, self.evaluation.getColumnFormatters(aggtableviewdf))

    def passGroupToTableViews(self):

        if self.evaluation is None or not self.evaluation.isEvaluated():
            self.updateStatus("Refresh evaluation first to update results")
            return

        selectedfiltergroup = None
        if self.browser.treewidget.getSelectedEditable().__class__ is IPETFilterGroup:
            selectedfiltergroup = self.browser.treewidget.getSelectedEditable()

#        if selectedfiltergroup is not None and selectedfiltergroup.isActive():
#            return

        if selectedfiltergroup != self.lastfiltergroup:
            if selectedfiltergroup is not None:
                self.updateStatus("Display data for selected filter group \"%s\"" % selectedfiltergroup.getName())
                self.setDataFrames(self.evaluation.getInstanceGroupData(selectedfiltergroup), self.evaluation.getAggregatedGroupData(selectedfiltergroup))
            else:
                self.updateStatus("Display data for all instances")
                self.setDataFrames(self.evaluation.getInstanceData(), self.evaluation.getAggregatedData())

        self.lastfiltergroup = selectedfiltergroup

    def reevaluate(self):
        if self.evaluation is not None:
            rettab, retagg = self.evaluation.evaluate(ExperimentManagement.getExperiment())
            self.setDataFrames(rettab, retagg)

class IpetEvaluationEditorApp(IpetMainWindow):
    """
    This app represents the Editable Browser in a single, executable window
    """

    def __init__(self, parent = None):
        super(IpetEvaluationEditorApp, self).__init__(parent)
        self.evaluationeditorwindow = EvaluationEditorWindow()
        self.populateMenu(self.evaluationeditorwindow)
        self.populateToolBar(self.evaluationeditorwindow)
        self.setCentralWidget(self.evaluationeditorwindow)

    def setEvaluation(self, evaluation):
        self.evaluationeditorwindow.setEvaluation(evaluation)

    def setExperiment(self, _experiment):
        EditableForm.extendAvailableOptions("datakey", _experiment.getDatakeys())


if __name__ == "__main__":

    app = QApplication(sys.argv)
    app.setApplicationName("Evaluation editor")
    mainwindow = IpetEvaluationEditorApp()
    ev = IPETEvaluation.fromXMLFile("../test/testevaluate.xml")
    ev.set_defaultgroup('testmode')
    ExperimentManagement.addOutputFiles(["../test/check.short.scip-3.1.0.1.linux.x86_64.gnu.dbg.spx.opt85.testmode.out"])
    ExperimentManagement.getExperiment().collectData()
    mainwindow.setEvaluation(ev)
    mainwindow.setExperiment(ExperimentManagement.getExperiment())
    mainwindow.evaluationeditorwindow.reevaluate()
    IpetMainWindow.getStatusBar().showMessage("I am a working status bar", 5000)
    mainwindow.show()

    sys.exit(app.exec_())


