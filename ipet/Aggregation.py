'''
Created on 30.12.2013

@author: bzfhende
'''
import numpy
import Misc, Editable
from xml.etree import ElementTree
from _functools import partial
from ipet.quick_Pandas import getWilcoxonQuotientSignificance as qWilcox

class Aggregation(Editable.Editable):
    '''
    aggregates a list of values into a single value, as, e.g., a mean. Allows functions from numpy and
    from Misc-module
    '''
    possibleaggregations = ['shmean', 'gemean', 'min', 'max', 'mean', 'size', 'std', 'sum']
    agg2Stat = {'shmean':qWilcox}
 
    def __init__(self, aggregation, **kw):
        self.set_aggregation(aggregation)
        self.name = aggregation
        self.editableattributes = ['name']
        for key, val in kw.iteritems():
            self.__dict__[key] = val
            self.editableattributes.append(key)
 
    def set_name(self, newname):
        self.name = newname
        
    def getName(self):
        name = self.name
        if( len(self.getEditableAttributes()) > 1 ):
            name += '(%s)'% ','.join((str(self.__dict__[key]) for key in self.editableattributes[1:]))
        return name
    
    def getEditableAttributes(self):
        return self.editableattributes
 
    def set_aggregation(self, aggregation):
        if aggregation not in self.possibleaggregations:
            raise ValueError("%s aggregation not supported" % (aggregation))
        self.aggregation = aggregation
        try:
            self.aggrfunc = getattr(numpy, aggregation)
        except AttributeError:
            self.aggrfunc = getattr(Misc, aggregation)
 
    def aggregate(self, valuelist):
        if len(self.getEditableAttributes()) > 1:
            return self.aggrfunc(valuelist, **{key:self.__dict__[key] for key in self.editableattributes[1:]})
        else:
            return self.aggrfunc(valuelist)
        
    @staticmethod
    def processXMLElem(elem):
        if elem.tag == 'Aggregation':
            additional = {}
            for child in elem:
                additional.update({child.tag:float(child.attrib.get('val'))})
            return Aggregation(elem.attrib.get('name'), **additional)
    
    def toXMLElem(self):
        me = ElementTree.Element('Aggregation', {'name':self.name})
        for att in self.editableattributes:
            if att == 'name':
                continue
            val = self.__dict__[att]
            me.append(ElementTree.Element(att, {'type':'float', 'val':str(val)}))
        return me
    
    def getStatsTest(self):
        method = self.agg2Stat.get(self.name)
        if len(self.getEditableAttributes()) > 1 and method is not None:
            method = partial(method, **{key:self.__dict__[key] for key in self.editableattributes[1:]})
            method.__name__ = self.getName()
        return method    

if __name__ == '__main__':
    arr = range(10)
    agg = Aggregation('min')
    agg2 = Aggregation('max')
    print agg.aggregate(arr), agg2.aggregate(arr)
    agg.set_aggregation('mean')
    agg2 = Aggregation('listGetShiftedGeometricMean',  shiftby=30.0)
    agg3 = Aggregation('listGetShiftedGeometricMean',  shiftby=300.0)
    print agg3.aggregate(arr), agg2.aggregate(arr)
