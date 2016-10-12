'''
Created on 28.12.2013

@author: bzfhende
'''
from Tkinter import Menu, Toplevel
from ipet.gui import IPETBrowser
from Tkconstants import BOTH
from ipet import misc
import tkFileDialog

class IPETManagerMenu(Menu):
    '''
    a manager menu has all manager related actions available
    '''
    def __init__(self, master, manager, cnf={}):
        Menu.__init__(self, master, cnf)
        self.manager = manager
        if "fromXMLFile" in dir(self.manager.__class__):
            self.add_command(label="Save", command=self.saveManageables)
            self.add_command(label="Load", command=self.loadManageables)

        self.add_command(label='Browse...', command=self.openBrowser)


    def openBrowser(self):
        '''
        opens a browser centered on the screen to browse managed objects
        '''
        self.tp = Toplevel()
        self.browser = IPETBrowser(self.tp, self.manager)
        self.browser.pack(fill=BOTH, expand=True)
        self.tp.protocol('WM_DELETE_WINDOW', self.quit)
        self.tp.mainloop()

    def quit(self):
        self.browser.quit()
        self.tp.destroy()


    def loadManageables(self):
        '''
        load manageables
        '''
        filename = tkFileDialog.askopenfilename()
        if filename:
            rm = self.manager.__class__.fromXMLFile(filename)
            for reader in rm.getManageables(False):
                try:
                    self.manager.registerReader(reader)
                except:
                    pass

    def saveManageables(self):
        '''
        save custom readers and list readers to a specified destination
        '''
        filename = tkFileDialog.asksaveasfilename()
        if filename:
            misc.saveAsXML(self.manager, filename)
