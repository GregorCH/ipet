'''
Created on 25.03.2015

@author: bzfhende
'''
from PyQt4.QtGui import QTreeWidget, QTreeWidgetItem, QMainWindow, QApplication,\
    QWidget, QHBoxLayout, QFrame, QIcon, QLabel, QVBoxLayout, QGridLayout
from ipet.evaluation import IPETEvaluation, IPETEvaluationColumn
import sys
from PyQt4.QtCore import SIGNAL, Qt
from .EditableForm import EditableForm
from ipet.evaluation import Aggregation
from ipet.evaluation import IPETFilterGroup, IPETInstance
from ipet.evaluation import IPETFilter
from PyQt4 import QtCore
import os.path as osp
class IpetTreeView(QTreeWidget):
    '''
    classdocs
    '''
    imagepath = osp.sep.join((osp.dirname(__file__), osp.pardir, "images"))
    icons = {IPETEvaluationColumn:(osp.sep.join((imagepath, "Letter-C-violet-icon.png"))),
             Aggregation:(osp.sep.join((imagepath, "Letter-A-dg-icon.png"))),
             IPETFilterGroup:(osp.sep.join((imagepath, "Letter-G-gold-icon.png"))),
             IPETFilter:(osp.sep.join((imagepath, "Letter-F-lg-icon.png"))),
             IPETInstance:(osp.sep.join((imagepath, "Letter-I-blue-icon.png")))}

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
        item.setText(0, self.itemGetEditable(item).getName()) 
        
    def populateTree(self, editable):
        self.clear()
        self.setColumnCount(1)
        self.setItemsExpandable(True)
        self.item2editable = []
        self.createAndAddItem(editable)
    
    def bindItemIcon(self, item, editable):
        filename = self.icons.get(editable.__class__)
        if filename is not None:
            item.setIcon(0, QIcon(filename))
            
    def itemGetEditable(self, item):
        '''
        returns the Editable object corresponding to the given item
        '''
        for i,e in self.item2editable:
            if i == item:
                return e
            
        raise Exception("List does not contain the item %s, have only %s" % (item, self.item2editable))
        
    
    def currentItemAcceptsClassAsChild(self, nodeclass):
        item = self.currentItem()
        if not item:
            return False
        return self.itemAcceptsClassAsChild(item, nodeclass)
        
    def itemAcceptsClassAsChild(self, item, nodeclass):
        node = self.itemGetEditable(item)
        if node.acceptsAsChild(nodeclass):
            return True
        else:
            return False
        
    def getSelectedEditable(self):
        try:
            item = self.selectedItems()[0]
            if not item:
                return None
        except:
            return None
        
        return self.itemGetEditable(item)
    
    def getParentOfSelectedEditable(self):
        try:
            selecteditem = self.selectedItems()[0]
            return self.itemGetEditable(selecteditem.parent())
        except:
            return None

    def setSelectedEditable(self, editable):
        self.setItemSelected(self.currentItem(), False)
        for item, editableval in self.item2editable:
            if editable == editableval:
                #we need to set both the selected and the current item
                self.setItemSelected(item, True)
                self.setCurrentItem(item)
                assert self.currentItem() == item
                self.emit(SIGNAL("itemSelectionChanged()"))
                self.updateSelectedItem()
                return
        
        
    def createAndAddItem(self, editable, parent=None):
        if parent is None:
            parent = self
        me = QTreeWidgetItem(parent, [editable.getName()])
        self.bindItemIcon(me, editable)
        self.item2editable.append((me, editable))
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
    def redrawEditFrameContent():
        item = treeview.selectedItems()[0]
        
        
        for i in reversed(list(range(layout2.count()))): 
            layout2.itemAt(i).widget().close()
        editframecontent = EditableForm(treeview.itemGetEditable(item), editframe)
        textlabel = QLabel(("Edit attributes for %s"%(treeview.itemGetEditable(item).getName())))
        textlabel.setAlignment(Qt.AlignCenter)
        textlabel.setBuddy(editframecontent)
        layout2.addWidget(textlabel, 0,0)
        layout2.addWidget(editframecontent, 1,0)
        
    mainwindow.connect(treeview, SIGNAL("itemSelectionChanged()"), redrawEditFrameContent)
    mainwindow.show()
    
    sys.exit(app.exec_())
    
    
