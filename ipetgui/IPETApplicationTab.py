"""
The MIT License (MIT)

Copyright (c) 2016 Zuse Institute Berlin, www.zib.de

Permissions are granted as stated in the license file you have obtained
with this software. If you find the library useful for your purpose,
please refer to README.md for how to cite IPET.

@author: Gregor Hendel
"""
from PyQt4.Qt import QWidget, QAction, QIcon, SIGNAL

import os.path as osp
from .IpetMainWindow import IpetMainWindow
class IPETApplicationTab(QWidget):
    """
    base class for all widgets displayed in the single tabs of the IPET application
    """

    imagepath = osp.sep.join((osp.dirname(__file__), osp.pardir, "images"))
    def __init__(self, parent = None):
        super(IPETApplicationTab, self).__init__(parent)

    def getMenuActions(self):
        """
        returns a tuple of menu actions. Nested menus are supported

        format to be used is (menu-name, [actions])
        """
        return None

    def getToolBarActions(self):
        """
        returns a list of action lists

        format is [[action1,action2,...], [actionk, ...]]

        just a list of actions is fine, using nested lists will tell the caller where to put separators
        """
        return None

    def createAction(self, text, slot = None, shortcut = None, icon = None,
        tip = None, checkable = False, signal = "triggered()"):
        action = QAction(text, self)
        if icon is not None:
            action.setIcon(QIcon(osp.sep.join((self.imagepath, "%s.png" % icon))))
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

    def updateStatus(self, message):
        IpetMainWindow.getStatusBar().showMessage(message, 5000)
