'''
Created on 08.03.2013

@author: bzfhende

The PbHistoryWidget features methods to visualize the history of primal and dual bound events of multiple testruns.
Testruns can be activated/dectivated. The normalization can be chosen (no normalization (values on the real primal
and dual scale) or Cplex Gap)
'''
from .IPETWidget import IpetWidget
from tkinter import IntVar, Checkbutton, Toplevel, Button, StringVar
from tkinter.constants import BOTH, TOP, HORIZONTAL
import matplotlib
matplotlib.use('TkAgg')
import numpy
from matplotlib.pyplot import cm
import matplotlib.pylab as plt
from ipet import misc
from tkinter.ttk import Panedwindow, LabelFrame, Treeview, Frame, OptionMenu, Label
import tkinter.constants
from .IPETParam import IPETParam
from ipet.parsing import PrimalBoundHistoryReader, DualBoundHistoryReader, PrimalBoundReader, DualBoundReader
from .IPETBrowser import IPETTypeWidget
from ipet.concepts import Manager
from .IPETPlotWindow import IPETPlotFrame

class IPETBoundHistoryWidget(IpetWidget):

    '''
    classdocs
    '''
    name = "Primal Gap History"
    ALLPROBLEMS = "ALL"
    default_cmap = 'spectral'
    
    param_normalization = IPETParam("Use normalization", True, set([True, False]), 'Should normalization be used for the history?');
    param_dualboundhistory = IPETParam("Show dual bound", True, set([True, False]), 'Should the dual bound history be plotted?');
    param_ylabel = IPETParam("Y Label", "Gap over time", [], 'Y axis description')
    param_xlabel = IPETParam("X Label", "Time (sec.)", [], 'X axis description')
    
    def __init__(self, master, gui, **kw):
        '''
        Constructor of Pb History widget
        - master is the Tk container frame for the widget
        - gui is the central gui instance to retrieve data and events from
        '''
        IpetWidget.__init__(self, master, gui, **kw)
        
        self.boolVars = {}
        self.buttons = {}
        
        self.gui.requestUpdate(self)
        
        self.pw = IPETPlotFrame(self)
        
        self.a = self.pw.getAxis()
        self.navpanel = Frame(self, width=self.winfo_screenwidth())
        Label(self.navpanel, text="select test run and instance:").grid(row=0, column=1)
        
        self.probvar = StringVar(value=str(None))
        self.navpanel.pack(side=TOP, fill=tkinter.constants.X)
        
        # init a canvas
        self.pw.pack(side=TOP, fill=BOTH, expand=1)
        self.canvas = self.pw.canvas
        
        # init a toolbar
        self.primallines = {}
        self.duallines = {}
        
        # init another frame for the configuration widget
        buttonframe = Frame(self)
        Button(buttonframe, text="Configure", command=self.openPbConfiguration).pack()
        buttonframe.pack()
        
        # create the parameters for this widget
        params = [getattr(self, name) for name in dir(self) if name.startswith('param_')]
        self.params = Manager(params)
        self.params.addObserver(self)
    
    
    
        self.probvar.trace_variable("w", self.update)
        
        self.update()
    
    def updateBoxes(self):
        try:
            self.ompr.destroy()
        except AttributeError:
            pass
        
        self.ompr = OptionMenu(self.navpanel, self.probvar, self.probvar.get(), *([str(None)] + self.gui.getProblemList()))
        self.ompr.config(width=40)
        self.ompr.grid(row=0, column=3)
    
    def openPbConfiguration(self):
        pbconfigurationframe = PbConfigurationFrame(self.gui, self)
        pbconfigurationframe.mainloop()
    
    def resetAxis(self):
        '''
        reset axis by removing all primallines and primalpatches previously drawn.
        '''
        while len(self.a.patches) > 0:
            p = self.a.patches[-1]
            p.remove()
        for testrunname in list(self.primallines.keys()):
            try:
                self.a.lines.remove(self.primallines[testrunname])
            except:
                pass
        for testrunname in list(self.duallines.keys()):
            try:
                self.a.lines.remove(self.duallines[testrunname])
            except:
                pass
    
    def getTestrunPlotData(self, testrun, probname, normalize, datakey=PrimalBoundHistoryReader.datakey, lastdatakey=PrimalBoundReader.datakey):
        '''
        get the test run plot data, depending on wether normalization is triggered on or off.
        '''
        optsol = testrun.problemGetOptimalSolution(probname)
        if optsol is None:
            print("cannot normalize because of missing solu file data")
            normalize = False
        # we don't want the gui to crash because of a missing history - just continue with next testrun
        try:
            history = testrun.problemGetData(probname, datakey)[:]
        except TypeError:
            print(testrun.getSettings(), " has no history for ", probname)
            history = []
        
        # retrieve some instance problem data
        solvingtime = testrun.problemGetData(probname, "SolvingTime")
        
        if len(history) > 0:
            history.append((solvingtime, testrun.problemGetData(probname, lastdatakey)))
        
        if normalize:
            history.insert(0, (0.0, misc.FLOAT_INFINITY))
        
        thelist = list(map(list, list(zip(*history))))
        x = numpy.array(thelist[0])
        
        # depending on the normalization parameter, the normfunction used is either the CPlex gap, or the identity
        if normalize:
            normfunction = lambda x : min(100.0, misc.getGap(x, optsol, True))
        else:
            normfunction = lambda x : x
        y = numpy.array(list(map(normfunction, thelist[1])))
        
        return (x, y)
    def update(self, *args):
        '''
        update method called every time a new instance was selected
        '''
        self.updateBoxes()
        self.resetAxis()
        # make up data for plotting method
        x = {}
        y = {}
        z = {}
        zx = {}
        kws = {}
        duallinekws = {}
        dualbarkws = {}
        baseline = 0
        
        usenormalization = self.params.getManageable("Use normalization").getValue()
        showdualbound = self.params.getManageable("Show dual bound").getValue()
        xmax = xmin = ymax = ymin = 0
        # loop over testruns still in the GUI (test runs can be removed by resetting comparator object )
        for testrun in [testrun for testrun in self.gui.getTestrunList() if self.boolVars.setdefault(testrun.getIdentification(), IntVar(value=1)).get() == 1]:
            testrunname = testrun.getIdentification()
         
            probname = self.probvar.get()
            if probname not in self.gui.getProblemList():
                return
         
            x[testrunname], y[testrunname] = self.getTestrunPlotData(testrun, probname, usenormalization)
            if not usenormalization:
                baseline = testrun.problemGetOptimalSolution(probname)
                y[testrunname] -= baseline
         
            xmax = max(xmax, max(x[testrunname]))
            ymax = max(ymax, max(y[testrunname]))
            ymin = min(ymin, min(y[testrunname]))
            if showdualbound:
                zx[testrunname], z[testrunname] = self.getTestrunPlotData(testrun, probname, usenormalization, datakey=DualBoundHistoryReader.datakey, lastdatakey=DualBoundReader.datakey);
                if usenormalization:
                    z[testrunname] = -z[testrunname]
                ymin = min(ymin, min(z[testrunname]))
          
                duallinekws[testrunname] = dict(linestyle=':')
                dualbarkws = dict(alpha=0.1)
          
            # set special key words for the testrun
            kws[testrunname] = dict(alpha=0.1)
        else:
            # for now, only one color cycle exists
            #colormap = cm.get_cmap(name='spectral', lut=128)
            #self.a.set_color_cycle([colormap(i) for i in numpy.linspace(0.1, 0.9, len(self.gui.getTestrunList()))])
            
            # call the plot on the collected data
            self.primalpatches, self.primallines, self.a = self.axisPlotForTestrunData(x, y, baseline=baseline, ax=self.a, legend=False, labelsuffix="_primal", plotkw=kws, barkw=kws)
            if showdualbound:
                __ , self.duallines, self.a = self.axisPlotForTestrunData(zx, z, step=False, baseline=0, ax=self.a, legend=False, labelsuffix="_dual", plotkw=duallinekws, barkw=dualbarkws)
            
            # set a legend and limits
            self.a.legend(fontsize=8)
            self.a.set_xlim((xmin - 0.05 * (xmax - xmin), xmax + 0.05 * (xmax - xmin)))
            self.a.set_ylim((ymin - 0.1 * (ymax - ymin), ymax + 0.1 * (ymax - ymin)), emit=True)
            self.a.set_xlabel(self.params.getManageable("X Label").getValue())
            self.a.set_ylabel(self.params.getManageable("Y Label").getValue())
            
            self.canvas.draw()
    
    def axisPlotForTestrunData(self, dataX, dataY, bars=False, step=True, barwidthfactor=1.0, baseline=0, testrunnames=None, ax=None, legend=True, labelsuffix="",
         colormapname="spectral", plotkw=None, barkw=None):
        '''
        create a plot for your X and Y data. The data can either be specified as matrix, or as a dictionary
        specifying containing the labels as keys.
        
        - returns the axes object and a dictionary {label:line} of the line plots that were added
        
        arguments:
        -dataX : The X data for the plot, exspected either as
                    1: A dictionary with the plot labels as keys and some iterable as value-list
                    OR
                    2: A list of some iterables which denote the X values.
        
        -dataY : The y plot data of the plot. Must be specified in the same way as the X data
        
        -testrunnames: labels for axis legend. they will overwrite the labels specified by dictionary-organized data.
                       if testrunnames == None, the primallines will either be labelled from '0' to 'len(dataX)-1',
                       or inferred from the dataX-keys().
        -ax: matplotlib axes object, will be created as new axis if not specified
        
        -legend: specify if legend should be created, default True
        -colormapname: name of the colormap to use in case no colors are specified by the 'colors' argument
        
        -kw, other keywords for the plotting function, such as transparency, etc. can be specified for every plot
            separately, either as a dictionary with the dataX-keys, or as a kw-list with the same length as the
            dataX list
        '''
        
        # index everything by labels, either given as dictionary keys, or integer indices ranging from 0 to len(dataX) - 1
        assert type(dataX) is type(dataY)
        if type(dataX) is dict:
            labels = list(dataX.keys())
            if testrunnames is None:
                testrunnames = {label:label for label in labels}
        else:
            assert type(dataX) is list
            labels = list(range(len(dataX)))
           
            if testrunnames is None:
                testrunnames = {label:repr(label) for label in labels}
        
        # init colors if not given
        
        try:
            colormap = cm.get_cmap(name=colormapname, lut=128)
        except ValueError:
            print("Colormap of name ", colormapname, " does not exist")
            colormap = cm.get_cmap(name=SCIPguiPbHistoryWidget.default_cmap, lut=128)
        colortransform = numpy.linspace(0.1, 0.9, len(labels))
        
        colors = {label:colormap(colortransform[index]) for index, label in enumerate(labels)}
        
        
        if ax is None:
            ax = plt.gca()
        
        patches = {}
        lines = {}
        for label in labels:
            # retrieve special key words, or use the entire keyword dictionary
            if plotkw is not None:
                linekw = plotkw.get(testrunnames[label], plotkw)
            else:
                linekw = {}
            if barkw is not None:
                bkw = barkw.get(testrunnames[label], barkw)
            else:
                bkw = {}
         
            x = dataX[label]
            y = dataY[label]
            idd = testrunnames[label]
            if bars:
                patches[idd] = ax.bar(x[:-1], y[:-1], width=barwidthfactor * (x[1:] - x[:-1]), bottom=baseline, color=colors[label], linewidth=0, **bkw)
            else:
                patches[idd] = []
            # # use step functions for primal and plot for dual plots
            plotlabel = idd + labelsuffix
            if step:
                #lines[idd], = ax.step(x, y + baseline, color=colors[label], label=idd, where='post')
                lines[idd], = ax.step(x, y + baseline, label=plotlabel, where='post')
            else:
                #lines[idd], = ax.plot(x, y + baseline, color=colors[label], label=idd, **linekw)
                lines[idd], = ax.plot(x, y + baseline, label=plotlabel, **linekw)
        
        if len(labels) > 0 and legend:
            ax.legend(fontsize=8)
        return (patches, lines, ax)
    
    def selectTestrun(self, testrun):
        var = self.boolVars.setdefault(testrun.getIdentification(), IntVar())
        var.set(1)
    def unselectTestrun(self, testrun):
        var = self.boolVars.setdefault(testrun.getIdentification(), IntVar())
        var.set(0)

