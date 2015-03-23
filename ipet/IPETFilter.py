'''
Created on 16.12.2013

@author: bzfhende
'''
from Editable import Editable
import xml.etree.ElementTree as ElementTree
import numpy as np
import pandas as pd

class IPETComparison:
    '''
    comparison operators for filters. All standard binary comparisons + float comparisons (with tolerance)
    + percentage based inequality
    '''
    comparisondict = {"le":"le", "ge":"ge", "eq":"eq", "neq":"neq", "contains":"cont"}

    def __init__(self, operator, containset=None):
        '''
        constructs a comparison object by passing an appropriate operator as string
        '''
        if IPETComparison.comparisondict.has_key(operator):
            self.operator = operator
        else:
            raise KeyError("Unknown key value %s" % (operator))
        self.containset = containset


    def compare(self, x, y):
        method = getattr(self, "method_" + IPETComparison.comparisondict[self.operator])
        return method(x, y)

    def method_le(self, x, y):
        return x <= y
    def method_ge(self, x, y):
        return x >= y
    def method_eq(self, x, y):
        return x == y
    def method_neq(self, x, y):
        return x != y

    def method_cont(self, x, y):
        return x in self.containset or y in self.containset

class IPETFilter(Editable):
    '''
    Filters are used for selecting subsets of problems to analyze.
    '''
    attribute2Options = {"anytestrun":["one", "all"], "operator":IPETComparison.comparisondict.keys()}
    
    def __init__(self, expression1, expression2, operator, anytestrun='all', containset=None):
        '''
        filter constructor
        '''
        self.expression1 = expression1
        self.expression2 = expression2

        self.anytestrun = anytestrun
        
        if operator == "contains" and containset is None:
            raise ValueError("Error: Trying to initialize a filter with operator 'contains' but no 'containset'")
        
        self.containset = containset
        self.set_operator(operator)
        

    @staticmethod
    def fromDict(attrdict):
        expression1 = attrdict.get('expression1')
        expression2 = attrdict.get('expression2')

        anytestrun = attrdict.get('anytestrun')
        operator = attrdict.get('operator')
        containset = attrdict.get('containset')

        return IPETFilter(expression1, expression2, operator, anytestrun, containset)


    def getName(self):
        prefix = self.anytestrun
        return " ".join((prefix, self.expression1, self.operator, self.expression2))

    def set_operator(self, operator):
        self.operator = operator
        self.comparison = IPETComparison(self.operator, self.containset)

    def getEditableAttributes(self):
        return ['anytestrun', 'expression1', 'operator', 'expression2']
    
    def getRequiredOptionsByAttribute(self, attr):
        return self.attribute2Options.get(attr)

    def filterProblem(self, probname, testruns=[]):
        '''
        return True or False depending on the evaluation of the filter operator comparison
        '''
        if self.operator == 'contains':
            if probname in self.containset:
                return True
            return False
        for testrun in testruns:
            x = self.evaluate(self.expression1, probname, testrun)
            y = self.evaluate(self.expression2, probname, testrun)
            if self.anytestrun == 'one' and self.comparison.compare(x, y):
                return True
            elif self.anytestrun == 'all' and not self.comparison.compare(x, y):
                return False

        if self.anytestrun == 'one':
            return False
        return True


    def filterDataFrame(self, df):
        if self.operator == 'contains':
            return np.all(df.index.isin(self.containset))
        x = self.evaluateValueDataFrame(df, self.expression1)
        y = self.evaluateValueDataFrame(df, self.expression2)
        booleanseries = self.comparison.compare(x, y)
        mymethod = np.any
        if self.anytestrun == 'all':
            mymethod = np.all

        return mymethod(booleanseries)

    def getNeededColumns(self, df):
        return [exp for exp in [self.expression1, self.expression2] if exp in df.columns]


    def evaluateValueDataFrame(self, df, value):
        if value in df.columns:
            return df[[value]]
        else:
            for conversion in [int, float, str]:
                try:
                    return conversion(value)
                except ValueError:
                    pass
        return value

    def evaluate(self, value, probname, testrun):
        if value in testrun.getKeySet():
            return testrun.problemGetData(probname, value)
        else:
            for conversion in [int, float, str]:
                try:
                    return conversion(value)
                except ValueError:
                    pass

        return value

    def filterProblems(self, probnames, testruns=[]):
        return [self.filterProblem(probname, testruns) for probname in probnames]

    def getFilteredList(self, probnames, testruns=[]):
        return [probname for probname in probnames if self.filterProblem(probname, testruns)]

    def toXMLElem(self):
        myattributes = self.attributesToDict()
        mystrattributes = {key:str(myattributes[key]) for key in self.getEditableAttributes()}
        me = ElementTree.Element('Filter', mystrattributes)
        if self.containset is not None:
            for containelem in sorted(list(self.containset)):
                me.append(ElementTree.Element("Instance", {"name":containelem}))
        return me

