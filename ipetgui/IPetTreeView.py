"""
The MIT License (MIT)

Copyright (c) 2016 Zuse Institute Berlin, www.zib.de

Permissions are granted as stated in the license file you have obtained
with this software. If you find the library useful for your purpose,
please refer to README.md for how to cite IPET.

@author: Gregor Hendel
"""
from PyQt4.QtGui import QTreeWidget, QTreeWidgetItem, QMainWindow, QApplication,\
    QWidget, QHBoxLayout, QFrame, QIcon, QLabel, QVBoxLayout, QGridLayout, QColor
from ipet.evaluation import IPETEvaluation, IPETEvaluationColumn
import sys
from PyQt4.QtCore import SIGNAL, Qt
from .EditableForm import EditableForm
from ipet.evaluation import Aggregation
from ipet.evaluation import IPETFilterGroup, IPETValue
from ipet.evaluation import IPETFilter
from PyQt4 import QtCore
import os.path as osp
from ipet.concepts.IPETNode import IpetNodeAttributeError
class IpetTreeViewItem(QTreeWidgetItem):

    def __init__(self, ipetnode, parent = None):
        super(IpetTreeViewItem, self).__init__(parent, [ipetnode.getName()])
        self.ipetnode = ipetnode
        self.myIcon = None

    def getIpetNode(self):
        return self.ipetnode

    def data(self, column, role):
        if column == 0:
            if role == QtCore.Qt.DisplayRole:
                return self.ipetnode.getName()
            elif role == QtCore.Qt.ForegroundRole:
                try:
                    self.ipetnode.checkAttributes()
                    if self.ipetnode.isActive():
                        return QColor(0, 0, 0)
                    else:
                        return QColor(128, 128, 128)
                except IpetNodeAttributeError as e:
                    self.setStatusTip(0, e.getMessage())
                    return QColor(255, 0, 0)
            elif role == QtCore.Qt.DecorationRole:
                return self.myIcon

    def setMyIcon(self, icon):
        self.myIcon = icon


class IpetTreeView(QTreeWidget):
    """
    classdocs
    """
    imagepath = osp.sep.join((osp.dirname(__file__), osp.pardir, "images"))
    icons = {IPETEvaluationColumn:(osp.sep.join((imagepath, "Letter-C-violet-icon.png"))),
             Aggregation:(osp.sep.join((imagepath, "Letter-A-dg-icon.png"))),
             IPETFilterGroup:(osp.sep.join((imagepath, "Letter-G-gold-icon.png"))),
             IPETFilter:(osp.sep.join((imagepath, "Letter-F-lg-icon.png"))),
             IPETValue:(osp.sep.join((imagepath, "Letter-I-blue-icon.png")))}

    def __init__(self, parent = None):
        """
        Constructor
        """
        super(IpetTreeView, self).__init__(parent)
        self.header().hide()
        self.setAlternatingRowColors(True)
        self.setEditTriggers(QTreeWidget.NoEditTriggers)
        self.setSelectionMode(QTreeWidget.SingleSelection)
        self.editable2item = {}
    
    def updateSelectedItem(self):
        pass

    def populateTree(self, editable):
        self.clear()
        self.setColumnCount(1)
        self.setItemsExpandable(True)
        self.createAndAddItem(editable, parent = self)
    
    def bindItemIcon(self, item, editable):
        filename = self.icons.get(editable.__class__)
        if filename is not None:
            item.setMyIcon(QIcon(filename))
            
    def itemGetEditable(self, item):
        """
        returns the Editable object corresponding to the given item
        """
        return item.getIpetNode()
        
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
        item = self.editable2item[editable]
        if editable.equals(item.getIpetNode()):
            # we need to set both the selected and the current item
            self.setItemSelected(item, True)
            self.setCurrentItem(item)
            assert self.currentItem() == item
            self.emit(SIGNAL("itemSelectionChanged()"))
            self.updateSelectedItem()
            return
        
        
    def createAndAddItem(self, editable, parent=None):
        if parent is None:
            parent = self
        me = IpetTreeViewItem(editable, parent)
        self.editable2item[editable] = me
        self.bindItemIcon(me, editable)
        try:
            if editable.getChildren() is not None:
                for child in editable.getChildren():
                    self.createAndAddItem(child, me)
                
                self.expandItem(me)
        except AttributeError as e:
            print(e)
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
    
    
