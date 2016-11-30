'''
Created on 30.04.2013

@author: bzfhende
'''
from .IPETWidget import IpetWidget
from tkinter.constants import TOP
import tkinter.constants
from .IPETScrolledOutputWidget import ScrolledOutputWidget
from tkinter.ttk import Frame, OptionMenu, Label
from tkinter import StringVar

class IpetOutputWidget(IpetWidget):
    '''
    the widget for the log file output of a specific instance
    '''
    name = "Output Widget"

    def __init__(self, master, gui, **kw):

        IpetWidget.__init__(self, master, gui, **kw)
#        self.tableframe = SCIPTable(self, 10, gui, bd=5, bg="", width=self.winfo_screenwidth()/10, height=self.winfo_screenheight()/3)
#
#        self.tableframe.pack(side=LEFT, fill=Y)
        self.navpanel = Frame(self, width=self.winfo_screenwidth())
        Label(self.navpanel, text="select test run and instance:").grid(row=0, column=1)
        self.trvar = StringVar(value=str(None))
        self.probvar = StringVar(value=str(None))

        self.navpanel.pack(side=TOP, fill=tkinter.constants.X)
        self.textoutputframe = ScrolledOutputWidget(self, self.gui, bd=5, bg="white", width=self.winfo_screenwidth(), height=self.winfo_screenheight())
        self.textoutputframe.pack(side=TOP, expand=1, fill=tkinter.constants.BOTH)
        self.trvar.trace_variable("w", self.reactOnSelection)
        self.probvar.trace_variable("w", self.reactOnSelection)

        self.updateBoxes()

        gui.requestUpdate(self)

    def updateBoxes(self):
        try:
            self.omtr.destroy()
            self.ompr.destroy()
        except AttributeError:
            pass

        self.omtr = OptionMenu(self.navpanel, self.trvar, self.trvar.get(), *([str(None)] + self.gui.getTestrunnames()))
        self.omtr.config(width=40)
        self.omtr.grid(row=0, column=2)

        self.ompr = OptionMenu(self.navpanel, self.probvar, self.probvar.get(), *([str(None)] + self.gui.getProblemList()))
        self.ompr.config(width=40)
        self.ompr.grid(row=0, column=3)

    def reactOnSelection(self, *args):
        print("reacting on selection %s %s" % (self.probvar.get(), self.trvar.get()))
        self.textoutputframe.setProblem(self.probvar.get())
        self.textoutputframe.setTestrun(self.gui.getTestrun(self.trvar.get()))
        self.textoutputframe.update()

    def update(self):
        self.updateBoxes()

