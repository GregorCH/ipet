'''
Created on 31.01.2014

@author: Customer
'''
from Tkinter import Toplevel, StringVar, Button
from matplotlib.figure import Figure
from matplotlib import markers
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
import Tkconstants
from ipet.IpetParam import IPETParam, IPETColorParam
from ipet.Manager import Manager
from IPETBrowser import IPETTypeWidget
from tkColorChooser import askcolor
from ttk import Frame, Notebook, LabelFrame, OptionMenu, Entry
from functools import partial
# implement the default mpl key bindings
class IPETPlotWindow(Toplevel):
    '''
    toplevel window to contain a matplotlib plot
    
    An IPETPlotWindow is a toplevel window which contains a matplotlib figure,
    containing one or more axes, and a control panel to control its appearance.
    '''
    def __init__(self, master=None, cnf={}, **kw):
        Toplevel.__init__(self, master, cnf)
        f = Figure(figsize=(8, 6), dpi=100)
        self.a = f.add_subplot(111)

        self.canvas = FigureCanvasTkAgg(f, master=self)
        self.canvas.get_tk_widget().pack(side=Tkconstants.BOTTOM, fill=Tkconstants.BOTH, expand=1)

        self.toolbar = IpetNavigationToolBar(self.canvas, self)
        self.toolbar.update()


        self.canvas._tkcanvas.pack(side=Tkconstants.TOP, fill=Tkconstants.BOTH, expand=1)

    def resetAxis(self):
        while len(self.a.patches) > 0:
            p = self.a.patches[-1]
            p.remove()

    def getAxis(self):
        return self.a

