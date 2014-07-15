'''
Created on 25.12.2013

@author: bzfhende
'''
from ttk import Treeview, Frame, Panedwindow, Labelframe, Checkbutton, LabelFrame, Entry, Button, Label, PanedWindow
from Tkconstants import VERTICAL, BOTH, TRUE, END, HORIZONTAL, LEFT, TOP
from ScrolledText import ScrolledText
from Manager import Manager
from Tkinter import Tk, IntVar, StringVar
from Comparator import Comparator
import Tkconstants
import tkFont
class IPETTreeview(Frame):
   '''
   a treeview allows for browsing and custom selection of items from a manager object
   '''

   def __init__(self, master, manager, **kw):
      '''
      constructs a vertical tree view of the manager objects in string representation
      '''
      Frame.__init__(self, master, **kw);
      self.manager = manager
      self.manager.addObserver(self)

      buttonframe = Frame(self)
      buttons = self.createButtons(buttonframe)
      for button in buttons:
         button.pack(side=LEFT)
      buttonframe.pack(side=TOP, fill=Tkconstants.X)

      self.treeview = Treeview(self)
      self.treeview.pack(side=TOP)
      self.fill()

   def fill(self, splitonkey='_', split=True):
      '''
      fill the tree view
      '''
      print "active: ", map(self.manager.getStringRepresentation, self.manager.getActiveSet())
      sortedkeys = sorted(self.manager.getAllRepresentations())
      for key in sortedkeys:
         print key, self.manager.isActive(self.manager.getManageable(key))
         if self.manager.isActive(self.manager.getManageable(key)):
            tag = 'active'
         else:
            tag = 'inactive'

         if key.split:
            splitkey = key.split(splitonkey)
            nlevels = len(splitkey)
            for level in range(0, nlevels):
               menukey = splitonkey.join(splitkey[:level + 1])
               if not self.treeview.exists(menukey):
                  self.treeview.insert(splitonkey.join(splitkey[:level]), 'end', menukey, text=menukey, tags=tag)
         else:
            if not self.treeview.exists(key):
               self.treeview.insert(splitonkey.join(splitkey[:level]), 'end', key, text=key, tags=tag)

         self.treeview.tag_configure('active', background='white')
         self.treeview.tag_configure('inactive', background='red')

   def quit(self):
      print 'deleting'
      self.manager.removeObserver(self)
      self.destroy()

   def getSelection(self):
      '''
      get the tree views current selection
      '''
      return self.treeview.selection()

   def update(self, manager):
      map(self.treeview.delete, self.treeview.get_children())
      self.fill()

   def createButtons(self, master):
         return [Button(master, text='Activate', command=self.activateSelection),
                 Button(master, text='Deactivate', command=self.deactivateSelection)]

   def activateSelection(self):
      '''
      activates the current selection
      '''
      manageables = map(self.manager.getManageable, self.getSelection())
      self.manager.activate(manageables)

   def deactivateSelection(self):
      '''
      deactivates the current selection
      '''
      manageables = map(self.manager.getManageable, self.getSelection())
      self.manager.deactivate(manageables)


class IPETObjectRepresentation(Labelframe):
   '''
   an object representation displays and edits all editable attributes of an object
   '''
   EMPTYREPRESENTATION = "No object to display"
   EMPTYDOCUMENTATION = "No documentation available for this object"
   maxrows = 4
   def __init__(self, master, **kw):
      Labelframe.__init__(self, master, **kw)
      self.reset(text=self.EMPTYREPRESENTATION)

   def displayObject(self, manager, managedobject):
      '''
      displays the object representation by showing the objects documentation to browse and
      its editable attributes
      '''
      self.reset()
      self.config(text=manager.getStringRepresentation(managedobject))
      try:
         attributes = managedobject.getEditableAttributes()
      except AttributeError:
         self.reset(text="No editable attributes defined for object %s" % (manager.getStringRepresentation(managedobject)))
         return

      for number, attributename in enumerate(attributes):
         widget = IPETTypeWidget(self.upperpart, attributename, managedobject, manager)
         widget.grid(row=int(number / self.maxrows), column=number % self.maxrows)
      if managedobject.__doc__ != None:
         self.lowerpart.insert(END, managedobject.__doc__)
      else:
         self.lowerpart.insert(END, self.EMPTYDOCUMENTATION)

   def reset(self, text=""):
      if hasattr(self, 'content'):

         self.content.destroy()
      self.content = PanedWindow(self, orient=VERTICAL)
      self.upperpart = Frame(self.content)
      self.lowerpart = ScrolledText(self.content)
      self.content.add(self.upperpart)
      self.content.add(self.lowerpart)
      self.content.pack(expand=TRUE, fill=BOTH)
      if text != "":
         self.lowerpart.insert(END, text)

