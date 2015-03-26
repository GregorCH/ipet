'''
Created on 21.03.2015

@author: bzfhende
'''
from PyQt4.QtGui import QDialog, QFormLayout, QLabel, QLineEdit, QApplication,\
    QComboBox, QCompleter, QWidget, QMainWindow
import sys
from ipet.IPETEvalTable import IPETEvaluationColumn, IPETEvaluation
from PyQt4.QtCore import QStringList, SIGNAL
from ipet.IPETFilter import IPETFilterGroup, IPETFilter

class EditableForm(QWidget):
    '''
    classdocs
    '''
    availableOptions = {}
    
    USERINPUT_SIGNAL = "userinput"
    
    @staticmethod
    def extendAvailableOptions(key, moreoptions):
        currentoptionsforkey = EditableForm.availableOptions.get(key, [])
        EditableForm.availableOptions[key] = sorted(currentoptionsforkey + moreoptions)
        
    def __init__(self, editable, parent=None):
        '''
        Constructor
        '''
        
        super(EditableForm, self).__init__(parent)
        layout = EditableFormLayout()
        
        self.editable = editable
        
        self.key2val = {}
        
        for key, val in sorted(editable.attributesToDict().iteritems()):
            label = QLabel(key)
            helptext = editable.getAttrDocumentation(key)
            if helptext is not None:
                label.setToolTip(helptext)
                label.setStatusTip(helptext)
            
            valwidget = self.valToWidget(key, val)
            
            layout.addRow(label, valwidget)
            
        self.setLayout(layout)
        
        
    def reactOnUserInput(self):

        for key in self.editable.getEditableAttributes():
            val = self.convertTextToValue(self.key2val[key]())
            self.editable.editAttribute(key, val)
        
        self.emit(SIGNAL(EditableForm.USERINPUT_SIGNAL))

    def convertToText(self, value):
        if value is None:
            return ""
        else:
            return str(value)
        
    def convertTextToValue(self, text):
        if text == "":
            return None
        else:
            return str(text)
        
    def convertListOptions(self, optioninlist):
        if optioninlist is None:
            return unicode("-- no selection --")
        else:
            return unicode(optioninlist)
        
    def valToWidget(self, attr, val):
        requiredOptions = self.editable.getRequiredOptionsByAttribute(attr)
        if requiredOptions is None:
            lineedit = QLineEdit()
            lineedit.setText(self.convertToText(val))
            self.key2val[attr] = lineedit.text
            self.connect(lineedit, SIGNAL("editingFinished()"), self.reactOnUserInput)
            return lineedit
        else:
            if type(requiredOptions) is list:
                options = requiredOptions
            else:
                options = self.availableOptions.get(requiredOptions)
            if options is None:
                lineedit = QLineEdit()
                lineedit.setText(self.convertToText(val))
                self.key2val[attr] = lineedit.text
                self.connect(lineedit, SIGNAL("editingFinished()"), self.reactOnUserInput)
                return lineedit    
            options = sorted(map(self.convertListOptions, options))
            combobox = OptionsComboBox()
            combobox.addItems(options)
            if val is not None:
                combobox.setCurrentIndex(options.index(unicode(val)))
            self.key2val[attr] = combobox.currentText
            self.connect(combobox, SIGNAL("currentIndexChanged(int)"), self.reactOnUserInput)
            return combobox
            

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