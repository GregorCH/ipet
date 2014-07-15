'''
Created on 30.04.2013

@author: bzfhende
'''
from SCIPguiWidget import SCIPguiWidget
from SCIPTable import SCIPTable
from Tkconstants import LEFT, X, Y, RIGHT
from ScrolledOutputWidget import ScrolledOutputWidget

class SCIPguiOutputWidget(SCIPguiWidget):
   name = "Output Widget"

   def __init__(self, master, gui, **kw):

      SCIPguiWidget.__init__(self, master, gui, **kw)
#      self.tableframe = SCIPTable(self, 10, gui, bd=5, bg="", width=self.winfo_screenwidth()/10, height=self.winfo_screenheight()/3)
#
#      self.tableframe.pack(side=LEFT, fill=Y)

      textoutputframe = ScrolledOutputWidget(self,self.gui, bd=5, bg="white", width=self.winfo_screenwidth(), height=self.winfo_screenheight()/3)
      textoutputframe.pack(side=RIGHT, expand=1, fill=Y)

#      gui.requestUpdate(self.tableframe)
