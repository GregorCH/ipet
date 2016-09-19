'''
Created on 08.03.2013

@author: bzfhende
'''
from Tkinter import Label, Menu



class SCIPguiSelectionLabel(Label):

   EMPTY = "None"

   def __init__(self, master, alistcommand, avariable, acommand, key=EMPTY, **kw):
      Label.__init__(self, master, textvariable=avariable, **kw)

      avariable.set(key)
      self.v = avariable

      self.listquery = alistcommand
      self.query = acommand
      self.bind("<Button-1>", self.popup)
      self.buttonmenu = None

   def popup(self, event):
      if self.buttonmenu != None:
         self.buttonmenu.destroy()
         self.buttonmenu = None
         return 1
      keylist = self.listquery()[:]
      keylist.insert(0, SCIPguiSelectionLabel.EMPTY)
      keylist.sort()
#
      self.buttonmenu = Menu(self, tearoff=0)
      submenus = {}

      for key in keylist:
         splitkey = key.split('_')
         nlevels = len(splitkey)
         themenutoinsert = self.buttonmenu
         for level in range(1, nlevels):
            menukey = '_'.join(splitkey[:level])
            if not submenus.get(menukey):
               newmenu = Menu(themenutoinsert)
               submenus[menukey] = newmenu
               themenutoinsert.add_cascade(label=menukey, menu=newmenu)
               themenutoinsert = newmenu
            else:
               themenutoinsert = submenus.get(menukey)

         themenutoinsert.add_radiobutton(label=key,
                  variable=self.v, value=key, command=self.query)

      self.buttonmenu.post(event.x_root, event.y_root)

      return 0