class PbConfigurationFrame(Toplevel):

    def __init__(self, gui, pbhistorywidget, master=None, cnf={}, **kw):
        Toplevel.__init__(self, master=master, cnf=cnf, **kw)
        self.wm_title("Configure History")
        w = self.winfo_screenwidth()
        h = self.winfo_screenheight()
        self.geometry("600x300+%d+%d" % ((w - 400) / 2, (h - 300) / 2))
        self.pbhistorywidget = pbhistorywidget
        panedwindow = Panedwindow(self, orient=HORIZONTAL)
        panedwindow.pack(expand=True, fill=BOTH);
        dataselectionframe = LabelFrame(panedwindow, text='Choose test runs')
        self.createSelectionPanel(dataselectionframe, gui)
        panedwindow.add(dataselectionframe)
        
        historystyleoptionpanel = LabelFrame(panedwindow, text='History display options')
        panedwindow.add(historystyleoptionpanel)
        for param in pbhistorywidget.params.getManageables(onlyactive=False):
            IPETTypeWidget(historystyleoptionpanel, param.getName(), param, pbhistorywidget.params, attribute=param.getValue()).pack(side=TOP)
        
    def createSelectionPanel(self, dataselectionframe, gui):
        '''
        create the tree view object to (de)activate test run display
        '''
        
        self.treeviewkeys = Treeview(dataselectionframe)
        # add two buttons to (unselect) testruns for the primal integral
        buttons = Frame(dataselectionframe)
        buttons.pack(fill=tkinter.constants.X);
        Button(buttons, text="SHOW Sel", command=self.selectitems).pack(side=tkinter.constants.LEFT)
        Button(buttons, text="HIDE Sel", command=self.unselectitems).pack(side=tkinter.constants.LEFT)
        
        self.treeviewkeys.pack()
        self.iids = {}
        for index, testrunname in enumerate(gui.getTestrunnames()):
            self.treeviewkeys.insert("", "end", testrunname, text=testrunname)
            self.iids[testrunname] = index
    
    def selectitems(self):
        for testrunname in self.treeviewkeys.selection():
            testrun = self.pbhistorywidget.gui.getTestrunList()[self.iids[testrunname]]
            self.pbhistorywidget.selectTestrun(testrun)
        self.pbhistorywidget.update()
    
    def unselectitems(self):
        for testrunname in self.treeviewkeys.selection():
            testrun = self.pbhistorywidget.gui.getTestrunList()[self.iids[testrunname]]
            self.pbhistorywidget.unselectTestrun(testrun)
        self.pbhistorywidget.update()
    
