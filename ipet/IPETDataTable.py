'''
Created on 31.01.2014

@author: Customer
'''
from ttk import Frame, Scrollbar
import Tkconstants
from Tkconstants import TOP, END
from ScrolledText import ScrolledText
from Tkinter import Menu
class IPETDataTableFrame(Frame):
   '''
   Frame object to display and interact with DataFrame objects.
   '''
   def __init__(self, master=None, scrollbar=None, **kw):
      '''
      constructs a Data Table Frame with no data
      
      pass a scrollbar to make horizontal scrolling possible
      '''
      Frame.__init__(self, master=master, **kw)

      self.text = ScrolledText(self, wrap=Tkconstants.NONE)
      self.text.pack(side=TOP, expand=1, fill=Tkconstants.BOTH)
      self.text.bind('<Motion>', self.highlightCurrentWord)
      self.text.bind('<Button-3>', self.openContextMenu)

      self.text.config(bg='white')

      if scrollbar is not None:
#         scrollbar = Scrollbar(master, orient=Tkconstants.HORIZONTAL)
         scrollbar.config(command=self.text.xview)
         self.text.config(xscrollcommand=scrollbar.set)

#      scrollbar.pack(side=TOP, fill=Tkconstants.X)
      self.dataframe = None

   def reset(self):
      self.text.delete("1.0", END)

   def setDataFrame(self, dataframe):
      '''
      set a dataframe object as the data to be displayed
      '''
      self.dataframe = dataframe
      self.update()

   def update(self):
      '''
      updates view when a new data frame is received
      '''
      self.reset()
      self.text.insert(END, self.dataframe.to_string())

   def highlightCurrentWord(self, event):
      '''
      highlight word under mouse pointer
      '''
      self.text.tag_remove('hover', 1.0, Tkconstants.END)
      startofword = "%s+1c" % self.text.search(r'\s', Tkconstants.CURRENT, backwards=True, regexp=True)
      endofword = self.text.search(r'\s', Tkconstants.CURRENT, regexp=True)
      self.text.tag_add('hover', startofword, endofword)
      self.text.tag_config('hover', background='gray85')

   def openContextMenu(self, event):
      '''
      open the context menu to interact with the underlying data frame
      '''
      menu = Menu(self, tearoff=0)
      plotmenu = Menu(menu)
      plotmenu.add_command(label='Bar plot')
      plotmenu.add_command(label='Scatter Plot')
      plotmenu.add_command(label='Scatter Matrix')
      menu.add_cascade(label='Data Plots', menu=plotmenu)
      menu.post(event.x, event.y)
