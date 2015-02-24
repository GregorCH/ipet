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
        self.columns = []
        
    def addFilterGroup(self, fg):
        self.filtergroups.append(fg)
    def removeFilterGroup(self, fg):
        self.filtergroups.remove(fg)
        
    def setGroupKey(self, gk):
        self.groupkey = gk
        
    def addColumn(self, col):
        self.columns.append(col)
    
    def removeColumn(self, col):
        self.columns.remove(col)
        
    def reduceToColumns(self, df):
        return df[[col.origcolname for col in self.columns] + [self.groupkey]]
    
    def toXMLElem(self):
        me = ElementTree.Element('Evaluation', {'groupkey':self.groupkey})
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
        columndata['ProblemNames'] = columndata.index
        filtered = {}
        
            
        ret = columndata.pivot('ProblemNames', self.groupkey).swaplevel(0, 1, axis=1)
        
        # filter column data and group by group key #
        
        for fg in self.filtergroups:
            reduceddata = columndata[self.applyFilterGroup(columndata, fg, comp)]
            filtered[fg.name] = reduceddata.pivot_table(index=self.groupkey, aggfunc=len)
        
        ret = pd.concat((ret, self.aggregateTable(ret)))
        print ret.to_string(na_rep = '')
        print pd.concat([filtered[fg.name] for fg in self.filtergroups], keys=[fg.name for fg in self.filtergroups], names=['Group']).to_latex()
        
        return ret
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
                
        print columnorder
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
    print ElementTree.tostring(agg.toXMLElem())
        
    from ipet.Comparator import Comparator
    comp = Comparator.loadFromFile('../test/.testcomp.cmp')
    
    ev.evaluate(comp)
#     
    xml = ev.toXMLElem()
    from xml.dom.minidom import parseString
    dom = parseString(ElementTree.tostring(xml))
    with open("myfile.xml", 'w') as myfile:
        myfile.write(dom.toprettyxml())
#     xml = ev.toXMLElem()
#     dom = parseString(ElementTree.tostring(xml))
#     print dom.toprettyxml()
#         
        