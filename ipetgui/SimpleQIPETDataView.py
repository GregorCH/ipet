"""
The MIT License (MIT)

Copyright (c) 2016 Zuse Institute Berlin, www.zib.de

Permissions are granted as stated in the license file you have obtained
with this software. If you find the library useful for your purpose,
please refer to README.md for how to cite IPET.

@author: Gregor Hendel
"""
from PyQt4.Qt import QAbstractTableModel, QDialog, QLabel, QTableView,\
    QVBoxLayout, SIGNAL

from PyQt4 import QtCore, QtGui
import sys
from PyQt4.QtCore import Qt

class IpetTableDataModel(QAbstractTableModel):
    """
    represents a model for pandas data frames
    """
    SORT_INDEX = 0
    SORT_UP = 1
    SORT_DOWN = 2
    

    def __init__(self, dataframe):
        """
       Constructor for a data table model
        """
        super(IpetTableDataModel, self).__init__()
        self.dataframe = dataframe
        self.sorted = self.SORT_INDEX
        self.sortcolumn = None
        self.formatters = {}
       

    def sortTable(self, section):
        """
        sort the table by the given column indexed by the section
        
        sorting is iterated for a column in the order ascending, nonascending, and by index (e.g., unsorted)
        """
        if self.sortcolumn != self.dataframe.columns[section]:
            self.sorted = self.SORT_UP
        else:
            self.sorted += 1
            self.sorted %= 3
        self.sortcolumn = self.dataframe.columns[section]
        
        if self.sorted == self.SORT_INDEX:
            self.dataframe = self.dataframe.sort_index()
            self.sortcolumn = None
        elif self.sorted == self.SORT_UP:
            self.dataframe = self.dataframe.sort_values(by=self.sortcolumn, ascending=True)
        else:
            self.dataframe = self.dataframe.sort_values(by=self.sortcolumn, ascending=False)
        
        self.reset()
        
        
    def rowCount(self, *args, **kwargs):
        if self.dataframe is None:
            return 0
        return len(self.dataframe)
    
    def columnCount(self, *args, **kwargs):
        if self.dataframe is None:
            return 0
        return len(self.dataframe.columns)
    
    def data(self, index, role=QtCore.Qt.DisplayRole):
        """
        returns the data to be displayed
        """
        if role == QtCore.Qt.DisplayRole:
            i = index.row()
            j = index.column()
            dataval = self.dataframe.loc[self.dataframe.index[i], self.dataframe.columns[j]]
            formatter = self.formatters.get(self.dataframe.columns[j])

            if formatter is not None:
                return '{0}'.format(formatter(dataval))
            else:
                return '%.1f' % (dataval) if dataval is float else '{0}'.format(dataval)
        else:
            return None
        
    def getDataFrame(self):
        """
        returns the data frame for this model
        """
        return self.dataframe
    
    def setDataFrame(self, dataframe, formatters = {}):
        self.dataframe = dataframe
        self.formatters = formatters
        self.reset()
        
    
    def getString(self, stringortuple, join = "\n"):
        if type(stringortuple) is str:
            return stringortuple
        elif type(stringortuple) is tuple:
            return join.join(stringortuple)
        else:
            raise TypeError("Wrong type %s, expected string or tuple" % type(stringortuple))
    
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """
        get header data at the given orientation
        """
        if role == Qt.TextAlignmentRole:
            if orientation == Qt.Horizontal:
                return str(int(Qt.AlignLeft|Qt.AlignVCenter))
            return str(int(Qt.AlignRight|Qt.AlignVCenter))
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return self.getString(self.dataframe.columns[section])
        return self.getString(self.dataframe.index[section], join = ":    ")
    
    def flags(self, index):
        """
        return the item flags
        """
        if not index.isValid():
            return Qt.ItemIsEnabled
        return Qt.ItemFlags(QAbstractTableModel.flags(self, index))
    
    
class IPETDataTableView(QTableView):
    def __init__(self, dataframe, parent = None):
        super(IPETDataTableView, self).__init__(parent)
        self.model = IpetTableDataModel(dataframe)
        self.setModel(self.model)
        
        header = self.horizontalHeader()
        self.connect(header, SIGNAL("sectionClicked(int)"), self.sortTable)
        self.horizontalHeader().setResizeMode(QtGui.QHeaderView.Stretch)
        
    def sortTable(self, section):
        self.model.sortTable(section)
        
    def resizeColumns(self):
        pass
        
    def setDataFrame(self, dataframe, formatters = {}):
        self.model.setDataFrame(dataframe, formatters)
        self.resizeColumns()
    
        
class MainForm(QDialog):
    def __init__(self, dataframe, parent=None):
        super(MainForm, self).__init__(parent)
        
        tableLabel = QLabel("Table &1")
        self.tableView = IPETDataTableView(dataframe, self)
        tableLabel.setBuddy(self.tableView)
        layout = QVBoxLayout()
        layout.addWidget(tableLabel)
        layout.addWidget(self.tableView)
        self.setLayout(layout)
        
        self.tableView.resizeColumns()
        
if __name__ == "__main__":
    import pandas as pd
    df = pd.DataFrame(data=[[1,2,3,4], [5,6,7,8], [12,34,56,78], [98,87,76,75]], index=list("ABCD"), columns=["First", "Second", "Third", "Fourth"])
    
    qApp = QtGui.QApplication(sys.argv)

    aw = MainForm(df)
    aw.setWindowTitle("Test of data model")
    aw.show()
    sys.exit(qApp.exec_())
    
        
