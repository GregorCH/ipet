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
    statusbar = None
    def __init__(self, parent=None):
        '''
        Constructor
        '''
        super(IpetMainWindow, self).__init__(parent)
        
        self.setGeometry(300, 300, 800, 500)
        IpetMainWindow.statusbar = self.statusBar()
        
    
        
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
    