class IpetNavigationToolBar(NavigationToolbar2TkAgg):

    LINESTYLES = {
              '-': 'Solid',
              '--': 'Dashed',
              '-.': 'DashDot',
              ':': 'Dotted',
              'steps': 'Steps',
              'None': 'none',
              }

    MARKERS = {val:key for key, val in markers.MarkerStyle.markers.iteritems()}

    COLORS = {'b': '#0000ff', 'g': '#00ff00', 'r': '#ff0000', 'c': '#ff00ff',
          'm': '#ff00ff', 'y': '#ffff00', 'k': '#000000', 'w': '#ffffff'}
    def __init__(self, canvas, window):
        # list of toolitems to add to the toolbar, format is:
        # (
        #   text, # the text of the button (often not visible to users)
        #   tooltip_text, # the tooltip shown on hover (where possible)
        #   image_file, # name of the image for the button (without the extension)
        #   name_of_method, # name of the method in NavigationToolbar2 to call
        # )
        additionaloptions = ('Show Options', 'Edit Axis and Curve Properties', 'stock_close', 'edit_options')
        self.toolitems = list(NavigationToolbar2TkAgg.toolitems)
        self.toolitems.append(additionaloptions)
        self.toolitems = tuple(self.toolitems)
        print self.toolitems
        NavigationToolbar2TkAgg.__init__(self, canvas, window)

    def change_var(self, *args):
        print args
        label, paramname = tuple(args[0].split(':'))
        manager = self.linemanagers.get(label, self.generalmanager)
        param = manager.getManageable(paramname)
        newval = self.paramtovar.get(param).get()

        print "Changing value of parameter %s to %s" % (paramname, newval)
        param.checkAndChange(newval)

    def changeColorVar(self, param):
        '''
        change a color parameter
        '''
        newcolor = askcolor(color=param.getValue(), parent=self.tl)
        self.colorparambuttons[param].config(background=newcolor[1])
        param.checkAndChange(newcolor[1])



    def addParamWidget(self, masterwindow, param, manager, label='General'):
        if type(param.getPossibleValues()) is set:
            labelframe = LabelFrame(masterwindow, text=param.getName(), width=85)
            self.paramtovar[param] = StringVar(value=param.getValue(), name="%s:%s" % (label, param.getName()))
            OptionMenu(labelframe, self.paramtovar[param], param.getValue(), *list(param.getPossibleValues())).pack(side=Tkconstants.LEFT, fill=Tkconstants.X, expand=True)

            self.paramtovar[param].trace('w', self.change_var)
            return labelframe
        elif isinstance(param, IPETColorParam):
            labelframe = LabelFrame(masterwindow, text=param.getName(), width=85)
            thebutton = Button(labelframe, text="", command=partial(self.changeColorVar, *[param]), background=param.getValue())
            self.colorparambuttons[param] = thebutton
            thebutton.pack(side=Tkconstants.LEFT, fill=Tkconstants.X, expand=True)
            return labelframe
        else:
            return IPETTypeWidget(masterwindow, param.getName(), param, self.generalmanager, attribute=param.getValue())
    def edit_options(self):
        print "Calling Edit Options"
        self.tl = Toplevel(self.window, width=self.winfo_screenwidth() / 4, height=self.winfo_screenheight() / 2)

        self.createParams()
        self.paramtovar = {}
        self.colorparambuttons = {}

        notebook = Notebook(self.tl, width=self.winfo_screenwidth() / 3, height=self.winfo_screenheight() / 2)
        generalframe = Frame(notebook)
        for idx, param in enumerate(self.general):
            widget = self.addParamWidget(generalframe, param, self.generalmanager, 'General')
            widget.grid(row=idx)
        notebook.add(generalframe, text='General')

        for curvedata, label, _ in self.curves:
            curveframe = Frame(notebook)

            for idx, param in enumerate(curvedata):
                widget = self.addParamWidget(curveframe, param, self.linemanagers.get(label), label)
                widget.grid(row=idx)

            notebook.add(curveframe, text=label)


        notebook.pack(side=Tkconstants.TOP, fill=Tkconstants.X, expand=1)

        buttonbox = Frame(self.tl)
        Button(buttonbox, text='Ok', command=self.tl.destroy).pack(side=Tkconstants.LEFT)
        Button(buttonbox, text='Apply', command=self.applyChanges).pack(side=Tkconstants.LEFT)
        buttonbox.pack(side=Tkconstants.TOP, fill=Tkconstants.X)
        self.window.wait_window(self.tl)
        self.tl.mainloop()

    def col2hex(self, c):
        return self.COLORS.get(c, c)

    def createParams(self):
        ax = self.canvas.figure.get_axes()[0]
        xmin, xmax = map(float, ax.get_xlim())
        ymin, ymax = map(float, ax.get_ylim())
        self.general = [IPETParam("Title", ax.get_title(), [], "Title for the axis"),
                   IPETParam("X-Min", xmin, [], "Minimum x"),
                   IPETParam("X-Max", xmax, [], "Maximum x"),
                   IPETParam('X-Label', ax.get_xlabel(), [], "Label for x-axis"),
                   IPETParam('X-Scale', ax.get_xscale(), set(('linear', 'log')), "Scale for x-axis"),
                   IPETParam("Y-Min", ymin, [], "Minimum y"),
                   IPETParam("Y-Max", ymax, [], "Maximum y"),
                   IPETParam('Y-Label', ax.get_ylabel(), [], "Label for y-axis"),
                   IPETParam('Y-Scale', ax.get_yscale(), set(('linear', 'log')), "Scale for y-axis")
               ]
        self.generalmanager = Manager(self.general)
        self.linemanagers = {}

        linedict = {}
        for line in ax.get_lines():
            label = line.get_label()
            if label == '_nolegend_':
                continue
            linedict[label] = line
        self.curves = []
        linestyles = IpetNavigationToolBar.LINESTYLES.values()
        markerkeys = IpetNavigationToolBar.MARKERS.keys()
        curvelabels = sorted(linedict.keys())
        for label in curvelabels:
            line = linedict[label]
            curvedata = [
                         IPETParam('Label', label, [], "Lable of curve in legend"),
                         IPETParam('Line Style', IpetNavigationToolBar.LINESTYLES[line.get_linestyle()], set(linestyles), "Line style of curve"),
                         IPETParam('Line Width', float(line.get_linewidth()), [], "The line width in points"),
                         IPETColorParam('Line Color', self.col2hex(line.get_color()), "The line color as hex"),
                         IPETParam('Marker Style', markers.MarkerStyle.markers[line.get_marker()], set(markerkeys), "The marker style for this curve"),
                         IPETParam('Marker Size', float(line.get_markersize()), [], "The size of the marker in pt."),
                         IPETColorParam('Marker Facecolor', self.col2hex(line.get_markerfacecolor()), "The face color of the marker"),
                         IPETColorParam('Marker Edgecolor', self.col2hex(line.get_markeredgecolor()), "The edge color of the marker")
                         ]
            self.curves.append([curvedata, label, line])
            manager = Manager(curvedata)
            self.linemanagers[label] = manager


    def applyChanges(self):
        ax = self.canvas.figure.get_axes()[0]
        title, xmin, xmax, xlabel, xscale, ymin, ymax, ylabel, yscale = tuple(map(IPETParam.getValue, self.general))
        ax.set_title(title)
        ax.set_xlim(xmin, xmax)
        ax.set_ylim(ymin, ymax)
        ax.set_xlabel(xlabel)
        ax.set_xscale(xscale)
        ax.set_ylabel(ylabel)
        ax.set_yscale(yscale)

        for curvedata, label, line in self.curves:
            label, linestyle, linewidth, color, \
                    marker, markersize, markerfacecolor, markeredgecolor = tuple(map(IPETParam.getValue, curvedata))
            line.set_label(label)
            line.set_linestyle(linestyle.lower())
            line.set_linewidth(linewidth)
            line.set_color(color)
            if marker is not 'none':
                marker = IpetNavigationToolBar.MARKERS.get(marker)
                line.set_marker(marker)
                line.set_markersize(markersize)
                line.set_markerfacecolor(markerfacecolor)
                line.set_markeredgecolor(markeredgecolor)

        ax.legend()
        self.canvas.figure.tight_layout(pad=0.5)
        self.canvas.draw()



if __name__ == "__main__":
    import numpy as np
    x = np.linspace(-1, 1, 100)

    window = IPETPlotWindow(width=200, height=200)
    window.a.plot(x, x ** 2, label="Quadrat")
    window.a.legend()
    window.mainloop()
