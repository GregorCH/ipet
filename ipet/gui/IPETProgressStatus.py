'''
Created on 13.08.2014

@author: Customer
'''
import tkinter.ttk
from tkinter.ttk import Label, Frame
from tkinter.constants import TOP, X, LEFT
class IpetProgressStatus(Frame):

    def __init__(self, master=None, cnf={}, **kw):
        Frame.__init__(self, master, **kw)
        self.label = Label(self, text="I am idle")
        self.progressbar = tkinter.ttk.Progressbar(self, mode="determinate", length=200)
        self.progressbar.pack(side=LEFT)
        self.label.pack(side=LEFT)
        self.update_step = 0.1

    def setUpdateStep(self, updatestep):
        self.update_step = updatestep

    def start(self, maximum=100):
        self.progressbar.config(maximum=maximum, value=0)
    def stop(self):
        self.progressbar.config(value=self.progressbar.cget('maximum'))

    def update(self, *args):
#        self.progressbar.step(self.update_step)
        self.label.config(text=str(args[0]))
        self.progressbar.config(value=(self.progressbar.cget('value') + 1) % self.progressbar.cget('maximum'))
        self.update_idletasks()
