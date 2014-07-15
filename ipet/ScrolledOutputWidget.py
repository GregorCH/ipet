'''
Created on 12.03.2013

@author: bzfhende
'''
from Tkinter import Frame, IntVar, Checkbutton, Button
from ScrolledText import ScrolledText
from Tkconstants import END, BOTH, LEFT, SEL_FIRST, SEL_LAST, CURRENT, SEL, RIGHT, Y
from SCIPreaderWizard import SCIPreaderWizard

class ScrolledOutputWidget(Frame):
   '''
   classdocs
   '''

   def __init__(self, master, gui, **kw):
      '''
      Constructor
      '''
      Frame.__init__(self, master, **kw)
      self.gui = gui

      self.scrolledText = ScrolledText(self, bg="white", width = self.winfo_screenwidth())

      self.scrolledText.pack(expand=1, fill=Y)

      self.statsVar = IntVar()
      self.outputVar = IntVar()
      self.statsVar.set(1)
      self.outputVar.set(1)

      bottomframe = Frame(self)
      checkboxstats = Checkbutton(bottomframe, text="Display statistics", variable=self.statsVar, command=self.update)
      checkboxoutput = Checkbutton(bottomframe, text="Display output", variable=self.outputVar, command=self.update)
      checkboxstats.pack(side=LEFT)
      checkboxoutput.pack(side=LEFT)
      createReaderButton = Button(bottomframe, text="Open Reader Wizard", command=self.openReaderWizard)
      createReaderButton.pack(side=RIGHT)
      bottomframe.pack()

      self.headlinesToSuppress = []
      self.tagnametexts = {}

      self.gui.requestUpdate(self)
      self.update()

   def update(self):

      rightProblem = False

      self.scrolledText.delete(1.0, END)
      try:
         f = open(self.gui.selected_testrun.filenames[0], 'r')
      except:
         return

      self.inOutput = False
      self.inStatistics = False
      self.lastheadline = ""
      currentlineno = 0
      self.buttons = {}
      thetag = ''
      self.headlines = []

      for line in f:
         if not rightProblem and line.startswith('@01') and self.gui.selected_problem in line:
            rightProblem = True
            self.inOutput = True
         if rightProblem and "SCIP Status        :" in line:
            self.inOutput = False
            self.inStatistics = True
         if rightProblem and self.lineShouldBePrinted(line):
            self.scrolledText.insert(END, line)
            currentlineno += 1
            if self.inStatistics and self.lineIsHeadline(line):
               self.headlines.append(self.getHeadlineString(line))
               thetag = self.headlines[-1]
               self.buttons[thetag] = Button(self.scrolledText, text='-', command=self.buttonaction)
               self.scrolledText.window_create('%d.0'%currentlineno, window=self.buttons[thetag])

            elif self.inStatistics:
               self.scrolledText.insert('%d.0'%currentlineno, " ")
               self.scrolledText.tag_add(thetag, '%d.0'%currentlineno, '%d.end'%currentlineno)

         if rightProblem and "=ready=" in line:
            rightProblem = False
            f.close()
            break
      self.inStatistics = False
      self.inOutput = False

   def lineShouldBePrinted(self, line):
      if self.inOutput and self.outputVar.get():
         return True
      if self.inStatistics and self.statsVar.get():
         return True
      return False
   def lineIsHeadline(self, line):
      return not line.startswith(" ") and ':' in line

   def getHeadlineString(self, line):
      assert self.lineIsHeadline(line)
      return line[:line.find(':')]

   def removeText(self, tagname):
      self.tagnametexts[tagname] = self.scrolledText.get('%s.first'%tagname, '%s.last'%tagname)
      self.scrolledText.delete('%s.first'%tagname, '%s.last'%tagname)

   def showText(self, tagname):

      self.scrolledText.insert('%s+1line'%CURRENT, self.tagnametexts[tagname])
      self.scrolledText.tag_add(tagname, '%s+1line'%CURRENT, '%s+1line+%dc'%(CURRENT, len(self.tagnametexts[tagname])))

   def buttonaction(self):
      lineidx = map(int, self.scrolledText.index(CURRENT).split('.'))[0]
      line = self.scrolledText.get(CURRENT, '%d.end'%lineidx)
      assert self.lineIsHeadline(line)
      self.elidetaggedtext(self.getHeadlineString(line))
   def elidetaggedtext(self, tagname):
      if tagname in self.headlinesToSuppress:
         self.headlinesToSuppress.remove(tagname)
         self.buttons[tagname].config(text='-')
         self.showText(tagname)
      else:
         self.buttons[tagname].config(text='+')
         self.headlinesToSuppress.append(tagname)
         self.removeText(tagname)

   def openReaderWizard(self):
      lineidx = map(int, self.scrolledText.index(SEL_FIRST).split('.'))[0]
      colstartidx = map(int, self.scrolledText.index(SEL_FIRST).split('.'))[1]
      colidx = 0
      if len(self.scrolledText.tag_names(SEL_FIRST)) > 1:
         tagname = self.scrolledText.tag_names(SEL_FIRST)[-1]
         colidx = 1
      else:
         tagname = "@01"
      line = self.scrolledText.get("%d.%d"%(lineidx, colidx), "%d.end"%lineidx)
      window = SCIPreaderWizard(line, colstartidx - 1, self.gui, tagname)

      window.mainloop()