class IPETFilterGroup(Editable):
    '''
    represents a list of filters or filter groups, has a name attribute for quick tabular representation

    a filter group collects
    '''
    attribute2options = {"filtertype":["union", "intersection"]}
    
    editableAttributes = ["name", "filtertype"]

    def __init__(self, name=None, filtertype="intersection"):
        '''
        constructor for a filter group

        Parameters:
        ----------
        name : a suitable name for the filter group
        filtertype : either 'union' or 'intersection'
        '''
        self.name = name
        self.filters = []
        if filtertype not in ["intersection", "union"]:
            raise ValueError("Error: filtertype <%s> must be either 'intersection' or 'union'"%filtertype)

        self.filtertype = filtertype
        
    def getEditableAttributes(self):
        return self.editableAttributes
    
    def getRequiredOptionsByAttribute(self, attr):
        return self.attribute2options.get(attr)

    def addFilter(self, filter_):
        '''
        add a filter to the list of filters.

        Parameters
        ----------
        filter_ : an instance of IPETFilter or IPETFilterGroup
        '''
        self.filters.append(filter_)

    def getName(self):
        return self.name

    def filterDataFrame(self, df):
        '''
        filters a data frame object as the intersection of all instances that match the criteria defined by the filters
        '''

        groups = df.groupby(level=0)
        # first, get the highest number of instance occurrences. This number must be matched to keep the instance
        if self.filtertype == "intersection":
            instancecount = groups.apply(len).max()
            intersectionfunction = lambda x:len(x) == instancecount
        elif self.filtertype == "union":
            intersectionfunction = lambda x:len(x) >= 1

        # return a filtered data frame as intersection of all instances that match all filter criteria and appear in every test run
        return groups.filter(lambda x:intersectionfunction(x) and np.all([filter_.filterDataFrame(x) for filter_ in self.filters]))

    def filterProblem(self, probname, testruns=[]):
        for filter_ in self.filters:
            if not filter_.filterProblem(probname, testruns):
                return False

        return True

    def getNeededColumns(self, df):
        needed = []
        for filter_ in self.filters:
            needed += filter_.getNeededColumns(df)

        return needed


    def toXMLElem(self):
        myattributes = {'name':self.name}
        if self.filtertype != "intersection":
            myattributes.update({'filtertype':self.filtertype})

        me = ElementTree.Element('FilterGroup', myattributes)

        for filter_ in self.filters:
            me.append(filter_.toXMLElem())

        return me

    @staticmethod
    def processXMLElem(elem):
        '''
        inspect and process an xml element
        '''
        if elem.tag == 'FilterGroup':
            filtergroup = IPETFilterGroup(**elem.attrib)
            for child in elem:
                filtergroup.addFilter(IPETFilterGroup.processXMLElem(child))
            return filtergroup
        elif elem.tag == 'Filter':
            elemdict = dict(elem.attrib)
            for child in elem:
                instancename = child.attrib.get("name")
                if instancename:
                    elemdict.setdefault('containset', set()).add(instancename)
            filter_ = IPETFilter.fromDict(elemdict)
            return filter_

    @staticmethod
    def fromXML(xmlstring):
        '''
        parse an xml string matching the filter group XML syntax
        '''
        tree = ElementTree.fromstring(xmlstring)
        return IPETFilterGroup.processXMLElem(tree)

    @staticmethod
    def fromXMLFile(xmlfilename):
        '''
        parse a file containing an xml string matching the filter group XML representation syntax
        '''
        tree = ElementTree.parse(xmlfilename)
        return IPETFilterGroup.processXMLElem(tree.getroot())


if __name__ == '__main__':
    from Comparator import Comparator
    print "Hallo"
    comp = Comparator(files=['../../check/results/check.short.scip-3.0.2.1.linux.x86_64.gnu.opt.spx.opt83.zib.de.default.out'])
    comp.addSoluFile('../../check/testset/short.solu')
    comp.collectData()
    operator = 'ge'
    expression1 = 'Nodes'
    expression2 = '2'
    filter1 = IPETFilter(expression1, expression2, operator, anytestrun=False)
    filter2 = IPETFilter(expression1, expression2, operator, anytestrun=True)
    print filter1.getName()
    print len(comp.getProblems())
    print len(filter1.getFilteredList(comp.getProblems(), comp.getManager('testrun').getManageables()))
    print len(filter2.getFilteredList(comp.getProblems(), comp.getManager('testrun').getManageables()))


    group = IPETFilterGroup('new')
    filter1 = IPETFilter('SolvingTime', '10', 'ge', True)
    filter2 = IPETFilter('SolvingTime', '10', 'le', True)
    group.addFilter(filter1)
    group.addFilter(filter2)
    group2 = IPETFilterGroup('another')
    group2.addFilter(filter1)
    group.addFilter(group2)
    xml = group.toXMLElem()
    from xml.dom.minidom import parseString
    dom = parseString(ElementTree.tostring(xml))
    with open("myfile.xml", 'w') as myfile:
        myfile.write(dom.toprettyxml())
    group3 = IPETFilterGroup.fromXMLFile('myfile.xml')
    xml = group3.toXMLElem()
    dom = parseString(ElementTree.tostring(xml))
    print dom.toprettyxml()
