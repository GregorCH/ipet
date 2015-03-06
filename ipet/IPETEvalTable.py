'''
Created on 24.02.2015

@author: Gregor Hendel
'''
import pandas as pd
from Aggregation import Aggregation
import xml.etree.ElementTree as ElementTree
from ipet.IPETFilter import IPETFilterGroup
import numpy

class IPETEvaluationColumn:

    def __init__(self, origcolname=None, name=None, formatstr=None, transformfunc=None, constant=None,
                 nanrep=None, minval=None, maxval=None, comp=None, translevel=None):
        '''
        constructor of a column for the IPET evaluation

        Parameters
        ----------
        origcolname : column name in the original data frame
        name : column name that will be displayed for this column
        formatstr : a format string to define how the column gets printed, if no format

        transformfunc : a transformation function, that should be applied to all children
                        columns of this column recursively. See also the 'translevel' attribute

        constant : should this column represent a constant value?

        nanrep : replacement of nan-values for this column

        minval : a minimum value for all elements in this column

        maxval : a maximum value for all elements in this column

        comp : should a comparison for this column with the 'comp'-group be made? This will append one column per group with this column
               name and a 'Q'-Suffix. Use comp="default" if it should be compared with the setting 'default', if existent. Any nonexistent
               comp will be silently skipped

        translevel : Specifies the level on which to apply the defined transformation for this column. Use translevel=0 to handle every instance
                     and group separately, and translevel=1 for an instance-wise transformation over all groups, e.g., the mean solving time
                     if five permutations were tested. Columns with translevel=1 are appended at the end of the instance-wise table
        '''

        if origcolname is None and transformfunc is None and constant is None:
            raise AttributeError("Error constructing this column: No origcolname or transformfunction specified")


        self.origcolname = origcolname
        self.name = name

        self.formatstr = formatstr
        self.transformfunc = transformfunc
        self.constant = constant

        self.nanrep = nanrep
        self.minval = minval
        self.maxval = maxval
        self.translevel = translevel
        self.comp = comp


        self.aggregations = []
        self.children = []

    def addChild(self, child):
        self.children.append(child)

    def getName(self):
        '''
        infer the name for this column

        if this column was constructed with a column name, the name is used
        else if this column represents an original column of the data frame,
        the original column name is used, otherwise, we construct an
        artificial name that represents how this column is constructed
        '''
        if self.name is not None:
            return self.name
        elif self.origcolname is not None:
            return self.origcolname
        elif self.constant is not None:
            return "Const_%s"%self.constant
        else:
            return self.transformfunc + ','.join((child.getName() for child in self.children))

    def parseValue(self, val):
        '''
        parse a value into an integer (prioritized) or float
        '''
        for conversion in [int, float]:
            try:
                return conversion(val)
            except:
                pass
        return None


    def parseConstant(self):
        '''
        parse the constant attribute, which is a string, into an integer (prioritized) or float
        '''
        return self.parseValue(self.constant)

    def addAggregation(self, agg):
        self.aggregations.append(agg)

    def getTransLevel(self):
        if self.translevel is None or int(self.translevel) == 0:
            return 0
        else:
            return 1

    def toXMLElem(self):
        '''
        convert this Column into an XML node
        '''

        # keep only non NAN elements
        myelements = {k:self.__dict__[k] for k in ['name', 'origcolname', 'transformfunc', 'formatstr', 'constant', 'nanrep', 'minval', 'maxval'] if self.__dict__.get(k) is not None}


        me = ElementTree.Element("Column", myelements)

        # iterate through children and aggregations and convert them to xml nodes
        for child in self.children:
            me.append(child.toXMLElem())

        for agg in self.aggregations:
            me.append(agg.toXMLElem())

        return me
    @staticmethod

    def processXMLElem(elem):

        if elem.tag == 'Column':
            column = IPETEvaluationColumn(**elem.attrib)
            for child in elem:
                if child.tag == 'Aggregation':
                    column.addAggregation(Aggregation.processXMLElem(child))
                elif child.tag == 'Column':
                    column.addChild(IPETEvaluationColumn.processXMLElem(child))
            return column

    def getColumnData(self, df):
        '''
        Retrieve the data associated with this column
        '''

        # if no children are associated with this column, it is either
        # a column represented in the data frame by an 'origcolname',
        # or a constant
        if len(self.children) == 0:
            if self.origcolname is not None:
                result = df[self.origcolname]
            elif self.constant is not None:
                df[self.getName()] = self.parseConstant()
                result = df[self.getName()]
        else:
            # try to apply an element-wise transformation function to the children of this column
            transformfunc = getattr(numpy, self.transformfunc)

            # concatenate the children data into a new data frame object
            argdf = pd.concat([child.getColumnData(df) for child in self.children], axis=1)

            if self.translevel is not None and int(self.translevel) == 1:

                # group the whole table per instance #
                argdf = argdf.groupby(level=0)

                #determine the axis along which to apply the transformation later on
                applyaxis = 0
            else:
                applyaxis = 1

            try:
                # try to directly apply the transformation function, this might fail for
                # some transformations, e.g., the 'divide'-function of numpy because it
                # requires two arguments instead of the series associated with each row
                result = argdf.apply(transformfunc, axis=applyaxis)
            except ValueError:

                # try to wrap things up in a temporary wrapper function that unpacks
                # the series argument into its single values
                def tmpwrapper(*args):
                    return transformfunc(*(args[0].values))

                # apply the wrapper function instead
                result = argdf.apply(tmpwrapper, axis=applyaxis)

        if self.nanrep is not None:
            nanrep = self.parseValue(self.nanrep)
            if nanrep is not None:
                result = result.fillna(nanrep)
        if self.minval is not None:
            minval = self.parseValue(self.minval)
            if minval is not None:
                result = numpy.maximum(result, minval)
        if self.maxval is not None:
            maxval = self.parseValue(self.maxval)
            if maxval is not None:
                result = numpy.minimum(result, maxval)

        return result


    def getStatsTests(self):
        return [agg.getStatsTest() for agg in self.aggregations if agg.getStatsTest() is not None]

