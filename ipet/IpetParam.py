'''
Created on 29.11.2013

@author: bzfhende
'''
from ttk import Checkbutton, Entry, Button, Frame
from Tkinter import tkinter, IntVar, StringVar
import ttk
from Tkconstants import LEFT
from IPETBrowser import IPETTypeWidget
import Editable

class IPETParam:
   '''
   a parameter for the IPET gui. A parameter has a name, a description, a default value and
   a range or collection of possible values.
   '''

   def __init__(self, name, value, possiblevalues, description=''):
      '''
      construct a new Ipet parameter. the paramlist contains the name, description, value and a range or
      collection of possible values for this parameter

      To pass a float parameter called 'weight', set to 0.5 and ranging from 0 to 1,
      call
         IPETParam('weight', .5, [0,1])
      To pass collections of possible values, e.g., {True, False}, use a set for the possible values
      '''
      self.paramlist = [name, possiblevalues, description]
      self.value = value

   def getValue(self):
      '''
      get the current parameter value
      '''
      return self.value
   def getName(self):
      '''
      get the name of the parameter
      '''
      return self.paramlist[0]

   def getPossibleValues(self):
      '''
      get all possible values for this parameter
      '''
      return self.paramlist[1]

   def valIsPossible(self, value):
      '''
      check if some value is a possible parameter value
      '''
      pv = self.getPossibleValues()
      if type(pv) is set:
         return value in pv
      else:
         assert type(pv) is list
         assert len(pv) >= 2 or type(self.getValue()) is str
         if type(value) in [float, int]:
            return value <= pv[1] and value >= pv[0]
         else:
            return (pv == [] and type(self.getValue()) is str) or value in pv

   def checkAndChange(self, newvalue):
      '''
      set the parameter to a new value inside its domain
      '''
      if type(newvalue) != type(self.getValue()):
         return False
      if self.valIsPossible(newvalue):
         self.value = newvalue
         return True
      return False

   def getEditableAttributes(self):
      return ['value']

   def editAttribute(self, attributename, newvalue):
      self.checkAndChange(newvalue)
