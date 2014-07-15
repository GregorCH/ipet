'''
Created on 07.03.2013

@author: bzfhende
'''
from Tkinter import Frame, StringVar, Radiobutton, Label, Scrollbar, Menu
from Tkconstants import LEFT, RIGHT, END, W, GROOVE, SUNKEN, VERTICAL
from SCIPguiSelectionLabel import SCIPguiSelectionLabel

class TableEntry(Frame):
   '''
   classdocs
   '''

   EMPTY="None"
   def __init__(self, master, gui, key=EMPTY):
      '''
      Constructor
      '''
      Frame.__init__(self, master, borderwidth=10, relief=GROOVE)

      self.v = StringVar()
      self.v.set(key)

      self.selectionlabel=SCIPguiSelectionLabel(self, gui.getAllDatakeys, self.v, self.query, width=30)
      self.selectionlabel.pack()
      self.gui = gui

      self.textvar = StringVar()
      self.text = Label(self, textvariable=self.textvar, width=30, bg="white")
      self.query()

      self.text.pack()

   def update(self):
      self.query()

   def query(self):
      if self.v.get() != TableEntry.EMPTY:
         self.textvar.set(self.gui.selected_testrun.problemGetData(self.gui.selected_problem, self.v.get()))
      else:
         self.textvar.set("")