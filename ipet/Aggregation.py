'''
Created on 30.12.2013

@author: bzfhende
'''
import numpy
import Misc, Editable
class Aggregation:
   '''
   aggregates a list of values into a single value, as, e.g., a mean. Allows functions from numpy and
   from Misc-module
   '''
   possibleaggregations = ['listGetShiftedGeometricMean', 'listGetGeomMean', 'min', 'max', 'mean', 'size']

   def __init__(self, aggregation):
      self.set_aggregation(aggregation)

   def getName(self):
      return self.aggregation

   def set_aggregation(self, aggregation):
      if aggregation not in self.possibleaggregations:
         raise ValueError("%s aggregation not supported" % (aggregation))
      self.aggregation = aggregation
      try:
         self.aggrfunc = getattr(numpy, aggregation)
      except AttributeError:
         self.aggrfunc = getattr(Misc, aggregation)

   def aggregate(self, valuelist):
      return self.aggrfunc(valuelist)

if __name__ == '__main__':
   arr = range(10)
   agg = Aggregation('min')
   agg2 = Aggregation('max')
   print agg.aggregate(arr), agg2.aggregate(arr)
   agg.set_aggregation('mean')
   agg2.set_aggregation('listGetShiftedGeometricMean')
   print agg.aggregate(arr), agg2.aggregate(arr)