class IPETTypeWidget(Frame):
   '''
   type dependent widget to allow interaction and updating of string, float, integer, boolean, regular expression
   and managed lists
   '''
   conversionmap = {float:str}
   def __init__(self, master, attributename, objecttoedit, manager, attribute=None, **kw):
      Frame.__init__(self, master, **kw)

      self.objecttoedit = objecttoedit
      self.attributename = attributename
      self.manager = manager
      if attribute is None:
         attribute = getattr(self.objecttoedit, self.attributename)

      if type(attribute) is bool:
         self.var = IntVar()
         # bools get checkboxes.
         Checkbutton(self, text=attributename, variable=self.var, command=self.commandTypeSafe).pack()

      elif type(attribute) is str:
         # string elements get an entry
         self.var = StringVar()
         self.createCompositeEditWidget(attributename)
      elif type(attribute) is int:
         self.var = IntVar()
         self.createCompositeEditWidget(attributename)
      elif type(attribute) is float:
         self.var = StringVar()
         self.createCompositeEditWidget(attributename)
      elif type(attribute) is list:
         manager = Manager(listofmanageables=attribute)
         IPETTreeview(self, manager).pack()

      self.setVariableValue(attribute)

   def convertAttribute(self, attribute):
      '''
      convert an attribute for the variable representation
      '''
      t = type(attribute)
      convert = self.conversionmap.get(t)
      if convert is not None:
         return convert(attribute)
      else:
         return attribute

   def setVariableValue(self, attribute):
      if hasattr(self, 'var'):
         self.var.set(value=self.convertAttribute(attribute))
      self.currattribute = attribute

   def commandTypeSafe(self):
      '''
      evaluates an expression and ensures type safety, e.g., floats remain floats and are not turned to
      strings
      '''
      newattribute = self.var.get()
      if type(self.currattribute) is not type(newattribute):
         try:
            # try a conversion
            newattribute = type(self.currattribute)(self.var.get())
         except ValueError:
            # if the conversion did not work,
            self.setVariableValue(self.currattribute)
            return
      # new attribute is safe for type conversion
      self.setVariableValue(newattribute)
      self.manager.editObjectAttribute(self.objecttoedit, self.attributename, newattribute)


   def getVariable(self):
      '''
      returns this widgets variable
      '''
      return self.var

   def createCompositeEditWidget(self, attributename):
      labelframe = LabelFrame(self, text=attributename)
      Entry(labelframe, textvariable=self.var, validate="focusout", validatecommand=self.commandTypeSafe).pack(side=LEFT)
      Button(labelframe, text="Go", command=self.commandTypeSafe).pack(side=LEFT)
      labelframe.pack()

class IPETBrowser(Frame):
   '''
   a browser allows to access and watch all objects of a managed type, e.g., readers, filters, testruns, data keys
   '''
   def __init__(self, master, manager, **kw):
      '''
      construct a new browser as child of master
      '''
      Frame.__init__(self, master, **kw)
      self.manager = manager
      self.panedwindow = Panedwindow(self, orient=HORIZONTAL);
      self.treeview = IPETTreeview(self.panedwindow, manager)
      self.panedwindow.add(self.treeview)

      self.objectrepresentation = IPETObjectRepresentation(self.panedwindow)
      self.panedwindow.add(self.objectrepresentation)
      self.panedwindow.pack(fill=BOTH, expand=TRUE)
      self.treeview.treeview.bind("<Double-Button-1>", self.updateObject)

   def quit(self):
      self.treeview.quit()
      self.destroy()

   def updateObject(self, event):
      '''
      every selection of an object yields an update of the object representation
      '''
      selection = self.treeview.getSelection()[0]
      print selection
      selectedobject = self.manager.getManageable(selection)
      if selectedobject is not None:
         self.objectrepresentation.displayObject(self.manager, selectedobject)
      else:
         self.objectrepresentation.reset(text=IPETObjectRepresentation.EMPTYREPRESENTATION)

# testing method
if __name__ == '__main__':
   root = Tk()
   comp = Comparator()
   manager = Manager(listofmanageables=comp.datacollector.listofreaders)
   browser = IPETBrowser(root, manager, height=root.winfo_screenheight(), width=root.winfo_screenwidth())
   browser.pack(expand=TRUE, fill=Tkconstants.BOTH)
   root.mainloop()
