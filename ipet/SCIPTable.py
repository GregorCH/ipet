'''
Created on 08.03.2013

@author: bzfhende
'''
from TableEntry import TableEntry
from Tkinter import Frame

class SCIPTable(Frame):
   '''
   classdocs
   '''


   def __init__(self, master, nEntries, gui, cnf={}, **kw):
      '''
      Constructor
      '''
      Frame.__init__(self, master, kw)
#      self.toplabelvar = StringVar()
#      self.updateTopLabel(gui)
      self.gui = gui
#      self.toplabel = Label(self, textvariable=self.toplabelvar,width=50, font=('Times', '12'), borderwidth=10, relief=GROOVE)
#      self.toplabel.pack(fill=BOTH)
      self.tframes=[]
      for i in range(nEntries):
         tframe = TableEntry(self, gui)
         tframe.pack()
         self.tframes.append(tframe)
         
   def update(self):
      for tframe in self.tframes:
         tframe.update()
#   def updateTopLabel(self, gui):
#      self.toplabelvar.set(gui.selected_problem + "   " + gui.selected_testrun.getIdentification())

