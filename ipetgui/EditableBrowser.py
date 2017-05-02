"""
Created on 21.09.2016

@author: bzfhende
"""
"""
Created on 26.03.2015

@author: bzfhende
"""
from PyQt4.QtGui import QFrame, QWidget, QLabel, \
    QApplication, QKeySequence, QFileDialog, \
    QVBoxLayout, QHBoxLayout
from .IPetTreeView import IpetTreeView
from .EditableForm import EditableForm
from PyQt4.QtCore import Qt, SIGNAL
from ipet.evaluation.IPETEvalTable import IPETEvaluation, IPETEvaluationColumn
import sys
from ipet.misc import misc
from ipet.evaluation.Aggregation import Aggregation
from ipet.evaluation.IPETFilter import IPETFilterGroup, IPETInstance
from ipet.evaluation.IPETFilter import IPETFilter
from .IpetMainWindow import IpetMainWindow

class EditableBrowser(QWidget):
    """
    classdocs
    """
    addedcolumns = 0
    addedfiltergroups = 0
    addedfilters = 0
    addedaggregations = 0
    addedinstances = 0
    ITEMEVENT = "itemchanged"

    def __init__(self, parent = None):
        """
        Constructor
        """
        super(EditableBrowser, self).__init__(parent)

        self.treewidget = IpetTreeView(self)
        layout = QHBoxLayout()
        layout.addWidget(self.treewidget, 3)
        self.editframe = QFrame(self)
        layout.addWidget(self.editframe, 2)

        self.editframelayout = QVBoxLayout()

        self.editframe.setLayout(self.editframelayout)

        self.setLayout(layout)
        self.editable = None

        self.initConnections()

    def initConnections(self):
        self.connect(self.treewidget, SIGNAL("itemSelectionChanged()"), self.redrawEditFrameContent)

    def setRootElement(self, editable):
        self.editable = editable
        self.treewidget.populateTree(editable)
        self.redrawEditFrameContent()

    def getRootElement(self):
        return self.editable


    def getMenuActions(self):
        return {}

    def getToolBarActions(self):
        return {}
    
    def addNewElementAsChildOfRootElement(self, newelement):
        rootelement = self.getRootElement()
        rootelement.addChild(newelement)
        self.reselectAfterInsertOrRemoval(rootelement)

    def addNewElementAsChildOfSelectedElement(self, newelement):

        selectededitable = self.treewidget.getSelectedEditable()
        selectededitable.addChild(newelement)
        self.reselectAfterInsertOrRemoval(selectededitable)

    def reselectAfterInsertOrRemoval(self, newselection):
        self.treewidget.populateTree(self.getRootElement())

        self.treewidget.setSelectedEditable(newselection)


    def deleteElement(self):
        selectededitable = self.treewidget.getSelectedEditable()
        parentofselectededitable = self.treewidget.getParentOfSelectedEditable()
        if parentofselectededitable is not None:
            children = parentofselectededitable.getChildren()
            index = children.index(selectededitable)
            if index == len(children) - 1:
                newselectededitable = parentofselectededitable
            else:
                newselectededitable = children[index + 1]
            parentofselectededitable.removeChild(selectededitable)
            self.reselectAfterInsertOrRemoval(newselectededitable)

    def clearLayout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            child.widget().deleteLater()


    def redrawEditFrameContent(self):

        if self.treewidget.getSelectedEditable() is not None:
            editable = self.treewidget.getSelectedEditable()
            editframecontent = EditableForm(editable, self.editframe)
            textlabel = QLabel(("<b>Edit attributes for %s</b>" % (editable.getName())))
        else:
            editframecontent = QLabel(("Select an element first to modify its properties"))
            textlabel = QLabel(("<b>No element selected</b>"))

        self.clearLayout(self.editframelayout)
        textlabel.setMaximumHeight(20)
        textlabel.setMinimumHeight(20)
        textlabel.setAlignment(Qt.AlignCenter)
        textlabel.setBuddy(editframecontent)
        self.editframelayout.addWidget(textlabel)
        self.editframelayout.addWidget(editframecontent)
        self.connect(editframecontent, SIGNAL(EditableForm.USERINPUT_SIGNAL), self.updateItem)
        self.emit(SIGNAL(self.ITEMEVENT))

    def updateItem(self):
        self.treewidget.updateSelectedItem()
        self.redrawEditFrameContent()

if __name__ == "__main__":

    app = QApplication(sys.argv)
    app.setApplicationName("Evaluation editor")
    mainwindow = IpetEvaluationEditorApp()
    try:
        ev = IPETEvaluation.fromXMLFile("test/testevaluate.xml")
        mainwindow.setEvaluation(ev)
    except:
        pass
    mainwindow.show()

    sys.exit(app.exec_())