class IPETEvaluation:
    '''
    evaluates for a comparator with given group keys, columns, and filter groups
    '''

    #todo put tex, csv etc. here as other possible streams for filter group output
    possiblestreams=['stdout', 'tex', 'txt']
    DEFAULT_GROUPKEY="SETTINGS"
    DEFAULT_DEFAULTGROUP="default"
    ALLTOGETHER="_alltogether_"

    def __init__(self):
        self.filtergroups = []
        self.groupkey = self.DEFAULT_GROUPKEY
        self.defaultgroup = self.DEFAULT_DEFAULTGROUP
        self.columns = []
        self.fgroup2stream = {}

    def addFilterGroup(self, fg):
        self.filtergroups.append(fg)
    def removeFilterGroup(self, fg):
        self.filtergroups.remove(fg)

    def setGroupKey(self, gk):
        self.groupkey = gk


    def setDefaultGroup(self, dg):
        self.defaultgroup = dg

    def addColumn(self, col):
        self.columns.append(col)

    def removeColumn(self, col):
        self.columns.remove(col)

    def reduceToColumns(self, df):
        usercolumns = []

        levelonecols = []
        #treat columns differently for level=0 and level=1
        for col in self.columns:
            if col.getTransLevel() == 0:
                df[col.getName()] = col.getColumnData(df)
                usercolumns.append(col.getName())

                if col.comp is not None and col.comp in df[self.groupkey].unique():
                    compcol = dict(list(df.groupby(self.groupkey)[col.getName()]))[col.comp]
                    df["_tmpcol_"] = compcol
                    df[col.getName() + "Q"] = df[col.getName()] / df["_tmpcol_"]
                    usercolumns.append(col.getName() + "Q")


            else:
                levelonecols.append(col.getColumnData(df))
                if col.getName() not in usercolumns:
                    usercolumns.append(col.getName())

        # concatenate level one columns into a new data frame and treat them as the altogether setting
        if len(levelonecols) > 0:
            alltogetherdf = pd.concat(levelonecols, axis=1)
            alltogetherdf[self.groupkey] = IPETEvaluation.ALLTOGETHER
            # concatenate both data frames #
            newdf = pd.concat([df, alltogetherdf], axis=0)
        else:
            newdf = df



        neededcolumns = [col for col in [self.groupkey, 'Status', 'SolvingTime', 'TimeLimit'] if col not in usercolumns]
        result = newdf.loc[:,usercolumns + neededcolumns]
        self.usercolumns = usercolumns
        return result

    def calculateNeededData(self, df):
        df['_solved_'] = (df.SolvingTime < df.TimeLimit) & (df.Status != 'fail') & (df.Status != 'abort')
        df['_time_'] = (df.Status == 'timelimit')
        df['_fail_'] = (df.Status == 'fail')
        df['_abort_'] = (df.Status == 'abort')
        df['_count_'] = 1
        df['_unkn_'] = (df.Status == 'unknown')
        df['ProblemNames'] = df.index

        return df

    def toXMLElem(self):
        me = ElementTree.Element('Evaluation', {'groupkey':self.groupkey, 'defaultgroup':self.defaultgroup})
        for col in self.columns:
            me.append(col.toXMLElem())
        for fg in self.filtergroups:
            fgelem = fg.toXMLElem()
            me.append(fgelem)
            if self.fgroup2stream.get(fg.getName()) is not None:
                fgelem.attrib["stream"] = self.fgroup2stream.get(fg.getName())

        return me

    @staticmethod
    def fromXML(xmlstring):
        tree = ElementTree.fromstring(xmlstring)
        return IPETEvaluation.processXMLElem(tree)

    @staticmethod
    def fromXMLFile(xmlfilename):
        tree = ElementTree.parse(xmlfilename)
        return IPETEvaluation.processXMLElem(tree.getroot())

    @staticmethod
    def processXMLElem(elem):
        if elem.tag == 'Evaluation':
            ev = IPETEvaluation()
            ev.setGroupKey(elem.attrib.get('groupkey', IPETEvaluation.DEFAULT_GROUPKEY))
            ev.setDefaultGroup(elem.attrib.get('defaultgroup', IPETEvaluation.DEFAULT_DEFAULTGROUP))
        for child in elem:
            if child.tag == 'FilterGroup':
                # add the filter group to the list of filter groups
                fg = IPETFilterGroup.processXMLElem(child)
                ev.addFilterGroup(fg)

                #if there is a stream attribute associated with this group
                if child.attrib.get("stream") is not None:
                    ev.fgroup2stream[fg.getName()] = child.attrib.get("stream")

            elif child.tag == 'Column':
                ev.addColumn(IPETEvaluationColumn.processXMLElem(child))
        return ev

    def convertToHorizontalFormat(self, df):
        return df[self.usercolumns + ['ProblemNames', self.groupkey]].pivot('ProblemNames', self.groupkey).swaplevel(0, 1, axis=1)

    def checkStreamType(self, streamtype):
        if streamtype not in self.possiblestreams:
            return False
        else:
            return True

    def streamDataFrame(self, df, filebasename, streamtype):
        if not self.checkStreamType(streamtype):
            raise ValueError("Stream error: Unknown stream type %s"%streamtype)
        streammethod = getattr(self, "streamDataFrame_%s"%streamtype)

        streammethod(df, filebasename)

    def streamDataFrame_stdout(self, df, filebasename):
        '''
        print to console
        '''
        print "Data for %s:"%filebasename
        print df.to_string()

    def streamDataFrame_tex(self, df, filebasename):
        '''
        write tex output
        '''
        with open("%s.tex"%filebasename, "w") as texfile:
            texfile.write(df.to_latex())

    def streamDataFrame_txt(self, df, filebasename):
        '''
        write txt output
        '''
        with open("%s.txt"%filebasename, "w") as txtfile:
            df.to_string(txtfile)

    def evaluate(self, comp):
        '''
        evaluate the data of a Comparator instance comp

        Parameters
        ----------
        comp : a Comparator instance for which data has already been collected

        Returns
        -------
        rettab : an instance-wise table of the specified columns
        retagg : aggregated results for every filter group and every entry of the specified
        '''

        #data is concatenated along the rows
        data = pd.concat([tr.data for tr in comp.testrunmanager.getManageables()])

        columndata = self.reduceToColumns(data)
        columndata = self.calculateNeededData(columndata)

        filtered = {}

        # compile a results table containing all instances
        ret = self.convertToHorizontalFormat(columndata)

        # filter column data and group by group key #

        for fg in self.filtergroups:
            # iterate through filter groups, thereby aggregating results for every group
            reduceddata = self.applyFilterGroup(columndata, fg)

            if self.fgroup2stream.get(fg.getName()) is not None:
                self.streamDataFrame(self.convertToHorizontalFormat(reduceddata), fg.getName(), self.fgroup2stream.get(fg.getName()))

            # the general part sums up the number of instances falling into different categories
            generalpart = reduceddata[['_count_', '_solved_', '_time_', '_fail_', '_abort_', '_unkn_'] + [self.groupkey]].pivot_table(index=self.groupkey, aggfunc=sum)

            # column aggregations aggregate every column and every column aggregation
            colaggpart = pd.concat([reduceddata[[col.getName(), self.groupkey]].pivot_table(index=self.groupkey, aggfunc=agg.aggregate) for col in self.columns for agg in col.aggregations], axis=1)

            # rename the column aggregations
            colaggpart.columns = ['_'.join((col.getName(), agg.getName())) for col in self.columns for agg in col.aggregations]

            # determine the row in the aggregated table corresponding to the default group
            if self.defaultgroup in colaggpart.index:
                defaultrow = colaggpart.loc[self.defaultgroup, :]
            else:
                # if there is no default setting, take the first group as default group
                try:
                    defaultrow = colaggpart.iloc[0, :]
                except:
                    defaultrow = numpy.nan

            # determine quotients
            comppart = colaggpart / defaultrow
            comppart.columns = [col + 'Q' for col in colaggpart.columns]

            #apply statistical tests, whereever possible
            statspart = self.applyStatsTests(reduceddata)

            #glue the parts together
            parts = [generalpart, colaggpart, comppart]
            if statspart is not None:
                parts.append(statspart)

            filtered[fg.name] = pd.concat(parts, axis = 1)

        rettab = ret#pd.concat((ret, self.aggregateTable(ret)))
        retagg = pd.concat([filtered[fg.name] for fg in self.filtergroups], keys=[fg.name for fg in self.filtergroups], names=['Group'])

        return rettab, retagg
    '''
        for fg in self.filtergroups:
            self.applyFilterGroup(columndata, fg, comp)
    '''
    def applyFilterGroup(self, df, fg):
        return fg.filterDataFrame(df)

    def applyStatsTests(self, df):
        '''
        apply statistical tests defined by each column
        '''

        # group the data by the groupkey
        groupeddata = dict(list(df.groupby(self.groupkey)))
        stats = []
        names = []
        for col in self.columns:
            # iterate through the columns
            defaultvalues = None
            try:
                defaultvalues = groupeddata[self.defaultgroup][col.getName()]
            except KeyError:
                print "Sorry, cannot retrieve default values for column %s, key %s"%(col.getName(), self.defaultgroup)
                continue

            # iterate through the stats tests associated with each column
            for statstest in col.getStatsTests():
                stats.append(df[[self.groupkey, col.getName()]].pivot_table(index=self.groupkey, aggfunc=lambda x:statstest(x, defaultvalues)))
                names.append('_'.join((col.getName(), statstest.__name__)))

        if len(stats) > 0:
            stats = pd.concat(stats, axis=1)
            stats.columns = names

            return stats
        else:
            return None
    def aggregateTable(self, df):
        results = {}
        columnorder = []
        for col in self.columns:
            origcolname = col.getName()
            partialdf = df.xs(origcolname, level=1, axis=1, drop_level=False)

            for partialcol in partialdf.columns:
                columnorder.append(partialcol)
                results[partialcol] = {}
                for agg in col.aggregations:
                    results[partialcol][agg.getName()] = agg.aggregate(df[partialcol])

        return pd.DataFrame(results)[columnorder]

