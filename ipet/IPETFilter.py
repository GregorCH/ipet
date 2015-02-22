'''
Created on 16.12.2013

@author: bzfhende
'''
from Editable import Editable
from dicttoxml import dicttoxml
import xml.etree.ElementTree as ElementTree
class IPETComparison:
    '''
    comparison operators for filters. All standard binary comparisons + float comparisons (with tolerance)
    + percentage based inequality
    '''
    comparisondict = {"le":"le", "ge":"ge", "eq":"eq", "neq":"neq"}

    def __init__(self, operator):
        '''
        constructs a comparison object by passing an appropriate operator as string
        '''
        if IPETComparison.comparisondict.has_key(operator):
            self.operator = operator
        else:
            raise KeyError("Unknown key value %s" % (operator))

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

class IPETFilter(Editable):
    '''
    Filters are used for selecting subsets of problems to analyze.
    '''
    def __init__(self, expression1, expression2, operator, anytestrun=True):
        '''
        filter constructor
        '''
        self.expression1 = expression1
        self.expression2 = expression2

        self.anytestrun = anytestrun
        self.set_operator(operator)
        
    @staticmethod
    def fromDict(attrdict):
        expression1 = attrdict.get('expression1')
        expression2 = attrdict.get('expression2')

        anytestrun = bool(attrdict.get('anytestrun'))
        operator = attrdict.get('operator')
        return IPETFilter(expression1, expression2, operator, anytestrun)


    def getName(self):
        prefix = ""
        if self.anytestrun:
            prefix = "any"
        else:
            prefix = "all"
        return " ".join((prefix, self.expression1, self.operator, self.expression2))

    def set_operator(self, operator):
        self.operator = operator
        self.comparison = IPETComparison(self.operator)

    def getEditableAttributes(self):
        return ['anytestrun', 'expression1', 'operator', 'expression2']

    def filterProblem(self, probname, testruns=[]):
        '''
        return True or False depending on the evaluation of the filter operator comparison
        '''
        for testrun in testruns:
            x = self.evaluate(self.expression1, probname, testrun)
            y = self.evaluate(self.expression2, probname, testrun)
            if self.anytestrun and self.comparison.compare(x, y):
                return True
            elif not self.anytestrun and not self.comparison.compare(x, y):
                return False
        else:
            if self.anytestrun:
                return False
            return True

    def evaluate(self, value, probname, testrun):
        if value in testrun.getKeySet():
            return testrun.problemGetData(probname, value)
        else:
            for conversion in [int, float]:
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
        return ElementTree.Element('Filter', mystrattributes)

class IPETFilterGroup(Editable):

    def __init__(self, name):
        self.name = name
        self.filters = []

    def addFilter(self, filter_):
        self.filters.append(filter_)

    def toXMLElem(self):

        me = ElementTree.Element('FilterGroup', {'name':self.name})

        for filter_ in self.filters:
            me.append(filter_.toXMLElem())

        return me
    
    @staticmethod
    def processXMLElem(elem):
        '''
        inspect and process an xml element 
        '''
        if elem.tag == 'FilterGroup':
            filtergroup = IPETFilterGroup(elem.attrib.get('name'))
            for child in elem:
                filtergroup.addFilter(IPETFilterGroup.processXMLElem(child))
            return filtergroup
        elif elem.tag == 'Filter':
            filter_ = IPETFilter.fromDict(elem.attrib)
            return filter_

    @staticmethod
    def fromXML(xmlstring):
        tree = ElementTree.fromstring(xmlstring)
        return IPETFilterGroup.processXMLElem(tree)

    @staticmethod
    def fromXMLFile(xmlfilename):
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
