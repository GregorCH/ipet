'''
Created on 31.01.2014

@author: Customer
'''
from ttk import Frame, OptionMenu, Button, Label
import Tkconstants
from Tkconstants import TOP, END
from ScrolledText import ScrolledText
from Tkinter import Menu, Toplevel, StringVar
from cStringIO import StringIO
import numpy as np
from pandas import MultiIndex
from functools import partial
from IPETParam import IPETParam
from IPETPlotWindow import IPETPlotWindow
from IPETBrowser import IPETTypeWidget
from ipet.concepts import Manager

class IPETDataTableFrame(Frame):
    '''
    Frame object to display and interact with DataFrame objects.
    '''

    param_scatter_secondcolumn = IPETParam("Second column (Y-axis)", None, set([None]), "Second column (y-axis) for scatter plot")
    param_histogram_leftbin = IPETParam("Left bin edge", -10.0, [], "Left bin border")
    param_histogram_rightbin = IPETParam("Right bin edge", +10.0, [], "Right bin border")
    param_histogram_binwidth = IPETParam("Bin width", 1.0, [], "The bin width")
    param_histogram_nbins = IPETParam("Bin number", -1, [], "The number of bins")
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
        self.setMaxIndexWidth(20)

    def reset(self):
        self.text.delete("1.0", END)

    def getDataFrame(self):
        '''
        return the current data frame object
        '''
        return self.dataframe

    def setDataFrame(self, dataframe):
        '''
        set a dataframe object as the data to be displayed
        '''
        self.dataframe = dataframe
        self.update()

    def setMaxIndexWidth(self, maxindexwidth):
        '''
        set maximum index width
        '''
        self.maxindexwidth = maxindexwidth

    def analyseDataFrame(self):
        '''
        analyses a data frame object
        '''
        if self.dataframe.index.size == 0:
            return False

        if type(self.dataframe.columns) is MultiIndex:
            self.ncollevels = len(self.dataframe.columns.levels)
        else:
            self.ncollevels = 1

        # determine the number of characters that should be removed from every line if long indices are present
        maximumindexwidth = max(map(len, self.dataframe.index))
        self.ncharsindexremoval = max(0, maximumindexwidth - self.maxindexwidth)

        oldparamval = self.param_scatter_secondcolumn.getValue()
        self.param_scatter_secondcolumn = IPETParam("Second column (Y-axis)", None, set([None] + list(self.dataframe.columns)), "Second column (y-axis) for scatter plot")
        self.param_scatter_secondcolumn.checkAndChange(oldparamval)

        return True

    def update(self):
        '''
        updates view when a new data frame is received
        '''
        self.reset()

        # analyse data frame
        if not self.analyseDataFrame():
            return

        # mark the leftmost and rightmost element of a column index
        self.colwidths = [(-1, -1)] * len(self.dataframe.columns)

        buf = StringIO(self.dataframe.to_string(sparsify=False))

        for lineidx, line in enumerate(buf.readlines()):
            if not line:
                continue
            if self.ncharsindexremoval > 0:
                line = line[:self.maxindexwidth] + line[self.maxindexwidth + self.ncharsindexremoval:]
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

    def showPlot(self, kind='scatter'):
        if self.dataframe is None:
            return
        tl = Toplevel(self, width=self.winfo_width() / 5, height=self.winfo_height() / 10)


        newplotparam = IPETParam("New plot", False, set((True, False)), "Should a new plot be created?")
        if kind == 'scatter':
            param = self.param_scatter_secondcolumn
            tl.title("Choose Second Column")
            var = StringVar(value=str(param.getValue()))

            Label(tl, text="Selected X-Axis:%s" % str(self.dataframe.columns[self.getCurrentColumnIndex(None)])).pack(side=Tkconstants.TOP, fill=Tkconstants.X)
            possiblecolumns = {str(col):col for col in param.getPossibleValues()}
            om = OptionMenu(tl, var, str(param.getValue()), *list(map(str, param.getPossibleValues())))
            om.pack(side=Tkconstants.TOP, fill=Tkconstants.X, expand=True)

        elif kind == 'histogram':
            tl.title("Adjust bin properties")
            paramManager = Manager([getattr(self, paramname) for paramname in dir(self) if paramname.startswith("param_histogram")])
            for param in paramManager.getManageables():
                IPETTypeWidget(tl, param.getName(), param, paramManager, param.getValue()).pack(side=Tkconstants.TOP, fill=Tkconstants.X, expand=True)
        def show():
            newplot = newplotparam.getValue() or not hasattr(self, 'plotwindow')
            if newplot:
                self.plotwindow = IPETPlotWindow(master=self, width=self.winfo_width() / 2, heigth=self.winfo_width() / 2)

            if kind == 'scatter':
                param.checkAndChange(possiblecolumns.get(var.get()))
                if param.getValue() is not None:
                    col = self.dataframe.icol(self.getCurrentColumnIndex(None))
                    ax = self.plotwindow.getAxis()
                    ax.plot(col, self.dataframe[param.getValue()], 'o', alpha=0.7, label="(X)%s - (Y)%s" % (col.name, param.getValue()))

            elif kind == 'histogram':

                # reset in case we don't want to append
                if newplot or not hasattr(self, 'histogramcolumns'):
                    self.histogramcolumns = []
                self.histogramcolumns.append(self.dataframe.columns[self.getCurrentColumnIndex(None)])

                leftbin, rightbin, binwidth, nbins = map(IPETParam.getValue, [self.param_histogram_leftbin, self.param_histogram_rightbin, self.param_histogram_binwidth, self.param_histogram_nbins])
                if nbins <= 0:
                    bins = np.arange(leftbin, rightbin, step=binwidth)
                else:
                    bins = np.linspace(leftbin, rightbin, nbins + 1, endpoint=True)
                print "self.dataframe[self.histogramcolumns] = %s" % self.dataframe[self.histogramcolumns]
                data = [self.dataframe[col] for col in self.histogramcolumns]
                self.plotwindow.resetAxis()
                self.plotwindow.a.hist(data, bins=bins, label=self.histogramcolumns, alpha=0.7)

            tl.destroy()
            self.plotwindow.getAxis().legend()
            self.plotwindow.canvas.draw()
            self.plotwindow.lift()
            self.plotwindow.mainloop()

        if not hasattr(self, 'plotwindow'):
            newplotparam.checkAndChange(True)
        IPETTypeWidget(tl, newplotparam.getName(), newplotparam, Manager([newplotparam]), newplotparam.getValue()).pack(side=Tkconstants.TOP)
        buttonFrame = Frame(tl)
        buttonyes = Button(buttonFrame, text='OK', command=show)
        buttonno = Button(buttonFrame, text='Cancel', command=tl.destroy)
        buttonyes.pack(side=Tkconstants.LEFT)
        buttonno.pack(side=Tkconstants.LEFT)
        buttonFrame.pack(side=Tkconstants.TOP, fill=Tkconstants.X, expand=True)
        tl.mainloop()

    def openContextMenu(self, event):
        '''
        open the context contextmenu to interact with the underlying data frame
        '''
        try:
            self.contextmenu.destroy()
        except:
            pass

        self.contextmenu = contextmenu = Menu(self, tearoff=0)
        plotmenu = Menu(contextmenu)
        contextmenu.add_command(label='Sort By Column <<', command=partial(self.sortBy, ascending=True, what='column'))
        contextmenu.add_command(label='Sort By Column >>', command=partial(self.sortBy, ascending=False, what='column'))
        contextmenu.add_command(label='Sort By Index <<', command=partial(self.sortBy, ascending=True, what='index'))
        contextmenu.add_command(label='Sort By Index >> ', command=partial(self.sortBy, ascending=False, what='index'))
        contextmenu.add_separator()
        plotmenu.add_command(label='Bar plot')
        plotmenu.add_command(label='Scatter Plot', command=partial(self.showPlot, kind='scatter'))
        plotmenu.add_command(label='Scatter Matrix')
        plotmenu.add_command(label='Histogram', command=partial(self.showPlot, kind='histogram'))
        contextmenu.add_cascade(label='Data Plots', menu=plotmenu)
        contextmenu.post(event.x + self.winfo_rootx(), event.y + self.winfo_rooty())