if __name__ == '__main__':
    ev = IPETEvaluation.fromXMLFile('../test/testevaluate.xml')
#     ev.addColumn(IPETEvaluationColumn('SolvingTime'))
#     ev.addColumn(IPETEvaluationColumn('Nodes'))
#     group = IPETFilterGroup('new')
#     filter1 = IPETFilter('SolvingTime', '0.01', 'ge', True)
#     filter2 = IPETFilter('Nodes', '10', 'le', True)
#     group.addFilter(filter1)
#     group.addFilter(filter2)
    agg = Aggregation('shmean', shiftby=10)
    #ev.columns[0].addAggregation(agg)
    #print ElementTree.tostring(agg.toXMLElem())

    from ipet.Comparator import Comparator
    comp = Comparator.loadFromFile('../test/.testcomp.cmp')

    rettab, retagg = ev.evaluate(comp)
    print rettab.to_string()
    print retagg.to_string()
    xml = ev.toXMLElem()
    from xml.dom.minidom import parseString
    dom = parseString(ElementTree.tostring(xml))
    with open("myfile.xml", 'w') as myfile:
        myfile.write(dom.toprettyxml())
#     xml = ev.toXMLElem()
#     dom = parseString(ElementTree.tostring(xml))
#     print dom.toprettyxml()
#
