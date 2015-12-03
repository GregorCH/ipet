'''
Created on 26.03.2015

@author: bzfhende
'''
from PyQt4.QtGui import QMainWindow, QAction, QIcon
from PyQt4.QtCore import SIGNAL
import os.path as osp
class IpetMainWindow(QMainWindow):
    '''
    classdocs
    '''


    imagepath = osp.sep.join((osp.dirname(__file__), osp.pardir, "images"))
    def __init__(self, parent=None):
        '''
        Constructor
        '''
        super(IpetMainWindow, self).__init__(parent)
        
        print self.imagepath
        
        self.setGeometry(300, 300, 800, 500)
        

    def createAction(self, text, slot=None, shortcut=None, icon=None,
        tip=None, checkable=False, signal="triggered()"):
        action = QAction(text, self)
        if icon is not None:
            action.setIcon(QIcon(osp.sep.join((self.imagepath,"%s.png" % icon))))
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
    
        
    
    