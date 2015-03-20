'''
Created on 02.04.2013

@author: bzfhende
'''
from IpetWidget import IpetWidget
from Tkinter import StringVar, Scrollbar, Button, Frame, Toplevel, PanedWindow, LabelFrame

import Tkconstants
import pandas as pd

from ttk import Treeview, Separator, Entry
import os
from IPETDataTable import IPETDataTableFrame
from IpetParam import IPETParam
from IPETBrowser import IPETTypeWidget
from Manager import Manager
from ipet.IpetImageButton import IpetImageButton
from functools import partial
import numpy

class IpetTableWidget(IpetWidget):
    '''
    The table widget enables the user to create custom tables of their data
    '''

    EMPTYCOLUMN = ("EMPTY", "EMPTY")
    name = "Table Widget"

    param_maxindexwidth = IPETParam("Maximum index width", 20, [6, 100], 'The maximum index width in characters before truncation')

    def __init__(self, master, gui, **kw):
        '''
        constructs a table widget
        '''
        IpetWidget.__init__(self, master, gui, **kw)
        paned = PanedWindow(self, orient=Tkconstants.VERTICAL)
        scrollbar = Scrollbar(self, orient=Tkconstants.HORIZONTAL)
        self.tableframe = IPETDataTableFrame(paned, scrollbar=scrollbar)
        paned.add(self.tableframe)

        self.aggrframe = IPETDataTableFrame(paned, scrollbar=scrollbar)
        paned.add(self.aggrframe)

        self.exportfilenamevar = StringVar(value='newtable.txt')
        exportframe = Frame(self)
        Button(exportframe, text="Create Table", command=self.openTableCreationFrame).pack(side=Tkconstants.LEFT, padx=2)
        Button(exportframe, text="Export", command=self.export).pack(side=Tkconstants.LEFT, padx=2)
        Entry(exportframe, textvariable=self.exportfilenamevar).pack(side=Tkconstants.LEFT, padx=2)
        Separator(exportframe, orient=Tkconstants.VERTICAL).pack(side=Tkconstants.LEFT, padx=5)
        IpetImageButton(exportframe, "Refresh-icon", "Refresh the data frame", self.update).pack(side=Tkconstants.LEFT, padx=2)
        Separator(exportframe, orient=Tkconstants.VERTICAL).pack(side=Tkconstants.LEFT, padx=5)
        IpetImageButton(exportframe, "arrow-left-icon", "Move selected column left", partial(self.move, where= -1))\
        .pack(side=Tkconstants.LEFT, padx=2)
        IpetImageButton(exportframe, "arrow-right-icon", "Move selected column to the right", partial(self.move, where= +1)).pack(side=Tkconstants.LEFT, padx=2)

        IpetImageButton(exportframe, "sort-ascending-icon", "Sort selected column in ascending order", self.update).pack(side=Tkconstants.LEFT, padx=2)
        IpetImageButton(exportframe, "sort-descending-icon", "Sort selected column in descending order", self.update).pack(side=Tkconstants.LEFT, padx=2)

        self.optionsbutton = Button(exportframe, text="Show Options", command=self.showOptions)
        self.optionsbutton.pack(side=Tkconstants.RIGHT)
        exportframe.pack(side=Tkconstants.TOP, fill=Tkconstants.X)
        paned.pack(side=Tkconstants.TOP, fill=Tkconstants.BOTH, expand=Tkconstants.TRUE)
        scrollbar.pack(side=Tkconstants.TOP, fill=Tkconstants.X, expand=Tkconstants.TRUE)

        # use a manager to manage the parameters
        params = [getattr(IpetTableWidget, name) for name in dir(IpetTableWidget) if name.startswith('param_')]
        self.params = Manager(params)
        self.params.addObserver(self)

        self.selection = [(testrun.getName(), datakey) for testrun in self.gui.getTestrunList(onlyactive=False) \
                          for datakey in ['SolvingTime', 'Nodes']]
        self.update()

    def swapcolumns(self, i, j):
        if self.selection is None or self.df_selection is None:
            return
        size = len(self.df_selection.columns)
        if j < 0 or j >= size or j == i:
            return
        tmp = self.selection[i]
        self.selection[i] = self.selection[j]
        self.selection[j] = tmp
        for window, frame in zip([self.tableframe, self.aggrframe], [self.tableframe.getDataFrame(), self.aggrframe.getDataFrame()]):
            cols = list(frame.columns)
            tmp = cols[i]
            cols[i] = cols[j]
            cols[j] = tmp
            window.setDataFrame(frame[cols])


    def move(self, where= -1):
        currentcol = max(self.tableframe.getCurrentColumnIndex(None), \
                         self.aggrframe.getCurrentColumnIndex(None))
        if currentcol == -1:
            return
        if where == -1 and currentcol > 0:
            self.swapcolumns(currentcol, currentcol - 1)
        elif where == +1 and currentcol <= len(self.df_selection.columns) - 1:
            self.swapcolumns(currentcol, currentcol + 1)




    def update(self, *args):
        '''
        update method called from inside the table creation wizard
        '''
        self.df_selection = None
        self.tableframe.reset()
        self.aggrframe.reset()

        if self.selection == []:
            return

        for dtb in [self.aggrframe, self.tableframe]:
            dtb.setMaxIndexWidth(self.param_maxindexwidth.getValue())

        useshortnames = self.checkShortNames()
        testruns = self.gui.getTestrunList(onlyactive=False)
        dataframes = [testrun.data for testrun in testruns]
        probnames = self.gui.getProblemList(onlyfiltered=False)

        # construct a pandas data frame object to represent the data
        # distinguish between single testruns and multiple testruns
        if len(testruns) > 1:
            theselection = self.selection
            if useshortnames:
                keys = [testrun.getSettings() for testrun in testruns]
                testrunnames = self.gui.getTestrunnames()
                theselection = [(keys[testrunnames.index(run)], key) for run, key in self.selection]
            else:
                keys = self.gui.getTestrunnames()
            largedataframe = pd.concat(dataframes, axis=1, keys=keys)
        elif len(testruns) == 1:
            largedataframe = dataframes[0]
            theselection = [key for run, key in self.selection]
        # use the to_string() method to print the table
        self.df_selection = largedataframe[theselection].loc[probnames]
        self.tableframe.setDataFrame(self.df_selection)

        self.updateAggregation()


    def updateAggregation(self):
        aggregations = self.gui.comparator.getManager('aggregation').getManageables(onlyactive=True)
        self.df_aggr = pd.DataFrame(columns=self.df_selection.columns, index=[aggregation.getName() for aggregation in aggregations])
        print self.df_selection.columns
        for aggregation in aggregations:
            for col in self.df_selection.columns:
                try:
                    aggregatedval = aggregation.aggregate(self.df_selection[col])
                    self.df_aggr[col][aggregation.getName()] = aggregatedval
                except TypeError:
                    pass

        self.aggrframe.setDataFrame(self.df_aggr)


    def checkShortNames(self):
        '''
        are short names , i.e., only the settings of the testruns, sufficient to distinguish the testruns?
        '''
        testruns = self.gui.getTestrunList()
        settings = [testrun.getSettings() for testrun in testruns]
        for setting in settings:
            if settings.count(setting) > 1:
                return False
        return True

    def changeButtonName(self):
        if self.optionsbutton.cget('text') == 'Show Options':
            self.optionsbutton.config(text='Hide Options')
        else:
            self.optionsbutton.config(text='Show Options')
            self.tl.destroy()

    def showOptions(self):
        if self.optionsbutton.cget('text') == 'Show Options':

            buttonheight = self.optionsbutton.winfo_height()
            selfwidth = self.winfo_width()

            self.tl = Toplevel(self)
            for idx, param in enumerate(self.params.getManageables()):
                IPETTypeWidget(self.tl, param.getName(), param, self.params, attribute=param.getValue()).grid(row=idx)
            print "Opening options for Ipet Table Widget"
            self.optionsbutton.config(text='Hide Options')
            width = self.tl.winfo_width()
            height = self.tl.winfo_height()
            xoff = self.winfo_rootx() + selfwidth - width
            yoff = self.winfo_rooty() + buttonheight
            self.tl.geometry("%dx%d+%d+%d" % (width, height, xoff - width / 5, yoff + height / 16))
            self.tl.protocol('WM_DELETE_WINDOW', self.changeButtonName)
            self.tl.mainloop()
        else:
            try:
                self.tl.destroy()
            except AttributeError():
                pass
            self.optionsbutton.config(text='Show Options')


    def export(self):
        '''
        exports the table to the specified file format. The following formats are supported:

        -.tex for a latex compilable tabular
        -.txt for text format
        -.csv for a standard csv-file
        -.html for html-table
        -.xls for a Microsoft Excel parsable output
        '''
        thedf = self.tableframe.getDataFrame()
        if thedf is None:
            return
        # use export file name variable
        filename = self.exportfilenamevar.get()
        extension = os.path.splitext(filename)[1]
        # use the default .txt extension if no extension is specified
        if extension == "":
            extension = ".txt"
            filename = filename + extension
            self.exportfilenamevar.set(filename)

        f = None
        try:
            f = open(filename, 'w')
            f.close()
        except IOError:
            print "Error: File %s could not be opened for writing - check path and writing permissions" % (filename)
            return

        # infer the correct output method from the file extension
        extension = extension[1:]
        replacementdict = dict(tex='latex', xls='excel', xlsx='excel')
        methodname = "to_" + replacementdict.get(extension, extension)
        try:
            exportmethod = getattr(thedf, methodname)
            exportmethod(filename)
            print "Saved Table to file %s" % os.path.abspath(filename)
        except AttributeError:
            print "unknown file extension %s: using to string exportmethod" % (methodname)
            with open(filename, 'w') as f:
                f.write(thedf.to_string())
                print "Saved Table to file %s" % os.path.abspath(filename)


    def openTableCreationFrame(self):
        '''
        open a table creation frame for selecting data
        '''
        frame = TableCreationFrame(self.gui, self)
        frame.mainloop()

