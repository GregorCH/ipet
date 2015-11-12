#!/usr/bin/env python

# embedding_in_qt4.py --- Simple Qt4 application embedding matplotlib canvases
#
# Copyright (C) 2005 Florent Rougon
#               2006 Darren Dale
#
# This file is an example program for matplotlib. It may be used and
# modified with no restriction; raw copies as well as modified versions
# may be distributed without limitation.

from __future__ import unicode_literals
import sys
import os
import random

from PyQt4 import QtGui, QtCore

from numpy import arange, sin, pi
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar

from matplotlib.figure import Figure
from ipet import integrals
from PyQt4.Qt import QListWidget, QString, QAbstractItemView, QFileDialog, QApplication, QKeySequence, QAction, QIcon
from PyQt4.QtCore import SIGNAL
from ipet.TestRun import TestRun
from argparse import Action
from ipet.integrals import getProcessPlotData
from qipet.IpetMainWindow import IpetMainWindow
from ipet.StatisticReader_DualBoundHistoryReader import DualBoundHistoryReader
from ipet.StatisticReader import DualBoundReader
from matplotlib.pyplot import cm
import numpy

progname = os.path.basename(sys.argv[0])
progversion = "0.1"


class MyMplCanvas(FigureCanvas):
    """Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.)."""

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        # We want the axes cleared every time plot() is called
        self.axes.hold(False)

        self.compute_initial_figure()

        #
        
        FigureCanvas.__init__(self, fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QtGui.QSizePolicy.Expanding,
                                   QtGui.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    def compute_initial_figure(self):
        pass


class MyStaticMplCanvas(MyMplCanvas):
    """Simple canvas with a sine plot."""

    def compute_initial_figure(self):
        t = arange(0.0, 3.0, 0.01)
        s = sin(2*pi*t)
        self.axes.plot(t, s)


class IpetPbHistoryWindow(IpetMainWindow):
    
    default_cmap = 'spectral'
    
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle("application main window")

        self.file_menu = QtGui.QMenu('&File', self)
        self.file_menu.addAction('&Quit', self.fileQuit,
                                 QtCore.Qt.CTRL + QtCore.Qt.Key_Q)
        self.menuBar().addMenu(self.file_menu)
        loadaction = self.createAction("&Load", self.loadTestrun, QKeySequence.Open, icon="Load-icon", 
                                       tip="Load testrun from trn file (current test run gets discarded)")
        self.file_menu.addAction(loadaction)
        self.help_menu = QtGui.QMenu('&Help', self)
        self.menuBar().addSeparator()
        self.menuBar().addMenu(self.help_menu)

        self.help_menu.addAction('&About', self.about)

        self.main_widget = QtGui.QWidget(self)

        l = QtGui.QVBoxLayout(self.main_widget)
        self.sc = MyStaticMplCanvas(self.main_widget, width=5, height=4, dpi=100)
        toolbar = NavigationToolbar(self.sc, self.main_widget)
        l.addWidget(toolbar)
        l.addWidget(self.sc)
        self.listWidget = QListWidget()
        for item in list("ABCDE"):
            self.listWidget.addItem(QString(item))
        self.listWidget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        l.addWidget(self.listWidget)
        self.connect(self.listWidget, SIGNAL("itemSelectionChanged()"), self.selectionChanged)
        
        self.main_widget.setFocus()
        self.setCentralWidget(self.main_widget)
        self.testrun = None

        self.statusBar().showMessage("Ready to load some test run data!", 5000)

    def selectionChanged(self):
        if self.testrun is None:
            return
        
        problist = [str(item.text()) for item in self.listWidget.selectedItems()]
        if len(problist) == 0:
            return
        if len(problist) == 1:
            plotpoints = getProcessPlotData(self.testrun, problist[0])
            print plotpoints
            self.update_Axis(problist[0])
            
    def updateStatus(self, message):
        self.statusBar().showMessage(message, 5000)

    
    def fileQuit(self):
        self.close()
        
    def setTestrun(self, tr):
        self.testrun = tr
        self.listWidget.clear()
        for prob in tr.getProblems():
            self.listWidget.addItem(QString(prob))
        
    def closeEvent(self, ce):
        self.fileQuit()
        
    def loadTestrun(self):
        thedir = unicode(".")
        filename = unicode(QFileDialog.getOpenFileName(self, caption=QString("%s - Load a testrun"%QApplication.applicationName()),
                                               directory=thedir, filter=unicode("Testrun files (*.trn)")))
        if filename:
            try:
                tr = TestRun.loadFromFile(str(filename))
                message = "Loaded testrun from %s"%filename
                
                self.setTestrun(tr)
            except Exception, e:
                message = "Error: Could not load testrun from file %s"%filename
                
            self.updateStatus(message)
            
        
        pass
    
    def update_Axis(self, probname):
        '''
        update method called every time a new instance was selected
        '''
        #self.resetAxis()
        # make up data for plotting method
        x = {}
        y = {}
        z = {}
        zx = {}
        kws = {}
        duallinekws = {}
        dualbarkws = {}
        baseline = 0
        
        usenormalization = True
        showdualbound = False
        xmax = xmin = ymax = ymin = 0
        # loop over testruns still in the GUI (test runs can be removed by resetting comparator object )
        testrunname = self.testrun.getIdentification()
     
        x[testrunname], y[testrunname] = zip(*getProcessPlotData(self.testrun, probname, usenormalization))
        if not usenormalization:
            baseline = self.testrun.problemGetOptimalSolution(probname)
            y[testrunname] -= baseline
     
        xmax = max(xmax, max(x[testrunname]))
        ymax = max(ymax, max(y[testrunname]))
        ymin = min(ymin, min(y[testrunname]))
        if showdualbound:
            zx[testrunname], z[testrunname] = zip(*getProcessPlotData(self.testrun, probname, usenormalization, historytouse=DualBoundHistoryReader.datakey, xaftersolvekey=DualBoundReader.datakey))
            if usenormalization:
                z[testrunname] = -z[testrunname]
            ymin = min(ymin, min(z[testrunname]))
      
            duallinekws[testrunname] = dict(linestyle=':')
            dualbarkws = dict(alpha=0.1)
      
        # set special key words for the testrun
        kws[testrunname] = dict(alpha=0.1)
            # for now, only one color cycle exists
            #colormap = cm.get_cmap(name='spectral', lut=128)
        #self.axes.set_color_cycle([colormap(i) for i in numpy.linspace(0.1, 0.9, len(self.gui.getTestrunList()))])
        
        # call the plot on the collected data
        self.primalpatches, self.primallines, _ = self.axisPlotForTestrunData(x, y, baseline=baseline, legend=False, labelsuffix="_primal", plotkw=kws, barkw=kws)
        if showdualbound:
            __ , self.duallines, _ = self.axisPlotForTestrunData(zx, z, step=False, baseline=0, legend=False, labelsuffix="_dual", plotkw=duallinekws, barkw=dualbarkws)
        
        # set a legend and limits
        self.sc.axes.legend(fontsize=8)
        self.sc.axes.set_xlim((xmin - 0.05 * (xmax - xmin), xmax + 0.05 * (xmax - xmin)))
        self.sc.axes.set_ylim((ymin - 0.1 * (ymax - ymin), ymax + 0.1 * (ymax - ymin)), emit=True)
        
        self.sc.draw()
    
    def axisPlotForTestrunData(self, dataX, dataY, bars=False, step=True, barwidthfactor=1.0, baseline=0, testrunnames=None, legend=True, labelsuffix="",
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
            labels = dataX.keys()
            if testrunnames is None:
                testrunnames = {label:label for label in labels}
        else:
            assert type(dataX) is list
            labels = range(len(dataX))
           
            if testrunnames is None:
                testrunnames = {label:repr(label) for label in labels}
        
        # init colors if not given
        
        try:
            colormap = cm.get_cmap(name=colormapname, lut=128)
        except ValueError:
            print "Colormap of name ", colormapname, " does not exist"
            colormap = cm.get_cmap(name=IpetPbHistoryWindow.default_cmap, lut=128)
        colortransform = numpy.linspace(0.1, 0.9, len(labels))
        
        colors = {label:colormap(colortransform[index]) for index, label in enumerate(labels)}
        
        
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
                patches[idd] = self.sc.axes.bar(x[:-1], y[:-1], width=barwidthfactor * (x[1:] - x[:-1]), bottom=baseline, color=colors[label], linewidth=0, **bkw)
            else:
                patches[idd] = []
            # # use step functions for primal and plot for dual plots
            plotlabel = idd + labelsuffix
            if step:
                #lines[idd], = ax.step(x, y + baseline, color=colors[label], label=idd, where='post')
                lines[idd], = self.sc.axes.step(x, y, label=plotlabel, where='post')
            else:
                #lines[idd], = ax.plot(x, y + baseline, color=colors[label], label=idd, **linekw)
                lines[idd], = self.sc.axes.plot(x, y + baseline, label=plotlabel, **linekw)
        
        if len(labels) > 0 and legend:
            self.sc.axes.legend(fontsize=8)
        return (patches, lines, self.sc.axes)

    def about(self):
        QtGui.QMessageBox.about(self, "About",
                                """embedding_in_qt4.py example
Copyright 2005 Florent Rougon, 2006 Darren Dale

This program is a simple example of a Qt4 application embedding matplotlib
canvases.

It may be used and modified with no restriction; raw copies as well as
modified versions may be distributed without limitation."""
                                )


qApp = QtGui.QApplication(sys.argv)

aw = IpetPbHistoryWindow()
aw.setWindowTitle("%s" % progname)
aw.show()
sys.exit(qApp.exec_())