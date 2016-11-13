'''
Created on 22.09.2016

@author: Gregor Hendel
'''

from IpetMainWindow import IpetMainWindow
from PyQt4.QtGui import QLayout, QHBoxLayout
from PyQt4.Qt import QVBoxLayout, QWidget, QFrame, QTextEdit, QApplication, QTabWidget
from IPetTreeView import IpetTreeView
import sys
from EditableBrowser import EditableBrowser
from IPETParserWindow import IPETParserWindow
from IpetEvaluationEditorApp import EvaluationEditorWindow

class QIPETApplication(IpetMainWindow):
    '''
    an application that presents different widgets for parsing and evaluating in tabs
    '''

    def __init__(self, parent = None):
        super(QIPETApplication, self).__init__(parent)

        tabwidget = QTabWidget()
        for widget, name in [(IPETParserWindow(), "Parser"), \
                             (EvaluationEditorWindow(), "Evaluation") \
                             ]:
            tabwidget.addTab(widget, name)
            self.populateMenu(widget)
            self.populateToolBar(widget)
        
        self.setCentralWidget(tabwidget)



if __name__ == '__main__':
    app = QApplication(sys.argv)
    qipetapplication = QIPETApplication()
    qipetapplication.setWindowTitle("IPET 2.0")

    app.setApplicationName("Evaluation editor")
    parserwindow = IPETParserWindow()

    qipetapplication.show()

    sys.exit(app.exec_())
