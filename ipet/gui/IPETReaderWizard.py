'''
Created on 27.03.2013

@author: Gregor Hendel
'''
from tkinter import Toplevel, Label, Entry, StringVar, Button, Frame
from tkinter.constants import LEFT, RIGHT, TOP
from ipet.parsing import CustomReader
import tkinter.constants
from ipet.parsing import StatisticReader
from .IPETToolTip import createToolTip
class IpetReaderWizard(Toplevel):
    '''
    form to create a new Reader through the user interface
    '''
    def __init__(self, line, linestartidx, gui, activateString=""):

        self.allnumbersinline = StatisticReader.numericExpression.findall(line)
        self.numbersbeforelinestartidx = StatisticReader.numericExpression.findall(line[:linestartidx])
        print(self.numbersbeforelinestartidx)

        startindexsuggestion = len(self.numbersbeforelinestartidx)
        Toplevel.__init__(self)
        self.wm_title("Create Reader")

        if line.find(':') >= 0:
            regexp = line[:line.find(':')]
        else:
            regexp = line.split()[0]
        self.namevar = StringVar()
        self.namevar.set(regexp.replace(" ", "") + "Reader")
        self.createField("Name:", "Edit the name for this reader; reader names have to be unique", self.namevar, row=0)

        self.datakeyvar = StringVar()
        self.datakeyvar.set(activateString.replace(" ", "") + '_' + regexp.replace(" ", ""))
        self.createField("Datakey:", "Enter the field name under which the data are stored", self.datakeyvar, row=1)

        self.activateStringvar = StringVar()
        self.activateStringvar.set(activateString)
        self.createField("Activation:", "The activation string for this reader, which can be any string of the output. Use '@01' to have the reader activated from" \
                        " the start. Leave empty to have the reader always active)", self.activateStringvar, row=2)

        self.regexpvar = StringVar()
        self.regexpvar.set("^" + line[:line.find(regexp) + len(regexp)])
        self.createField("Line expression:", "Should match the parts of the line, usually the start, where the data are retrieved from", self.regexpvar, row=3)

        self.startindexvar = StringVar()
        self.startindexvar.set(str(startindexsuggestion))
        self.createField("Index: ", "the index of the number to parse, starting from 0", self.startindexvar, row=4)

        self.datatypevar = StringVar()
        self.datatypevar.set('float')
        self.createField("Data type - (int, float):", "Integer or floating point data?", self.datatypevar, row=6)

        buttonframe = Frame(self)
        cancelbutton = Button(buttonframe, text="Cancel", command=self.destroy)
        cancelbutton.pack(side=LEFT)
        createbutton = Button(buttonframe, text="Create Reader", command=self.finish)
        createbutton.pack(side=RIGHT)
        buttonframe.grid(row=7, columnspan=2, pady=7)

        w = self.winfo_screenwidth()
        h = self.winfo_screenheight()
        self.geometry("600x300+%d+%d" % ((w - 400) / 2, (h - 300) / 2))

        self.gui = gui


    def createField(self, title, tooltip, stringvar, row):
        namelabel = Label(self, text=title)
        createToolTip(namelabel, tooltip)
        nameentry = Entry(self, textvariable=stringvar, bg='white', width=75)
        namelabel.grid(row=row, column=0, sticky=tkinter.constants.W, pady=3)
        nameentry.grid(row=row, column=1, pady=3)

    def finish(self):
        customreader = CustomReader(name = self.namevar.get(),
                                    activateexpression=self.activateStringvar.get(),
                                    regpattern=self.regexpvar.get(),
                                    datakey = self.datakeyvar.get(),
                                    index = int(self.startindexvar.get()),
                                    datatype = self.datatypevar.get()
                                    )

        self.gui.addReader(customreader)

        self.destroy()

