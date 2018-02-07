"""
The MIT License (MIT)

Copyright (c) 2018 Zuse Institute Berlin, www.zib.de

Permissions are granted as stated in the license file you have obtained
with this software. If you find the library useful for your purpose,
please refer to README.md for how to cite IPET.

@author: Gregor Hendel
"""
from .IpetMainWindow import IpetMainWindow
from PyQt4.Qt import QApplication, QTabWidget
import sys
from .IPETParserWindow import IPETParserWindow
from .IpetEvaluationEditorApp import EvaluationEditorWindow

class QIPETApplication(IpetMainWindow):
    """
    an application that presents different widgets for parsing and evaluating in tabs
    """

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
