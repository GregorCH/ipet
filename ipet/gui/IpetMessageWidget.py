'''
Created on 08.08.2014

@author: Customer
'''
from .IPETWidget import IpetWidget
from tkinter.scrolledtext import ScrolledText
import tkinter.constants

class IpetMessageWidget(IpetWidget):
    '''
    prints all messages during the process of collecting data
    '''
    name = 'Messages'
    def __init__(self, master, gui):
        IpetWidget.__init__(self, master, gui)
        self.text = ScrolledText(self)
        self.text.pack(side=tkinter.constants.LEFT, expand=True, fill=tkinter.constants.BOTH)

#        sys.stdout = TextRedirector(self.text, 'stdout')
#        sys.stderr = TextRedirector(self.text, 'stderr')

        self.text.config(state='disabled')
        self.text.tag_config('stderr', background='grey', foreground='red')

    def reset(self):
        self.text.delete("1.0", tkinter.constants.END)

class TextRedirector(object):
    def __init__(self, widget, tag="stdout"):
        self.widget = widget
        self.tag = tag

    def write(self, string):
        self.widget.configure(state="normal")
        self.widget.insert("end", string, (self.tag,))
        self.widget.configure(state="disabled")
