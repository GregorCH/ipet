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
    
    def __init__(self, origcolname, colname=None):
        self.children = []
        
        self.origcolname = origcolname
        if colname is not None:
            self.name = colname
        else:
            self.name = origcolname
            
        self.aggregations = []
        
    def addChild(self, child):
        self.children.append(child)
        
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
        df['_timelimit_'] = (df.Status == 'TimeLimit')
        df['_fail_'] = (df.Status == 'fail')
        df['_abort_'] = (df.Status == 'abort') 
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
        
        #data is concatenated along the rows
        data = pd.concat([tr.data for tr in comp.testrunmanager.getManageables()])
        
        columndata = self.reduceToColumns(data)
        columndata = self.calculateNeededData(columndata)
        
        filtered = {}
        
        # compile a results table containing all instances    
        ret = columndata[[col.origcolname for col in self.columns] + ['ProblemNames', self.groupkey]].pivot('ProblemNames', self.groupkey).swaplevel(0, 1, axis=1)
        
        # filter column data and group by group key #
        
        for fg in self.filtergroups:
            reduceddata = columndata[self.applyFilterGroup(columndata, fg, comp)]
            firstpart = reduceddata[['_solved_', '_fail_', '_abort_'] + [self.groupkey]].pivot_table(index=self.groupkey, aggfunc=sum)
            secondpart = pd.concat([reduceddata[[col.origcolname, self.groupkey]].pivot_table(index=self.groupkey, aggfunc=agg.aggregate) for col in self.columns for agg in col.aggregations], axis=1)
            secondpart.columns = ['_'.join((col.name, agg.name)) for col in self.columns for agg in col.aggregations]
            if self.defaultgroup in secondpart.index:
                defaultidx = secondpart.index.find(self.defaultgroup)
            else:
                defaultidx = 0
                
            defaultrow = secondpart.iloc[defaultidx, :]
            thirdpart = secondpart / defaultrow
            thirdpart.columns = [col + 'Q' for col in secondpart.columns] 
             
                                   
            filtered[fg.name] = pd.concat([firstpart, secondpart, thirdpart], axis = 1)
            
        rettab = pd.concat((ret, self.aggregateTable(ret)))
        retagg = pd.concat([filtered[fg.name] for fg in self.filtergroups], keys=[fg.name for fg in self.filtergroups], names=['Group'])
        
        return rettab, retagg
    '''
        for fg in self.filtergroups:
            self.applyFilterGroup(columndata, fg, comp)
    '''        
    def applyFilterGroup(self, df, fg, comp):
        return df.ProblemNames.apply(fg.filterProblem, testruns=comp.testrunmanager.getManageables())
        
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
    ev = IPETEvaluation.fromXMLFile('myfile.xml')
#     ev.addColumn(IPETEvaluationColumn('SolvingTime'))
#     ev.addColumn(IPETEvaluationColumn('Nodes'))
#     group = IPETFilterGroup('new')
#     filter1 = IPETFilter('SolvingTime', '0.01', 'ge', True)
#     filter2 = IPETFilter('Nodes', '10', 'le', True)
#     group.addFilter(filter1)
#     group.addFilter(filter2)
    agg = Aggregation('listGetShiftedGeometricMean', shiftby=10)
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
        