"""
The MIT License (MIT)

Copyright (c) 2016 Zuse Institute Berlin, www.zib.de

Permissions are granted as stated in the license file you have obtained
with this software. If you find the library useful for your purpose,
please refer to README.md for how to cite IPET.

@author: Gregor Hendel
"""
import xml.etree.ElementTree as ElementTree
import numpy as np
from ipet import Experiment
from ipet.concepts import IpetNode, IpetNodeAttributeError
import logging
import pandas as pd

class IPETValue(IpetNode):
    nodetag = "Value"
    
    def __init__(self, name=None, active=True):
        """
        constructs an Ipet Instance
        
        Parameters
        ----------
        
        name : The name of this problem
        active : True or "True" if this element should be active, False otherwise
        """
        super(IPETValue, self).__init__(active)
        self.name = name
        
    def checkAttributes(self):
        if self.name is None:
            raise IpetNodeAttributeError("name", "No name specified")
        return True
        
    def getEditableAttributes(self):
        return ["name"] + super(IPETValue, self).getEditableAttributes()
    
    @staticmethod
    def getNodeTag():
        return IPETValue.nodetag
    
    def getName(self):
        return self.name

    def getValue(self):
        for mytype in [int, float, str]:
            try:
                return mytype(self.name)
            except ValueError:
                continue
        return None

    def toXMLElem(self):
        me = ElementTree.Element(IPETValue.getNodeTag(), self.attributesToStringDict())
        return me

class IPETComparison:
    """
    comparison operators for filters. All standard binary comparisons + float comparisons (with tolerance)
    + percentage based inequality
    """
    comparisondict = {
                      "le":"le",
                      "lt":"lt",
                      "gt":"gt",
                      "ge":"ge",
                      "eq":"eq",
                      "neq":"neq"
                      }

    def __init__(self, operator):
        """
        constructs a comparison object by passing an appropriate operator as string
        """
        if str(operator) in IPETComparison.comparisondict:
            self.operator = str(operator)
        else:
            raise KeyError("Unknown key value %s" % (operator))


    def compare(self, x, y):
        method = getattr(self, "method_" + IPETComparison.comparisondict[self.operator])
        try:
            return method(x, y)
        except TypeError as t:
            logging.error("Got type error %s comparing elements x:%s and y:%s" % (t, x, y))
            return 0

    def method_le(self, x, y):
        return x <= y
    def method_lt(self, x, y):
        return x < y
    def method_ge(self, x, y):
        return x >= y
    def method_gt(self, x, y):
        return x > y
    def method_eq(self, x, y):
        return x == y
    def method_neq(self, x, y):
        return x != y