class TableCreationFrame(Toplevel):

   def __init__(self, gui, tablewidget, master=None, cnf={}, **kw):
      Toplevel.__init__(self, master=tablewidget, cnf=cnf, **kw)
      self.wm_title("Configure Table")
      w = self.winfo_screenwidth()
      h = self.winfo_screenheight()
      self.geometry("%dx%d+%d+%d" % (w / 2, h / 4 * 3, tablewidget.winfo_rootx() + w / 10, tablewidget.winfo_rooty() + h / 10))
      self.tablewidget = tablewidget
      panedwindow = PanedWindow(self, orient=Tkconstants.VERTICAL)
      panedwindow.pack(expand=True, fill=Tkconstants.BOTH);
      dataselectionframe = LabelFrame(panedwindow, text='Select Data')
      self.createDataSelectionPanel(gui, dataselectionframe)
      panedwindow.add(dataselectionframe)

        #selectionviewpanel = LabelFrame(panedwindow, text='Current Selection')
        #self.createSelectionViewPanel(gui, selectionviewpanel)
        #panedwindow.add(selectionviewpanel)

   def createDataSelectionPanel(self, gui, master):
      panedwindowdsf = PanedWindow(master, orient=Tkconstants.HORIZONTAL)
      panedwindowdsf.pack(expand=True, fill=Tkconstants.BOTH)
      buttonframedfs = Frame(master)
      buttonframedfs.pack(side=Tkconstants.TOP)
      Button(buttonframedfs, text='Add current selection', command=self.selectionAdd).pack(side=Tkconstants.LEFT)
      Button(buttonframedfs, text='Remove current selection', command=self.selectionRemove).pack(side=Tkconstants.LEFT)
      Button(buttonframedfs, text='Reset', command=self.selectionReset).pack(side=Tkconstants.LEFT)
      Separator(master).pack(side=Tkconstants.TOP)

      self.treeviewkeys = Treeview(panedwindowdsf)
      panedwindowdsf.add(self.treeviewkeys)
      datakeys = gui.getAllDatakeys()
      self.fillTreeView(self.treeviewkeys, datakeys)
      self.treeviewtestruns = Treeview(panedwindowdsf)
      panedwindowdsf.add(self.treeviewtestruns)
      for testrunname in gui.getTestrunnames():
         self.treeviewtestruns.insert('', 'end', testrunname, text=testrunname)

   def createSelectionViewPanel(self, gui, master):
      panedwindowsv = PanedWindow(master, orient=Tkconstants.HORIZONTAL)
      panedwindowsv.pack(expand=True, fill=Tkconstants.BOTH)
      buttonframedfs = Frame(master)
      buttonframedfs.pack(side=Tkconstants.TOP)
      Separator(master).pack(side=Tkconstants.TOP)

      self.treeviewcurrselection = Treeview(panedwindowsv)
      panedwindowsv.add(self.treeviewcurrselection)
      optionframe = LabelFrame(panedwindowsv, text='Options for selection')
      panedwindowsv.add(optionframe)

   def fillTreeCurrSelection(self):
      map(self.treeviewcurrselection.delete, self.treeviewcurrselection.get_children())
      lastrun = ''
      for run, key in self.tablewidget.selection:
         if run != lastrun:
            self.treeviewcurrselection.insert('', 'end', run, text=run)
            lastrun = run
         self.treeviewcurrselection.insert(lastrun, 'end', text=key)

   def fillTreeView(self, treeview, datalist):
      '''
      populates a tree view with the content of data list

      hierarchy is defined by underscores -- each underscore defines a new level
      '''
      for key in sorted(datalist):
         splitkey = key.split('_')
         nlevels = len(splitkey)
         for level in range(0, nlevels):
            menukey = '_'.join(splitkey[:level + 1])
            if not treeview.exists(menukey):
               treeview.insert('_'.join(splitkey[:level]), 'end', menukey, text=menukey)

   def getCurrentSelectionList(self):
      return [(testrunname, key) for testrunname in self.treeviewtestruns.selection() \
             for key in self.treeviewkeys.selection()]

   def selectionAdd(self):
      newselection = self.getCurrentSelectionList()
      self.tablewidget.selection += [element for element in newselection if newselection not in self.tablewidget.selection]
      self.update()

   def selectionRemove(self):
      newselection = self.getCurrentSelectionList()
      for sel in newselection:
         while self.tablewidget.selection.count(sel) > 0:
            self.tablewidget.selection.remove(sel)
      self.update()

   def selectionReset(self):
      self.tablewidget.selection = []
      self.update()

   def update(self):
      self.tablewidget.update()
       #self.fillTreeCurrSelection()
