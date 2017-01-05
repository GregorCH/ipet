'''
The MIT License (MIT)

Copyright (c) 2016 Zuse Institute Berlin, www.zib.de

Permissions are granted as stated in the license file you have obtained
with this software. If you find the library useful for your purpose,
please refer to README.md for how to cite IPET.

@author: Gregor Hendel
'''
from PyQt4.QtGui import QDialog, QFormLayout, QLabel, QLineEdit, QApplication,\
    QComboBox, QCompleter, QWidget, QMainWindow, QCheckBox
import sys
from ipet.evaluation.IPETEvalTable import IPETEvaluationColumn, IPETEvaluation
from PyQt4.QtCore import SIGNAL, Qt
from ipet.evaluation.IPETFilter import IPETFilterGroup
from ipet.evaluation.IPETFilter import IPETFilter
from ipet.concepts.Editable import EditableAttributeError

class EditableForm(QWidget):
    '''
    classdocs
    '''
    availableOptions = {}
    
    USERINPUT_SIGNAL = "userinput"
    NOSELECTIONTEXT = "-- no selection --"
    
    ERRORSTYLE = "{0} {{ color : red; font-weight : bold; }}"

    @staticmethod
    def extendAvailableOptions(key, moreoptions):
        currentoptionsforkey = EditableForm.availableOptions.get(key, [EditableForm.NOSELECTIONTEXT, ])
        EditableForm.availableOptions[key] = sorted(currentoptionsforkey + moreoptions)
        
    def __init__(self, editable, parent=None):
        '''
        Constructor
        '''
        
        super(EditableForm, self).__init__(parent)
        layout = EditableFormLayout()
        
        self.error = None
        self.editable = editable
        try:
            self.editable.checkAttributes()
        except EditableAttributeError as e:
            self.error = e

        self.key2Container = {}
        
        for key, val in sorted(editable.attributesToDict().items()):
            label = QLabel(key, parent = self)

            if self.isErrorKey(key):
                label.setStyleSheet(self.ERRORSTYLE.format("QLabel"))
                helptext = self.error.getMessage()
            else:
                helptext = editable.getAttrDocumentation(key)

            valwidgetContainer = self.valToWidgetContainer(key, val)
            self.key2Container[key] = valwidgetContainer
            if helptext is not None:
                for w in (valwidgetContainer.getWidget(), label):
                    w.setToolTip(helptext)
                    w.setStatusTip(helptext)
            
            label.setBuddy(valwidgetContainer.getWidget())
            layout.addRow(label, valwidgetContainer.getWidget())
            
        self.setLayout(layout)
        
    def isErrorKey(self, key):
        return key == self.error.getAttribute() if self.error else False
        
    def reactOnUserInput(self):

        for key in self.editable.getEditableAttributes():
            container = self.key2Container[key]
            val = self.convertWidgetValueToValue(container.getWidgetValue())
            self.editable.editAttribute(key, val)
        
        self.emit(SIGNAL(EditableForm.USERINPUT_SIGNAL))

    def convertToText(self, value):
        if value is None:
            return ""
        return str(value)
        
    def convertWidgetValueToValue(self, val):
        if type(val) is bool:
            return val
        if val == "" or val == self.NOSELECTIONTEXT:
            return None
        else:
            return str(val)
        
    def convertListOptions(self, optioninlist):
        if optioninlist is None:
            return str(self.NOSELECTIONTEXT)
        else:
            return str(optioninlist)
        
    def errorAdjustValWidget(self, widget):
        '''
        adjust a widget to inform the user that it there is an error
        '''
        p = widget.palette()
        p.setColor(widget.backgroundRole(), Qt.red)
        widget.setPalette(p)

    def getRequiredOptionsListForAttribute(self, attr):
        requiredOptions = self.editable.getRequiredOptionsByAttribute(attr)
        if requiredOptions is not None:
            if type(requiredOptions) is list:
                options = requiredOptions
            else:
                options = self.availableOptions.get(requiredOptions)

            options = sorted(map(self.convertListOptions, options))
        else:
            options = None
        return options

    def valToWidgetContainer(self, attr, val):
        '''
        construct a widget container for the specified attribute
        '''
        options = self.getRequiredOptionsListForAttribute(attr)

        # the default container type is the more general one
        if type(val) is bool:
            # create a new check box with checked state set to val

            widget = QCheckBox(self)
            widget.setText("")
            widget.setChecked(val)
            self.connect(widget, SIGNAL("stateChanged(int)"), self.reactOnUserInput)
            if self.isErrorKey(attr):
                widget.setStyleSheet(self.ERRORSTYLE.format("QCheckBox"))
            valueCallable = widget.isChecked

        elif options is not None:
            # use a combobox to represent a list of options
            widget = OptionsComboBox(self)
            widget.addItems(options)
            if val is not None:
                widget.setCurrentIndex(options.index(str(val)))
            self.connect(widget, SIGNAL("currentIndexChanged(int)"), self.reactOnUserInput)
            if self.isErrorKey(attr):
                widget.setStyleSheet(self.ERRORSTYLE.format("OptionsComboBox"))
            valueCallable = widget.currentText

        else:
            # use a simple line edit if options are undefined
            widget = QLineEdit(self)
            widget.setText(self.convertToText(val))
            self.connect(widget, SIGNAL("editingFinished()"), self.reactOnUserInput)
            if self.isErrorKey(attr):
                widget.setStyleSheet(self.ERRORSTYLE.format("QLineEdit"))
            valueCallable = widget.text


        return EditableAttributeWidgetContainer(attr, widget, valueCallable)

class EditableAttributeWidgetContainer:

    def __init__(self, attr, widget, valueCallable):
        '''
        constructs a container that has both the attribute and the corresponding widget
        '''
        self._attribute = attr
        self._valueCallable = valueCallable
        self._widget = widget

    def getWidget(self):
        '''
        returns the widget of this container
        '''
        return self._widget

    def getAttribute(self):
        '''
        returns the attribute of this container
        '''
        return self._attribute

    def getWidgetValue(self):
        return self._valueCallable()

class OptionsComboBox(QComboBox):
    
    def __init__(self, parent=None):
        super(OptionsComboBox, self).__init__(parent)
        self.setEditable(True)
        completer = self.completer()
        completer.setCompletionMode(QCompleter.PopupCompletion)
        
class EditableFormLayout(QFormLayout):
    
    def __init__(self, parent=None):
        super(EditableFormLayout, self).__init__(parent)
        
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    EditableForm.extendAvailableOptions("datakey", list("ABCDEFHIJKLMNOPQRSTUVWXYZ1234567890"))
    
    col = IPETEvaluationColumn(origcolname="A", name="name", formatstr="%.2f", transformfunc="sum", constant=None, nanrep="2", minval="0.5", maxval="10.0", comp="default", translevel="1")
    
    mainwindow = QMainWindow()
    mainwindow.menuBar()
    ev = IPETEvaluation()
    fg = IPETFilterGroup(name="bla")
    f = IPETFilter("Bla", "expression2", "neq", "one")
    form = EditableForm(col)
    mainwindow.setCentralWidget(form)
    mainwindow.show()
    
    app.exec_()