class IPETFilter(IpetNode):
    """
    Filters are used for selecting subsets of problems to analyze.
    """
    valueoperators = ["keep", "drop"]
    attribute2Options = {
                         "anytestrun":["one", "all"],
                         "operator":list(IPETComparison.comparisondict.keys()) + valueoperators}
    nodetag = "Filter"
    

    def __init__(self, expression1 = None, expression2 = None, operator = "ge", anytestrun = 'all', active = True, datakey = None):
        """
        filter constructor
        
        Parameters
        ----------
        
        expression1 : integer, float, string, or column name
        expression2 : integer, float, string, or column name
        datakey : available data key for drop and keep filters
        operator : operator such that evaluation expression1 op expression2 yields True or False
        anytestrun : either 'one' or 'all' 
        active : True or "True" if this filter should be active, False otherwise
        """

        super(IPETFilter, self).__init__(active)
        self.expression1 = expression1
        self.expression2 = expression2

        self.anytestrun = anytestrun
        self.values = []
        
        self.set_operator(operator)
        self.datakey = datakey
        
    def checkAttributes(self):
        if self.operator in self.valueoperators and self.values == []:
            raise IpetNodeAttributeError("operator", "Trying to use a filter with operator {0} and empty problem set".format(self.operator))
        return True
        
        
    @staticmethod
    def fromDict(attrdict):
        expression1 = attrdict.get('expression1')
        expression2 = attrdict.get('expression2')

        anytestrun = attrdict.get('anytestrun')
        operator = attrdict.get('operator')
        datakey = attrdict.get('datakey')
        active = attrdict.get('active', True)

        return IPETFilter(expression1, expression2, operator, anytestrun, active, datakey)

    def getName(self):
        prefix = self.anytestrun
        if self.operator in self.valueoperators:
            return "{} value filter (key: {})".format(self.operator, self.datakey)
        else:
            return " ".join((prefix, self.expression1, self.operator, self.expression2))

    def set_operator(self, operator):
        self.operator = operator
        if self.operator in list(IPETComparison.comparisondict.keys()):
            self.comparison = IPETComparison(self.operator)

    def getEditableAttributes(self):
        """
        returns editable attributes depending on the selected operator

        if a binary operator is selected, two expressions as left and right hand side of operator must be chosen
        For problem operators, no expressions are selectable.
        """
        parenteditables = super(IPETFilter, self).getEditableAttributes()

        if self.operator in list(IPETComparison.comparisondict.keys()):
            return parenteditables + ['operator', 'anytestrun', 'expression1', 'expression2']
        else:
            return parenteditables + ['operator', 'anytestrun', 'datakey']
    
    @staticmethod
    def getNodeTag():
        return IPETFilter.nodetag
    
    def getChildren(self):
        return self.values
        
    def acceptsAsChild(self, child):
        return child.__class__ is IPETValue
    
    def addChild(self, child):
        self.values.append(child)
        
    def removeChild(self, child):
        self.values.remove(child)

    def getActiveValue(self):
        return [x for x in self.values if x.isActive()]
            
    def getRequiredOptionsByAttribute(self, attr):
        return self.attribute2Options.get(attr, super(IPETFilter, self).getRequiredOptionsByAttribute(attr))

    def applyValueOperator(self, df):
        contained = False
        # loop through problem set
        contained = df.isin([x.getValue() for x in self.getActiveValue()])

        if self.anytestrun:
            contained = contained.any().bool()
        else:
            contained = contained.all().bool()

        if contained and self.operator == "keep":
            return True
        elif self.operator == "drop":
            return (not contained)

        return False

    def filterProblem(self, probname, testruns=[]):
        """
        return True or False depending on the evaluation of the filter operator comparison
        """

        # apply an problem operator directly
        if self.operator in self.valueoperators:
            return self.applyValueOperator(probname)

        # evaluate the two expressions and filter according to the anytestrun attribute if one or all match the requirement
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

    def applyFilter(self, df):
        """Apply the filter to a data frame rowwise

           Returns
           -------
           booleanseries :
        """
        if self.operator in self.valueoperators:
            return self.applyValueOperator(df[[self.datakey]])

        x = self.evaluateValueDataFrame(df, self.expression1)
        y = self.evaluateValueDataFrame(df, self.expression2)
        booleanseries = self.comparison.compare(x, y)
        return booleanseries

    def filterDataFrame(self, df):
        if self.operator in self.valueoperators:
            return self.applyValueOperator(df[[self.datakey]])

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
            return testrun.getProblemDataById(probname, value)
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
        me = ElementTree.Element(IPETFilter.getNodeTag(), self.attributesToStringDict())
        for value in self.values:
            me.append(value.toXMLElem())
        return me

