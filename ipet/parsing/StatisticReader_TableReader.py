"""
The MIT License (MIT)

Copyright (c) 2018 Zuse Institute Berlin, www.zib.de

Permissions are granted as stated in the license file you have obtained
with this software. If you find the library useful for your purpose,
please refer to README.md for how to cite IPET.

@author: Gregor Hendel
"""
import re
from ipet import misc
from .StatisticReader import StatisticReader
from ipet.concepts.IPETNode import IpetNodeAttributeError

class TableReader(StatisticReader):
    """
    Reader which tries to read various data arranged in table format -
    Format Foo: a     b
             1  : 0     5
             2  : 7     9

    will be parsed into flattened data keys Foo_a_1, Foo_a_2, Foo_b_1 etc. and added to the testrun with their corresponding
    (numeric) table entry

    It can also read single column tables of the form
    Foo:
    a  : 1
    b  : 2
    ...

    and will store the corresponding values under Foo_a, and Foo_b
    """
    name = 'TableReader'
    tableids = ['Presolvers', 'Constraints', 'Constraint Timings', 'Propagators', 'Propagator Timings', 'Conflict Analysis', 'Cutselectors',
                'Separators', 'Branching Rules', 'Diving Statistics', 'Diving (single)', 'Diving (adaptive)', 'LP', 'Branching Analysis', 'Primal Heuristics', 'Concurrent Solvers', 'Integrals']
    columnids = ['Root Node', 'Total Time', 'B&B Tree']
    active = False
    spacesepcolumnnames = ['LP Iters']
    replacecolumnnames = [''.join(sscname.split()) for sscname in spacesepcolumnnames]
    wrongtableid = 'Wrong'
    tableid = wrongtableid


    def convertToFloat(self, x):
        try:
            return float(x)
        except:
            return None

    def extractStatistic(self, line):
        if re.match('^SCIP Status', line):
            self.active = True

        elif self.active and re.match('[a-zA-Z]', line):
            if not re.search(':', line):
                return None
            try:
                colonidx = line.index(':')
            except:
                # print(StatisticReader.problemname, line)
                raise Exception()
            tableid = line[:colonidx].rstrip()
            self.tableid = ''.join(tableid.split())
            if tableid in self.tableids:

                preprocessedline = line[colonidx + 1:]
                for expr, replacement in zip(self.spacesepcolumnnames, self.replacecolumnnames):
                    preprocessedline = re.sub(expr, replacement, preprocessedline)

                    # we are parsing a table
                self.columns = preprocessedline.split()

                    # we are only parsing a single column
            elif tableid in self.columnids:
                self.columns = []
            else:
                self.tableid = self.wrongtableid

        elif self.active and self.tableid != self.wrongtableid:
            try:
                colonidx = line.index(':')
            except:
                self.tableid = self.wrongtableid
                return None

            rowname = ''.join(line[:colonidx].split())

            # distinguish between single columns and tables with multiple columns
            if self.columns != []:

                # treat tables (tables with at least two data columns)
                datakeys = ['_'.join((self.tableid, column, rowname)) for column in self.columns]
                data = list(map(self.convertToFloat, misc.numericExpression.findall(line[colonidx + 1:])))
            else:
                # treat vectors (tables with only one data column)
                datakeys = ['_'.join((self.tableid, rowname))]
                # TODO This works, why is eclipse complaining?
                data = [self.convertToFloat(misc.numericExpression.search(line, colonidx + 1).group(0))]

            # determine minimum length (necessary if more headers were recognized than actual available data)
            minlen = min(len(datakeys), len(data))

            storekeys = [re.sub("[%&()]", ".", x) for x in datakeys[:minlen]]

            self.addData(storekeys, data[:minlen])

    def execEndOfProb(self):
        self.active = False

class CustomTableReader(TableReader):
    """customizable plugin statistics reader for user plugin data tables
    """

    def __init__(self, name = "CustomTableReader", tableid = None, columnid = None):
        """Constructs custom data table reader

        Parameters
        ----------
        tableid : string representing table identifier

        singlecolumname : string representing a column identifier
        """

        if tableid is None and columnid is None:
            raise Exception("Both tableid and singlecolumname are None")
        self.set_tableid(tableid)
        self.set_columnid(columnid)
        self.name = name

    def set_tableid(self, tableid):
        self.tableid = tableid
        if tableid is not None:
            self.tableids = [tableid]
        else:
            self.tableids = []

    def set_columnid(self, columnid):
        self.columnid = columnid
        if columnid is not None:
            self.columnids = [columnid]
        else:
            self.columnids = []


    def getEditableAttributes(self):
        return TableReader.getEditableAttributes(self) + ["tableid", "singlecolumname"]
