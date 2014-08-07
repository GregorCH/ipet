'''
Created on 31.01.2014

@author: Customer
'''
from ttk import Frame
import Tkconstants
from Tkconstants import TOP, END
from ScrolledText import ScrolledText
from Tkinter import Menu
from cStringIO import StringIO
import pandas as pd
from pandas import MultiIndex
from functools import partial

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
        self.text.bind('<Button-1>', self.highlightCurrentColumn)
        self.text.bind('<Button-3>', self.openContextMenu)

        self.text.config(bg='white')

        if scrollbar is not None:
#          scrollbar = Scrollbar(master, orient=Tkconstants.HORIZONTAL)
            scrollbar.config(command=self.text.xview)
            self.text.config(xscrollcommand=scrollbar.set)

#       scrollbar.pack(side=TOP, fill=Tkconstants.X)
        self.dataframe = None
        self.colwidths = []

    def reset(self):
        self.text.delete("1.0", END)

    def setDataFrame(self, dataframe):
        '''
        set a dataframe object as the data to be displayed
        '''
        self.dataframe = dataframe
        self.update()

    def analyseDataFrame(self):
        '''
        analyses a data frame object
        '''
        if type(self.dataframe.columns) is MultiIndex:
            self.ncollevels = len(self.dataframe.columns.levels)
        else:
            self.ncollevels = 1


    def update(self):
        '''
        updates view when a new data frame is received
        '''
        self.reset()

        # analyse data frame
        self.analyseDataFrame()

        # mark the leftmost and rightmost element of a column index
        self.colwidths = [(-1, -1)] * len(self.dataframe.columns)

        buf = StringIO(self.dataframe.to_string(sparsify=False))
        for lineidx, line in enumerate(buf.readlines()):
            if not line:
                continue
            if lineidx < self.ncollevels:
                # the line index is the level index
                startidx = 0
                for colidx, elem in enumerate(self.dataframe.columns.get_level_values(lineidx)):
                    firstindex = line.find(" %s" % elem, startidx) + 1
                    if firstindex == 0:
                        raise ValueError("Error: could not find string ' %s' in line %s" % (elem, repr(line[startidx:])))

                    startidx = firstindex + len(elem)
                    leftcolwidth, rightcolwidth = self.colwidths[colidx]
                    self.colwidths[colidx] = (firstindex if leftcolwidth == -1 else min(leftcolwidth, firstindex),
                                              startidx if rightcolwidth == -1 else max(rightcolwidth, startidx))

            else:
                # line is a row of the data frame
                for colidx in xrange(len(self.dataframe.columns)):
                    leftcolwidth, rightcolwidth = self.colwidths[colidx]
                    if leftcolwidth < 0 or rightcolwidth < 0:
                        raise ValueError("Error: Have uninitialized pair of col widths (%d,%d)" % (leftcolwidth, rightcolwidth))
                    while leftcolwidth > 0 and line[leftcolwidth - 1] != " ":
                        leftcolwidth -= 1
                    while rightcolwidth < len(line) - 1 and line[rightcolwidth + 1] not in [" ", "\n"]:
                        rightcolwidth += 1
                    self.colwidths[colidx] = (leftcolwidth, rightcolwidth)

            self.text.insert(END, line)


    def highlightCurrentWord(self, event):
        '''
        highlight word under mouse pointer
        '''
        self.text.tag_remove('hover', 1.0, Tkconstants.END)
        startofword = "%s+1c" % self.text.search(r'\s', Tkconstants.CURRENT, backwards=True, regexp=True)
        endofword = self.text.search(r'\s', Tkconstants.CURRENT, regexp=True)
        self.text.tag_add('hover', startofword, endofword)
        self.text.tag_config('hover', background='gray85')

    def highlightCurrentColumn(self, event):
        self.text.tag_remove('columntag', 1.0, Tkconstants.END)
        currentcolumnindex = self.getCurrentColumnIndex(event)
        if currentcolumnindex == -1:
            return
        if self.dataframe is None:
            return
        left, right = self.colwidths[currentcolumnindex]

        for line in xrange(1, self.dataframe.index.size + self.ncollevels + 1):
            self.text.tag_add('columntag', "%d.%d" % (line, left), "%d.%d" % (line, right))

        self.text.tag_config('columntag', background=self.text.cget('selectbackground'))



    def getCurrentColumnIndex(self, event):
        currentchar = map(int, self.text.index(Tkconstants.INSERT).split('.'))[1]
        print currentchar, self.colwidths
        for idx, elem in enumerate(self.colwidths):
            left = elem[0]
            right = elem[1]
            if right >= currentchar and left <= currentchar:
                return idx
        else:
            return -1

    def sortBy(self, ascending=True, what='column'):
        if what == 'index':
            method = self.dataframe.sort_index
        elif what == 'column':
            idx = self.getCurrentColumnIndex(None)
            if idx != -1:
                method = partial(self.dataframe.sort, columns=self.dataframe.columns[idx])
            else:
                return
        else:
            raise ValueError("ERROR: what == %s, only accept 'index' or 'column'" % what)
        newdataframe = method(ascending=ascending)
        self.setDataFrame(newdataframe)
    def openContextMenu(self, event):
        '''
        open the context menu to interact with the underlying data frame
        '''
        menu = Menu(self, tearoff=0)
        plotmenu = Menu(menu)
        menu.add_command(label='Sort By Column <', command=partial(self.sortBy, ascending=True, what='column'))
        menu.add_command(label='Sort By Column >', command=partial(self.sortBy, ascending=False, what='column'))
        menu.add_command(label='Sort By Index < ', command=partial(self.sortBy, ascending=True, what='index'))
        menu.add_command(label='Sort By Index > ', command=partial(self.sortBy, ascending=False, what='index'))
        plotmenu.add_separator()
        plotmenu.add_command(label='Bar plot')
        plotmenu.add_command(label='Scatter Plot')
        plotmenu.add_command(label='Scatter Matrix')
        menu.add_cascade(label='Data Plots', menu=plotmenu)
        menu.post(event.x, event.y)

