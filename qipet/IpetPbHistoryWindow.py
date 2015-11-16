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
from PyQt4.Qt import QListWidget, QString, QAbstractItemView, QFileDialog, QApplication, QKeySequence, QAction, QIcon,\
    QVariant, QFrame, QStringList
from PyQt4.QtCore import SIGNAL
from ipet.TestRun import TestRun
from argparse import Action
from ipet.integrals import getProcessPlotData, getMeanIntegral
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
        #self.axes.hold(False)
        
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
    
    DEBUG = True
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle("application main window")

        self.file_menu = QtGui.QMenu('&File', self)
        self.file_menu.addAction('&Quit', self.fileQuit,
                                 QtCore.Qt.CTRL + QtCore.Qt.Key_Q)
        self.menuBar().addMenu(self.file_menu)
        loadaction = self.createAction("&Load", self.loadTestruns, QKeySequence.Open, icon="Load-icon", 
                                       tip="Load testrun from trn file (current test run gets discarded)")
        self.file_menu.addAction(loadaction)
        self.help_menu = QtGui.QMenu('&Help', self)
        self.menuBar().addSeparator()
        self.menuBar().addMenu(self.help_menu)

        self.help_menu.addAction('&About', self.about)

        self.main_widget = QtGui.QWidget(self)

        lwframe = QFrame(self.main_widget)
        l = QtGui.QVBoxLayout(self.main_widget)
        self.sc = MyStaticMplCanvas(self.main_widget, width=5, height=4, dpi=100)
        toolbar = NavigationToolbar(self.sc, self.main_widget)
        l.addWidget(toolbar)
        l.addWidget(self.sc)
        h = QtGui.QHBoxLayout(lwframe)
        l.addWidget(lwframe)
        
        self.probListWidget = QListWidget()
        for item in list("12345"):
            self.probListWidget.addItem(QString(item))
        self.probListWidget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        h.addWidget(self.probListWidget)
        self.connect(self.probListWidget, SIGNAL("itemSelectionChanged()"), self.selectionChanged)
        
        self.trListWidget = QListWidget()
        for item in list("ABC"):
            self.trListWidget.addItem(QString(item))
        self.trListWidget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        h.addWidget(self.trListWidget)
        self.connect(self.trListWidget, SIGNAL("itemSelectionChanged()"), self.selectionChanged)
        
        self.main_widget.setFocus()
        self.setCentralWidget(self.main_widget)
        self.testruns = []
        self.primallines = {}
        self.duallines = {}
        self.primalpatches = {}

        self.statusBar().showMessage("Ready to load some test run data!", 5000)

    def getSelectedProblist(self):
        return [str(item.text()) for item in self.probListWidget.selectedItems()]
    
    def getSelectedTestrunList(self):
        return [tr for idx, tr in enumerate(self.testruns) if self.trListWidget.isItemSelected(self.trListWidget.item(idx))]
    
    def selectionChanged(self):
        if len(self.testruns) == 0:
            return
        
        problist = self.getSelectedProblist()
        if len(problist) == 0:
            return
        
        testruns = self.getSelectedTestrunList()
        if len(testruns) == 0:
            return
        
        
        self.update_Axis(problist, testruns)
        
        
            
    def updateStatus(self, message):
        self.statusBar().showMessage(message, 5000)

    
    def fileQuit(self):
        self.close()
        
    def addTestrun(self, tr):
        self.testruns.append(tr)
        self.probListWidget.clear()
        self.trListWidget.clear()
        
        problems = []
        for testrun in self.testruns:
            self.trListWidget.addItem(QString(testrun.getName()))
            problems += testrun.getProblems()
        
        for prob in sorted(list(set(problems))):
            self.probListWidget.addItem(QString(prob))
        
        self.trListWidget.selectAll()
        
    def closeEvent(self, ce):
        self.fileQuit()
        
    def debugMessage(self, message):
        if self.DEBUG:
            print message
        else:
            pass
        
    def loadTestruns(self):
        thedir = unicode(".")
        filenames = QFileDialog.getOpenFileNames(self, caption=QString("%s - Load testruns"%QApplication.applicationName()),
                                               directory=thedir, filter=unicode("Testrun files (*.trn)"))
        if filenames:
            loadedtrs = 0
            notloadedtrs = 0
            for filename in filenames:
                try:
                    print filename
                    tr = TestRun.loadFromFile(str(filename))
                    try:
                        self.addTestrun(tr)
                    except Exception, e:
                        print e
                    
                    loadedtrs += 1
                except Exception:
                    notloadedtrs += 1
                    
            message = "Loaded %d/%d test runs"%(loadedtrs, loadedtrs + notloadedtrs)
            self.updateStatus(message)
            
        
        pass
    
    def update_Axis(self, probnames, testruns):
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
        
        if len(probnames) == 1:
            self.updateStatus("Showing problem %s on %d test runs"%(probnames[0], len(testruns)))
        else:
            self.updateStatus("Showing mean over %d problems on %d test runs"%(len(probnames), len(testruns)))
        self.resetAxis()
        usenormalization = True
        showdualbound = False
        xmax = xmin = ymax = ymin = 0
        for testrun in testruns:
            testrunname = testrun.getName()
         
            if len(probnames) == 1:
                x[testrunname], y[testrunname] = zip(*getProcessPlotData(testrun, probnames[0], usenormalization))
            else:
                y[testrunname], scale = getMeanIntegral(testrun, probnames, 200)
                x[testrunname] = numpy.arange(200) * scale
            if not usenormalization and len(probnames) == 1:
                baseline = testrun.problemGetOptimalSolution(probnames[0])
                y[testrunname] -= baseline
         
            xmax = max(xmax, max(x[testrunname]))
            ymax = max(ymax, max(y[testrunname]))
            ymin = min(ymin, min(y[testrunname]))
            if showdualbound:
                arguments = {"historytouse":DualBoundHistoryReader.datakey, "xaftersolvekey":DualBoundReader.datakey}
                if len(probnames) == 1:
                    zx[testrunname], z[testrunname] = zip(*getProcessPlotData(testrun, probnames[0], usenormalization, **arguments))
                else:
                    z[testrunname], scale = getMeanIntegral(testrun, probnames, 200, usenormalization, **arguments)
                    zx[testrunname] = numpy.arange(200) * scale
                    
                # normalization requires negative dual gap
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
    
    
    def resetAxis(self):
        '''
        reset axis by removing all primallines and primalpatches previously drawn.
        '''
        self.sc.axes.cla()

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