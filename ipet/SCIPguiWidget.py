'''
Created on 08.03.2013

@author: bzfhende
'''
from Tkinter import Frame
from Tkconstants import GROOVE

class SCIPguiWidget(Frame):
   '''
   classdocs
   '''


   def __init__(self, master, gui, **kw):
      Frame.__init__(self, master, bg="white", bd=10, relief=GROOVE, **kw)
      self.gui = gui