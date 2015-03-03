'''
Created on 24.02.2015

@author: Gregor Hendel
'''
import pandas as pd
from Aggregation import Aggregation
import xml.etree.ElementTree as ElementTree
from ipet.IPETFilter import IPETFilterGroup, IPETFilter
from ipet.Misc import listGetShiftedGeometricMean

class IPETEvaluationColumn:

    
    
    def __init__(self, origcolname, colname=None, formatstr="%.1f"):
        self.children = []

        self.origcolname = origcolname
        if colname is not None:
            self.name = colname
        else:
            self.name = origcolname
            
        self.formatstr = formatstr

        self.aggregations = []

    def addChild(self, child):
        self.children.append(child)

    def getName(self):
        return self.name
    
    def addAggregation(self, agg):
        self.aggregations.append(agg)

    def toXMLElem(self):
        me = ElementTree.Element("Column", {'name':self.name, 'origcolname':self.origcolname})
        for child in self.children:
            me.append(child.toXMLElem())

        for agg in self.aggregations:
            me.append(agg.toXMLElem())

        return me
    @staticmethod
    def processXMLElem(elem):
        if elem.tag == 'Column':
            column = IPETEvaluationColumn(elem.attrib.get('origcolname'), elem.attrib.get('name'))
            for child in elem:
                if child.tag == 'Aggregation':
                    column.addAggregation(Aggregation.processXMLElem(child))

            return column


    def getStatsTests(self):
        return [agg.getStatsTest() for agg in self.aggregations if agg.getStatsTest() is not None]
        
class IPETEvaluation:
    '''
    evaluates for a comparator with given group keys, columns, and filter groups
    '''


    def __init__(self):
        self.filtergroups = []
        self.groupkey = 'Settings'
        self.defaultgroup = 'default'
        self.columns = []

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
        usercolumns = [col.origcolname for col in self.columns]
        neededcolumns = [col for col in [self.groupkey, 'Status', 'SolvingTime', 'TimeLimit'] if col not in usercolumns]
        return df.loc[:,usercolumns + neededcolumns]

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
            me.append(fg.toXMLElem())

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
            ev.setGroupKey(elem.attrib.get('groupkey'))
            ev.setDefaultGroup(elem.attrib.get('defaultgroup', 'default'))
        for child in elem:
            if child.tag == 'FilterGroup':
                ev.addFilterGroup(IPETFilterGroup.processXMLElem(child))
            elif child.tag == 'Column':
                ev.addColumn(IPETEvaluationColumn.processXMLElem(child))
        return ev
    
    
    
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
        ret = columndata[[col.origcolname for col in self.columns] + ['ProblemNames', self.groupkey]].pivot('ProblemNames', self.groupkey).swaplevel(0, 1, axis=1)

        # filter column data and group by group key #

        for fg in self.filtergroups:
            # iterate through filter groups, thereby aggregating results for every group
            reduceddata = self.applyFilterGroup(columndata, fg)
            
            # the general part sums up the number of instances falling into different categories
            generalpart = reduceddata[['_count_', '_solved_', '_time_', '_fail_', '_abort_', '_unkn_'] + [self.groupkey]].pivot_table(index=self.groupkey, aggfunc=sum)
            
            # column aggregations aggregate every column and every column aggregation
            colaggpart = pd.concat([reduceddata[[col.origcolname, self.groupkey]].pivot_table(index=self.groupkey, aggfunc=agg.aggregate) for col in self.columns for agg in col.aggregations], axis=1)
            
            # rename the column aggregations
            colaggpart.columns = ['_'.join((col.getName(), agg.getName())) for col in self.columns for agg in col.aggregations]
            
            # determine the row in the aggregated table corresponding to the default group
            if self.defaultgroup in colaggpart.index:
                defaultrow = colaggpart.loc[self.defaultgroup, :]
            else:
                # if there is no default setting, take the first group as default group
                defaultrow = colaggpart.iloc[0, :]

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
                defaultvalues = groupeddata[self.defaultgroup][col.origcolname]
            except KeyError:
                print "Sorry, cannot retrieve default values for column %s, key %s"%(col.origcolname, self.defaultgroup)
                continue
            
            # iterate through the stats tests associated with each column
            for statstest in col.getStatsTests():
                stats.append(df[[self.groupkey, col.origcolname]].pivot_table(index=self.groupkey, aggfunc=lambda x:statstest(x, defaultvalues)))
                names.append('_'.join((col.getName(), statstest.__name__)))
                
        if len(stats) > 0:
            stats = pd.concat(stats, axis=1)
            print stats
            print names
            stats.columns = names
            
            return stats
        else:
            return None 
    def aggregateTable(self, df):
        results = {}
        columnorder = []
        for col in self.columns:
            origcolname = col.origcolname
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
    print rettab.dtypes
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
