'''
Created on 25.03.2015

@author: bzfhende
'''
from PyQt4.QtGui import QTreeWidget, QTreeWidgetItem, QMainWindow, QApplication,\
    QWidget, QHBoxLayout, QFrame, QIcon, QLabel, QVBoxLayout, QGridLayout
from ipet.IPETEvalTable import IPETEvaluation, IPETEvaluationColumn
import sys
from PyQt4.QtCore import SIGNAL, QString, Qt
from qipet.EditableForm import EditableForm
from ipet.Aggregation import Aggregation
from ipet.IPETFilter import IPETFilterGroup, IPETFilter, IPETInstance
from PyQt4 import QtCore
import os.path as osp
class IpetTreeView(QTreeWidget):
    '''
    classdocs
    '''
    imagepath = osp.sep.join((osp.dirname(__file__), osp.pardir, "images"))
    icons = {IPETEvaluationColumn:QString(osp.sep.join((imagepath, "Letter-C-violet-icon.png"))),
             Aggregation:QString(osp.sep.join((imagepath, "Letter-A-dg-icon.png"))),
             IPETFilterGroup:QString(osp.sep.join((imagepath, "Letter-G-gold-icon.png"))),
             IPETFilter:QString(osp.sep.join((imagepath, "Letter-F-lg-icon.png"))),
             IPETInstance:QString(osp.sep.join((imagepath, "Letter-I-blue-icon.png")))}

    def __init__(self, parent = None):
        '''
        Constructor
        '''
        super(IpetTreeView, self).__init__(parent)
        self.header().hide()
        self.setAlternatingRowColors(True)
        self.setEditTriggers(QTreeWidget.NoEditTriggers)
        self.setSelectionMode(QTreeWidget.SingleSelection)
        
    
    def updateSelectedItem(self):
        if len(self.selectedItems()) == 0:
            return
            
        item = self.selectedItems()[0]
        item.setText(0, self.item2editable[item].getName()) 
        
    def populateTree(self, editable):
        self.clear()
        self.setColumnCount(1)
        self.setItemsExpandable(True)
        self.item2editable = {}
        self.createAndAddItem(editable)
    
    def bindItemIcon(self, item, editable):
        filename = self.icons.get(editable.__class__)
        if filename is not None:
            item.setIcon(0, QIcon(filename))
    
    def currentItemAcceptsClassAsChild(self, nodeclass):
        item = self.currentItem()
        if not item:
            return False
        return self.itemAcceptsClassAsChild(item, nodeclass)
        
    def itemAcceptsClassAsChild(self, item, nodeclass):
        node = self.item2editable[item]
        if node.acceptsAsChild(nodeclass):
            return True
        else:
            return False
        
    def getSelectedEditable(self):
        item = self.currentItem()
        if not item:
            return False
        else:
            return self.item2editable[item]
        
    def setSelectedEditable(self, editable):
        self.setItemSelected(self.currentItem(), False)
        for item, editableval in self.item2editable.items():
            if editable == editableval:
                self.setItemSelected(item, True)
                self.emit(SIGNAL("itemSelectionChanged()"))
                return
        
        
    def createAndAddItem(self, editable, parent=None):
        if parent is None:
            parent = self
        me = QTreeWidgetItem(parent, [editable.getName()])
        self.bindItemIcon(me, editable)
        self.item2editable[me] = editable
        try:
            if editable.getChildren() is not None:
                for child in editable.getChildren():
                    self.createAndAddItem(child, me)
                
                self.expandItem(me)
        except AttributeError:
            pass

editframecontent = None
if __name__ == "__main__":
    
    ev = IPETEvaluation.fromXMLFile("test/testevaluate.xml")
    
    app = QApplication(sys.argv)
    mainwindow = QMainWindow()
    thewidget = QWidget(mainwindow)
    treeview = IpetTreeView(thewidget)
    
    layout = QHBoxLayout()
    layout.addWidget(treeview)
    
    editframe = QFrame(thewidget)
    layout.addWidget(editframe)

    layout2 = QGridLayout()

    editframe.setLayout(layout2)
    
    thewidget.setLayout(layout)
    mainwindow.setCentralWidget(thewidget)
    treeview.populateTree(ev)
    def changeSelection():
        item = treeview.selectedItems()[0]
        
        
        for i in reversed(range(layout2.count())): 
            layout2.itemAt(i).widget().close()
        editframecontent = EditableForm(treeview.item2editable[item], editframe)
        textlabel = QLabel(QString("Edit attributes for %s"%(treeview.item2editable[item].getName())))
        textlabel.setAlignment(Qt.AlignCenter)
        textlabel.setBuddy(editframecontent)
        layout2.addWidget(textlabel, 0,0)
        layout2.addWidget(editframecontent, 1,0)
        
    mainwindow.connect(treeview, SIGNAL("itemSelectionChanged()"), changeSelection)
    mainwindow.show()
    
    sys.exit(app.exec_())
    
    