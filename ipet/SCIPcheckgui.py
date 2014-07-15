'''
Created on 06.03.2013

@author: bzfhende
'''
from Tkinter import Tk, Listbox, Menu
from Comparator import Comparator
#from SCIPguiScatterWidget import SCIPguiScatterWidget
from Tkconstants import BOTH, TOP, LEFT, RIGHT, VERTICAL, END
#from SCIPguiPbHistoryWidget import SCIPguiPbHistoryWidget
from SCIPguiTableWidget import SCIPguiTableWidget
from TestRun import TestRun
import ttk
from SCIPguiOutputWidget import SCIPguiOutputWidget
import tkFileDialog
from IPETManagerMenu import IPETManagerMenu
from ttk import Frame, Label, Button, Scrollbar
import Tkconstants
from SCIPguiPbHistoryWidget import SCIPguiPbHistoryWidget
from SCIPguiScatterWidget import SCIPguiScatterWidget

class SCIPGui(Tk):
   DEFAULT_BORDERWIDTH = 15

   selected_problem = ''
   selected_testrun = None
   comparator = None

   listboxlistmap = {}
   listToActionDict = {}
   updatableWidgets = []

   TITLE = "IPET- Interactive Python Evaluation Tools"



   def __init__(self, comparator=None, show=True):
      '''
      initializes a SCIPGui. Pass an existing comparator or None to make the GUI create a new, empty
      comparator instance
      '''
      Tk.__init__(self)
      self.wm_title(SCIPGui.TITLE)

      self.topframe = Frame(self, width=self.winfo_screenwidth() / 10, height=self.winfo_screenheight())
      self.topframe.pack(side=LEFT, fill=Tkconstants.Y)

      frameforselection = Frame(self.topframe, width=200)
      Label(frameforselection, text="Current Selection:").pack(side=TOP, fill=Tkconstants.X)
      self.selectedProbLabel = Label(frameforselection)
      self.selectedTestrunLabel = Label(frameforselection, justify=RIGHT)

      self.selectedProbLabel.pack(side=TOP, fill=Tkconstants.X)
      self.selectedTestrunLabel.pack(side=TOP, fill=Tkconstants.X)
      frameforselection.pack(side=TOP)

      problemslabel = Label(self.topframe, text="Problem: ")
      problemslabel.pack(side=TOP)

      probnamesselectionframe, self.probnamesbox = self.listmakeBoxWithScrollbar(self.topframe, self.getProblemList(), self.setSelectedProblem, theheight=35)
      testrunlistboxframe, self.testrunsbox = self.listmakeBoxWithScrollbar(self.topframe, self.getTestrunnames(), self.setSelectedTestrun)
      probnamesselectionframe.pack(side=TOP, fill=Tkconstants.X)

      testrunlabel = Label(self.topframe, text="Testrun: ")
      testrunlabel.pack(side=TOP)

      testrunlistboxframe.pack(side=TOP, fill=Tkconstants.X)

      recollectDataButton = Button(self.topframe, text="Collect data", command=self.reCollectData)
      recollectDataButton.pack(side=TOP)

      # make the remaining window show a tabbed panel with the different widgets
      widgets = [SCIPguiTableWidget, SCIPguiOutputWidget, SCIPguiScatterWidget]
      tabbedFrame = ttk.Notebook(self, height=self.winfo_screenheight())

      for widget in widgets:
         tabbedFrame.add(widget(tabbedFrame, self, width=180, height=180), text=widget.name)

      tabbedFrame.pack(side=LEFT, fill=BOTH, expand=1)

      self.setComparator(comparator)

      self.setupMenu()

      if show:
         self.mainloop()

   def listmakeBoxWithScrollbar(self, master, alist, guiupdatefunction, theheight=5):
      frame = Frame(master)
      scrollbar = Scrollbar(frame, orient=VERTICAL)
      listbox = Listbox(frame, height=theheight, bg='white', yscrollcommand=scrollbar.set)
      scrollbar.config(command=listbox.yview)
      scrollbar.pack(side=RIGHT, fill=Tkconstants.Y)
      listbox.guiupdatefunction = guiupdatefunction
      self.updatelistbox(listbox, alist)
      listbox.pack(side=LEFT, fill=BOTH, expand=1)
      listbox.bind("<Double-Button-1>", self.handleClickEventListbox)

      return frame, listbox

   def updatelistbox(self, listbox, alist):

      if alist == []:
         self.listboxlistmap[listbox] = []
         listbox.delete(0, END)
         return
      newelems = [elem for elem in alist if not elem in self.listboxlistmap.get(listbox, [])]
      if newelems == []:
         return

      listbox.delete(0, END)
      self.listboxlistmap[listbox] = alist
      for item in self.listboxlistmap[listbox]:
         listbox.insert(END, item)

   def updateGui(self):
      for widget in self.updatableWidgets:
         widget.update()

      self.updatelistbox(self.probnamesbox, self.getProblemList())
      self.updatelistbox(self.testrunsbox, self.getTestrunnames())
      if not self.selected_problem is None:
         self.selectedProbLabel.config(text=self.selected_problem)
      else:
         self.selectedProbLabel.config(text="No Problem selected")
      if not self.selected_testrun is None:
         self.selectedTestrunLabel.config(text=self.selected_testrun.getIdentification())
      else:
         self.selectedTestrunLabel.config(text="No Testrun selected")


   def setSelectedProblem(self, idx):
      self.selected_problem = self.getProblemList()[idx]
   def setSelectedTestrun(self, idx):
      self.selected_testrun = self.getTestrunList()[idx]

   def getTestrun(self, identification):
      try:
         return [e for e in self.getTestrunList() if TestRun.getIdentification(e) == identification][0]
      except IndexError:
         print "Error : No such testrun exists: ", identification
         return None

   def requestUpdate(self, widget):
      if not widget in self.updatableWidgets:
         self.updatableWidgets.append(widget)

   def getAllDatakeys(self):
      try:
         return self.comparator.getDatakeys()
      except:
         return []

   def getTestrunnames(self):
      return map(TestRun.getIdentification, self.getTestrunList())

   def getProblemList(self, onlyfiltered=False):
      '''
      returns a list of problems which may have been filtered first through the list of active
      comparator filters
      '''
      try:
         probnamelist = self.comparator.probnamelist
         if onlyfiltered:
            filters = self.comparator.getManager('filter').getManageables(onlyactive=True)
            testruns = self.getTestrunList(onlyactive=True)
            for filterelem in filters:
               probnamelist = filterelem.getFilteredList(probnamelist, testruns)
         return sorted(probnamelist)
      except AttributeError:
         return []
   def getTestrunList(self, onlyactive=True):
      try:
         return self.comparator.getManager('testrun').getManageables(onlyactive)
      except AttributeError:
         return []

   def addReader(self, reader):
      self.comparator.addReader(reader)

   def reCollectData(self):
      self.comparator.collectData()
      self.updateGui()

   def handleClickEventListbox(self, event):
      idx = int(event.widget.curselection()[0])
      action = event.widget.guiupdatefunction
      action(idx)
      self.updateGui()

   def setupMenu(self):
      self.menu = Menu(self)
      self.config(menu=self.menu)
      compMenu = Menu(self.menu)
      self.menu.add_cascade(menu=compMenu, label="Comparator")
      compMenu.add_command(label="New", command=self.resetComparator)
      compMenu.add_command(label="Save", command=self.saveComparator)
      compMenu.add_command(label="Load", command=self.loadComparator)
      compMenu.add_separator()
      compMenu.add_command(label=" Add Log Files", command=self.addLogFiles)
      compMenu.add_command(label=" Add Solu Files", command=self.addSolufiles)
      compMenu.add_separator()
      compMenu.add_command(label=" Recollect Data", command=self.reCollectData)

      if self.comparator is not None:
         for managername, manager in self.comparator.getManagers().iteritems():
            managermenu = IPETManagerMenu(self.menu, manager)
            self.menu.add_cascade(menu=managermenu, label=managername.capitalize())

      self.file_opt = options = {}
      options['defaultextension'] = '.*'
      options['filetypes'] = [('all files', '.*'), ('out-files', '.out'), ('Comparator files', '.cmp'), ('Solu Files', '.solu')]

   def loadComparator(self):
      self.file_opt['defaultextension'] = '.cmp'
      filename = tkFileDialog.askopenfilename(**self.file_opt)
      if filename:
         compy = self.comparator.loadFromFile(filename)
         if not compy is None:
            self.setComparator(compy)

   def saveComparator(self):
      self.file_opt['defaultextension'] = '.cmp'
      filename = tkFileDialog.asksaveasfilename(**self.file_opt)
      if filename:
         self.comparator.saveToFile(filename)

   def resetComparator(self):
      self.setComparator(None)

   def setComparator(self, comparator):
      if comparator is not None:
         self.comparator = comparator
      else:
         self.comparator = Comparator()
      try:
         self.selected_testrun = self.comparator.testruns[0]
         self.selected_problem = self.comparator.probnamelist[0]
      except:
         self.selected_testrun = None
         self.selected_problem = None
      print "Problem list", self.getProblemList()
      print "Testruns;", self.getTestrunnames()
      if hasattr(self, 'menu'):
         del self.menu
      self.setupMenu()
      self.updateGui()

   def addLogFiles(self):
      self.file_opt['defaultextension'] = '.out'
      filenames = tkFileDialog.askopenfilenames(**self.file_opt)
      print filenames
      for filename in filenames:
         if filename:
            self.comparator.addLogFile(filename)

      self.updatelistbox(self.testrunsbox, self.getTestrunnames())

   def addSolufiles(self):
      self.file_opt['defaultextension'] = '.solu'
      filenames = tkFileDialog.askopenfilenames(**self.file_opt)
      print filenames
      for filename in filenames:
         if filename:
            self.comparator.addSoluFile(filename)

if __name__ == '__main__':
   pass
