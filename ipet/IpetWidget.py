'''
Created on 08.03.2013

@author: bzfhende
'''
from Tkinter import Frame
from Tkconstants import GROOVE

class IpetWidget(Frame):
    '''
    top class for all Ipet widgets: override this class for customized plug-ins that should make it into the notebook on the main frame
    '''


    def __init__(self, master, gui, **kw):
        '''
        construct an Ipet widget
        '''
        Frame.__init__(self, master, bg="white", bd=10, relief=GROOVE, **kw)
        self.gui = gui
