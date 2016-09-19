'''
Created on 08.03.2013

@author: bzfhende
'''
from IpetWidget import IpetWidget
from Tkinter import StringVar, Label, Frame, Toplevel
from SCIPguiSelectionLabel import SCIPguiSelectionLabel

import matplotlib
from Tkconstants import TOP, BOTH, BOTTOM
import numpy
from ipet.gui.IPETPlotWindow import IpetNavigationToolBar
matplotlib.use('TkAgg')

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
# implement the default mpl key bindings
from matplotlib.backend_bases import key_press_handler


from matplotlib.figure import Figure

class IpetScatterWidget(IpetWidget):
    '''
    classdocs
    '''
    name = "Scatter Plot"
    LABELWIDTH = 40

    def __init__(self, master, gui, **kw):
        '''
        Constructor
        '''
        IpetWidget.__init__(self, master, gui, **kw)

        self.firstdatakeyvar = StringVar()
        self.seconddatakeyvar = StringVar()
        self.firsttestrunvar = StringVar()
        self.secondtestrunvar = StringVar()

        selectionpanel = Frame(self)
        selectionpanel.pack()

        firsttestrunselectionlabel = SCIPguiSelectionLabel(selectionpanel, self.gui.getTestrunnames, self.firsttestrunvar, self.update)
        secondtestrunselectionlabel = SCIPguiSelectionLabel(selectionpanel, self.gui.getTestrunnames, self.secondtestrunvar, self.update)

        firstdatakeyselectionlabel = SCIPguiSelectionLabel(selectionpanel, self.gui.getAllDatakeys, self.firstdatakeyvar, self.update)
        seconddatakeyselectionlabel = SCIPguiSelectionLabel(selectionpanel, self.gui.getAllDatakeys, self.seconddatakeyvar, self.update)

        firsttestrunselectionlabel.grid(row=0, column=0)
        secondtestrunselectionlabel.grid(row=0, column=1)
        firstdatakeyselectionlabel.grid(row=1, column=0)
        seconddatakeyselectionlabel.grid(row=1, column=1)

        f = Figure(figsize=(5, 4), dpi=100)
        self.a = f.add_subplot(111)

        self.canvas = FigureCanvasTkAgg(f, master=self)
        self.canvas.get_tk_widget().pack(side=BOTTOM, fill=BOTH, expand=1)

        self.toolbar = IpetNavigationToolBar(self.canvas, self)
        self.toolbar.update()


        self.canvas._tkcanvas.pack(side=TOP, fill=BOTH, expand=1)
        self.canvas.mpl_connect('pick_event', self.onpick)
        self.canvas.draw()

        self.pointwindow = None
        self.markerline = None
        self.scatterplot = None
        self.diagonal = None

    def update(self):
        if self.firstdatakeyvar.get() == SCIPguiSelectionLabel.EMPTY or self.seconddatakeyvar.get() == SCIPguiSelectionLabel.EMPTY or self.firsttestrunvar.get() == SCIPguiSelectionLabel.EMPTY or self.secondtestrunvar.get() == SCIPguiSelectionLabel.EMPTY:
            return

        if self.scatterplot != None:
            self.a.lines.remove(self.scatterplot)
        if self.diagonal != None:
            self.a.lines.remove(self.diagonal)
        if self.pointwindow != None:
            self.pointwindow.destroy()
        if self.markerline != None:
            self.a.lines.remove(self.markerline)
        self.markerline = None
        self.pointwindow = None


        firsttestrun = self.gui.getTestrun(self.firsttestrunvar.get())
        secondtestrun = self.gui.getTestrun(self.secondtestrunvar.get())
        problist = self.gui.getProblemList()

        self.x = numpy.array(firsttestrun.problemlistGetData(problist, self.firstdatakeyvar.get()))
        self.y = numpy.array(secondtestrun.problemlistGetData(problist, self.seconddatakeyvar.get()))
        self.problist = numpy.array(problist)

        self.scatterplot, = self.a.plot(self.x, self.y, 'o', color='b', alpha=0.7, picker=3)
        maximum = max(numpy.max(numpy.abs(self.x)), numpy.max(numpy.abs(self.y)))
        self.diagonal, = self.a.plot([0, maximum], [0, maximum], alpha=0.6)
        self.a.set_xlabel(self.firsttestrunvar.get() + ":" + self.firstdatakeyvar.get())
        self.a.set_ylabel(self.secondtestrunvar.get() + ":" + self.seconddatakeyvar.get())
        self.canvas.draw()


    def onpick(self, event):
        thisline = event.artist
        xdata = thisline.get_xdata()
        ydata = thisline.get_ydata()
        ind = event.ind
#        matplotlib.artist.setp(thisline, color=colors)
        points = zip(self.problist[ind], self.x[ind], self.y[ind])
        if self.pointwindow != None:
            self.pointwindow.destroy()
        if self.markerline != None:
            self.a.lines.remove(self.markerline)
        self.markerline, = self.a.plot(xdata[ind], ydata[ind], 'o', c='r', picker=3)
        self.canvas.draw()
        self.pointwindow = Toplevel(self)
        self.pointwindow.wm_title("Selected Points")
        self.pointwindow.geometry("200x100+%d+%d" % (self.winfo_rootx() + event.mouseevent.x, self.winfo_rooty() + event.mouseevent.y))
        for elem in points:
            Label(self.pointwindow, text=elem, bg='white').pack(side=TOP)
        self.pointwindow.mainloop()

