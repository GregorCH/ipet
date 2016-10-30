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

    menus = {}
    toolbars = {}
    _statusbar = None
    def __init__(self, parent=None):
        '''
        Constructor
        '''
        super(IpetMainWindow, self).__init__(parent)
        
        self.setGeometry(100, 100, 1200, 800)
        print "status bar"
        IpetMainWindow.setStatusBar(self.statusBar())
        print IpetMainWindow.getStatusBar()
        
    @staticmethod
    def getStatusBar():
        return IpetMainWindow._statusbar
    
    @staticmethod
    def setStatusBar(statusbar):
        IpetMainWindow._statusbar = statusbar
        
    def populateMenu(self, ipetapplicationtab):
        for menuname, actions in ipetapplicationtab.getMenuActions():
            menu = self.menus.setdefault(menuname, self.menuBar().addMenu(menuname))
            for action in actions:
                menu.addAction(action)

    def populateToolBar(self, ipetapplicationtab):
        for toolbarname, actions in ipetapplicationtab.getToolBarActions():
            toolbar = self.toolbars.setdefault(toolbarname, self.addToolBar("toolbarname"))
            for action in actions:
                toolbar.addAction(action)


