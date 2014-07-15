'''
Created on 28.12.2013

@author: bzfhende
'''
from Tkinter import Menu, Toplevel
from IPETBrowser import IPETBrowser
from Tkconstants import BOTH

class IPETManagerMenu(Menu):
   '''
   a manager menu has all manager related actions available
   '''
   def __init__(self, master, manager, cnf={}):
      Menu.__init__(self, master, cnf)
      self.manager = manager
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
