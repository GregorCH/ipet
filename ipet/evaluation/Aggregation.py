"""
The MIT License (MIT)

Copyright (c) 2016 Zuse Institute Berlin, www.zib.de

Permissions are granted as stated in the license file you have obtained
with this software. If you find the library useful for your purpose,
please refer to README.md for how to cite IPET.

@author: Gregor Hendel
"""
import numpy
from ipet.misc import misc
from xml.etree import ElementTree
from _functools import partial
from ipet.misc.quick_Pandas import getWilcoxonQuotientSignificance as qWilcox
from ipet.concepts import IpetNode

class Aggregation(IpetNode):
    """
    aggregates a list of values into a single value, as, e.g., a mean. Allows functions from numpy and
    from misc-module
    """
    nodetag = "Aggregation"
    possibleaggregations = [None, 'shmean', 'gemean', 'min', 'max', 'mean', 'size', 'std', 'sum', 'median', 'lQuart', 'uQuart', 'iqr']
    agg2Stat = {'shmean':qWilcox}
    
    agg2keywords = {'shmean':[("shiftby", 10.0)]}

    def __init__(self, name=None, aggregation=None, **kw):
        """
        constructs an Aggregation
        
        Parameters
        ----------
        name : The name for this aggregation
        
        aggregation : the name of the aggregation function in use
        
        kw : eventually, other options that will be passed to the call of the aggregation function
        """
        # we make aggregations always active
        super(Aggregation, self).__init__(True)
        self.name = name
        self.editableattributes = ['name', 'aggregation']
        self.set_aggregation(None)
        if aggregation:
            self.set_aggregation(aggregation)
        elif name:
            try:
                self.set_aggregation(name)
            except ValueError:
                pass
            
        for key, val in kw.items():
            setattr(self, key, float(val))

    def set_name(self, newname):
        self.name = newname

    def getName(self):
        if self.name is not None:
            name = self.name
        else:
            name = self.aggregation
            
        if(len(self.getEditableAttributes()) > 2):
            name += '(%s)' % ','.join((str(self.__dict__[key]) for key in self.editableattributes[2:]))
        return name

    @staticmethod
    def getPossibleAggregations():
        return Aggregation.possibleaggregations
    
    def getEditableAttributes(self):
        return self.editableattributes

    def set_aggregation(self, aggregation):
        if aggregation not in self.possibleaggregations:
            raise ValueError("%s aggregation not supported" % (aggregation))
        
        self.aggregation = aggregation
            
        self.editableattributes = self.editableattributes[:2]
        
        if aggregation is None:
            return
        try:
            self.aggrfunc = getattr(numpy, aggregation)
        except AttributeError:
            self.aggrfunc = getattr(misc, aggregation)
            
        attrlist = self.agg2keywords.get(aggregation)
        if attrlist:
            for key, val in attrlist:
                self.__dict__[key] = val
                self.editableattributes.append(key)

    def aggregate(self, valuelist):
        if self.aggregation is None:
            return numpy.NAN
        if len(self.getEditableAttributes()) > 2:
            return self.aggrfunc(valuelist, **{key:self.__dict__[key] for key in self.editableattributes[2:]})
        else:
            return self.aggrfunc(valuelist)
        
    def getRequiredOptionsByAttribute(self, attr):
        if attr == "aggregation":
            return self.possibleaggregations
        else:
            return None

    @staticmethod
    def getNodeTag():
        return Aggregation.nodetag
    
    @staticmethod
    def processXMLElem(elem):
        if elem.tag == Aggregation.getNodeTag():
            additional = elem.attrib
            for child in elem:
                additional.update({child.tag:float(child.attrib.get('val'))})
            return Aggregation(**additional)

    def toXMLElem(self):
        attributes = self.attributesToStringDict()
        me = ElementTree.Element(Aggregation.getNodeTag(), attributes)
            
        return me

    def getStatsTest(self):
        method = self.agg2Stat.get(self.aggregation)
        if len(self.getEditableAttributes()) > 1 and method is not None:
            method = partial(method, **{key:self.__dict__[key] for key in self.editableattributes[2:]})
            method.__name__ = self.getName() + "p"
        return method

if __name__ == '__main__':
    arr = list(range(10))
    agg = Aggregation('min')
    agg2 = Aggregation('max')
    print(agg.aggregate(arr), agg2.aggregate(arr))
    agg.set_aggregation('mean')
    agg2 = Aggregation('shmean', shiftby=30.0)
    agg3 = Aggregation('shmean', shiftby=300.0)
    print(agg3.aggregate(arr), agg2.aggregate(arr))
