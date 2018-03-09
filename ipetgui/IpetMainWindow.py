"""
The MIT License (MIT)

Copyright (c) 2018 Zuse Institute Berlin, www.zib.de

Permissions are granted as stated in the license file you have obtained
with this software. If you find the library useful for your purpose,
please refer to README.md for how to cite IPET.

@author: Gregor Hendel
"""
from PyQt4.QtGui import QMainWindow, QAction, QIcon
from PyQt4.QtCore import SIGNAL
import os.path as osp
class IpetMainWindow(QMainWindow):
    """
    classdocs
    """

    menus = {}
    toolbars = {}
    _statusbar = None
    def __init__(self, parent=None):
        """
        Constructor
        """
        super(IpetMainWindow, self).__init__(parent)
        
        self.setGeometry(100, 100, 1200, 800)
        IpetMainWindow.setStatusBar(self.statusBar())
        
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
            toolbar = self.toolbars.setdefault(toolbarname, self.addToolBar(toolbarname))
            for action in actions:
                toolbar.addAction(action)


