'''
Created on 27.03.2013

@author: Gregor Hendel
'''
from Tkinter import Toplevel, Label, Entry, StringVar, Button, Frame
from Tkconstants import LEFT, RIGHT, TOP
from StatisticReader_CustomReader import CustomReader
import Tkconstants
class SCIPreaderWizard(Toplevel):
   def __init__(self, line, linestartidx, gui, activateString=""):

      self.customreader = CustomReader()
      self.allnumbersinline = self.customreader.numericExpression.findall(line)
      self.numbersbeforelinestartidx = self.customreader.numericExpression.findall(line[:linestartidx])
      print self.numbersbeforelinestartidx

      startindexsuggestion = len(self.numbersbeforelinestartidx)
      Toplevel.__init__(self)
      self.wm_title("Create Reader")

      if line.find(':') >= 0:
         regexp = line[:line.find(':')]
      else:
         regexp = line.split()[0]
      self.namevar = StringVar()
      self.namevar.set(activateString.replace(" ","")+'_'+regexp.replace(" ","")+"Reader")
      nameframe = self.createFrame("Name:", self.namevar)
      nameframe.pack(side=TOP, fill=Tkconstants.X, expand=True)

      self.datakeyvar = StringVar()
      self.datakeyvar.set(activateString.replace(" ","")+'_'+regexp.replace(" ",""))
      datakeyframe = self.createFrame("Datakey", self.datakeyvar)
      datakeyframe.pack(side=TOP, fill=Tkconstants.X, expand=True)

      self.activateStringvar = StringVar()
      self.activateStringvar.set(activateString)
      activateStringframe = self.createFrame("Activation", self.activateStringvar)
      activateStringframe.pack(side=TOP, fill=Tkconstants.X, expand=True)

      self.regexpvar = StringVar()
      self.regexpvar.set("^"+line[:line.find(regexp) + len(regexp)])
      regexpframe = self.createFrame("Regular expression", self.regexpvar)
      regexpframe.pack(side=TOP, fill=Tkconstants.X, expand=True)

      self.startindexvar = StringVar()
      self.startindexvar.set(str(startindexsuggestion))
      startindexframe = self.createFrame("Index : ", self.startindexvar)
      startindexframe.pack(side=TOP, fill=Tkconstants.X, expand=True)

      self.defaultvar = StringVar()
      self.defaultvar.set(str(0))
      defaultframe = self.createFrame("default", self.defaultvar)
      defaultframe.pack(side=TOP, fill=Tkconstants.X, expand=True)

      self.datatypevar = StringVar()
      self.datatypevar.set('float')
      datatypeframe = self.createFrame("Data type - (int, float)", self.datatypevar)
      datatypeframe.pack(side=TOP, fill=Tkconstants.X, expand=True)

      buttonframe = Frame(self)
      cancelbutton = Button(buttonframe, text="Cancel", command=self.destroy)
      cancelbutton.pack(side=LEFT)
      createbutton = Button(buttonframe, text="Create Reader", command=self.finish)
      createbutton.pack(side=RIGHT)
      buttonframe.pack(side=TOP)

      w = self.winfo_screenwidth()
      h = self.winfo_screenheight()
      self.geometry("600x300+%d+%d"%((w-400)/2, (h-300)/2))

      self.gui = gui


   def createFrame(self, title, stringvar):
      nameframe = Frame(self)
      namelabel = Label(nameframe, text=title)
      namelabel.pack(side=LEFT)
      nameentry = Entry(nameframe, textvariable=stringvar, bg='white')
      nameentry.pack(side=RIGHT, fill=Tkconstants.X, expand=True)
      return nameframe

   def finish(self):
      self.customreader.activateexpression = self.activateStringvar.get()
      self.customreader.name = self.namevar.get()
      self.customreader.defaultvalue = float(self.defaultvar.get())
      self.customreader.regexp = self.regexpvar.get()
      self.customreader.index = int(self.startindexvar.get())
      self.customreader.datakey = self.datakeyvar.get()
      self.customreader.setDataType(self.datatypevar.get())

      self.gui.addReader(self.customreader)

      self.destroy()

