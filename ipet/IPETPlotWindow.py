'''
Created on 31.01.2014

@author: Customer
'''
from Tkinter import Toplevel
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
import Tkconstants
# implement the default mpl key bindings
class IPETPlotWindow(Toplevel):
   '''
   toplevel window to contain a matplotlib plot
   
   An IPETPlotWindow is a toplevel window which contains a matplotlib figure,
   containing one or more axes, and a control panel to control its appearance.
   '''
   def __init__(self, master=None, cnf={}, **kw):
      Toplevel.__init__(self, master, cnf)
      f = Figure(figsize=(5, 4), dpi=100)
      self.a = f.add_subplot(111)

      self.canvas = FigureCanvasTkAgg(f, master=self)
      self.canvas.get_tk_widget().pack(side=Tkconstants.BOTTOM, fill=Tkconstants.BOTH, expand=1)

      self.toolbar = NavigationToolbar2TkAgg(self.canvas, self)
      self.toolbar.update()


      self.canvas._tkcanvas.pack(side=Tkconstants.TOP, fill=Tkconstants.BOTH, expand=1)