class IPETFilterGroup(IpetNode):
    """
    represents a list of filters, has a name attribute for quick tabular representation

    a filter group collects
    """
    nodetag = "FilterGroup"
    attribute2options = {"filtertype":["union", "intersection"]}
    
    editableAttributes = ["name", "filtertype"]

    def __init__(self, name=None, filtertype="intersection", active=True):
        """
        constructor for a filter group

        Parameters:
        ----------
        name : a suitable name for the filter group
        filtertype : either 'union' or 'intersection'
        active : True or "True" if this filter group should be active, False otherwise
        """
        super(IPETFilterGroup, self).__init__(active)

        self.name = name
        self.filters = []
        if filtertype not in ["intersection", "union"]:
            raise ValueError("Error: filtertype <%s> must be either 'intersection' or 'union'" % filtertype)

        self.filtertype = filtertype
        
    def getEditableAttributes(self):
        return super(IPETFilterGroup, self).getEditableAttributes() + self.editableAttributes
    
    def getChildren(self):
        return self.filters
    
    def addChild(self, child):
        self.addFilter(child)

    def acceptsAsChild(self, child):
        return child.__class__ is IPETFilter
    
    def removeChild(self, child):
        self.filters.remove(child)
    
    @staticmethod
    def getNodeTag():
        return IPETFilterGroup.nodetag
    
    def getRequiredOptionsByAttribute(self, attr):
        return self.attribute2options.get(attr, super(IPETFilterGroup, self).getRequiredOptionsByAttribute(attr))

    def addFilter(self, filter_):
        """
        add a filter to the list of filters.

        Parameters
        ----------
        filter_ : an problem of IPETFilter
        """
        self.filters.append(filter_)

    def getName(self):
        return self.name

    def getActiveFilters(self):
        return [f for f in self.filters if f.isActive()]

    def filterDataFrame(self, df, index):
        """
        filters a data frame object as the intersection of all values that match the criteria defined by the filters
        """
        groups = df.groupby(index)
        # first, get the highest number of problem occurrences. This number must be matched to keep the problem
        if self.filtertype == "intersection":
            instancecount = groups.apply(len).max()
            intersectionfunction = lambda x:len(x) == instancecount
        elif self.filtertype == "union":
            intersectionfunction = lambda x:len(x) >= 1

        activefilters = self.getActiveFilters()
        # return a filtered data frame as intersection of all values that match all filter criteria and appear in every test run
        return groups.filter(lambda x:intersectionfunction(x) and np.all([filter_.filterDataFrame(x) for filter_ in activefilters]))

    def filterProblem(self, probname, testruns=[]):
        for filter_ in self.getActiveFilters():
            if not filter_.filterProblem(probname, testruns):
                return False

        return True

    def getNeededColumns(self, df):
        needed = []
        for filter_ in self.filters:
            needed += filter_.getNeededColumns(df)

        return needed

    def toXMLElem(self):
        me = ElementTree.Element('FilterGroup', self.attributesToStringDict())

        for filter_ in self.filters:
            me.append(filter_.toXMLElem())

        return me

    @staticmethod
    def processXMLElem(elem):
        """
        inspect and process an xml element
        """
        if elem.tag == IPETFilterGroup.getNodeTag():
            filtergroup = IPETFilterGroup(**elem.attrib)
            for child in elem:
                filtergroup.addFilter(IPETFilterGroup.processXMLElem(child))
            return filtergroup
        elif elem.tag == IPETFilter.getNodeTag():
            elemdict = dict(elem.attrib)
            filter_ = IPETFilter.fromDict(elemdict)
            for child in elem:
                instancename = child.attrib.get("name")
                if instancename:
                    filter_.addChild(IPETValue(instancename))
                filter_.checkAttributes()
            return filter_

    @staticmethod
    def fromXML(xmlstring):
        """
        parse an xml string matching the filter group XML syntax
        """
        tree = ElementTree.fromstring(xmlstring)
        return IPETFilterGroup.processXMLElem(tree)

    @staticmethod
    def fromXMLFile(xmlfilename):
        """
        parse a file containing an xml string matching the filter group XML representation syntax
        """
        tree = ElementTree.parse(xmlfilename)
        return IPETFilterGroup.processXMLElem(tree.getroot())


if __name__ == '__main__':
    comp = Experiment(files=['../test/check.short.scip-3.1.0.1.linux.x86_64.gnu.dbg.spx.opt85.testmode.out'])
    comp.addSoluFile('../test/short.solu')
    comp.collectData()
    operator = 'ge'
    expression1 = 'Nodes'
    expression2 = '2'
    filter1 = IPETFilter(expression1, expression2, operator, anytestrun="all")
    filter2 = IPETFilter(expression1, expression2, operator, anytestrun="one")
    print(filter1.getName())
    print(len(comp.getProblemNames()))
    print(len(filter1.getFilteredList(comp.getProblemNames(), comp.getManager('testrun').getManageables())))
    print(len(filter2.getFilteredList(comp.getProblemNames(), comp.getManager('testrun').getManageables())))


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
    print(dom.toprettyxml())
