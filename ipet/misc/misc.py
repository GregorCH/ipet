'''
The MIT License (MIT)

Copyright (c) 2016 Zuse Institute Berlin, www.zib.de

Permissions are granted as stated in the license file you have obtained
with this software. If you find the library useful for your purpose,
please refer to README.md for how to cite IPET.

@author: Gregor Hendel
'''
from math import *
from xml.dom.minidom import parseString
import xml.etree.ElementTree as ElementTree
import numpy as np
'''
   Various methods for evaluation such as gap calculation, geometric means etc. and some printing methods
'''
FLOAT_INFINITY = 1e20
FLOAT_LARGE = 1e15
INT_INFINITY = 1e09
DEFAULT_MIN_GEOM_MEAN = 1.0


def getSoluFileProbName(probname):
    return probname.split('.')[0]

def floatPrint(number, digitsbef=16, digitsafter=9, dispchar='g' ):
    formatstring='%'+repr(digitsbef) + '.' + repr(digitsafter) + dispchar
    if number >= FLOAT_INFINITY:
        return 'Inf'
    else:
        return formatstring % (number)

def getTexName(name):
    return name.replace('_', '\_')

def getCplexGap(value, referencevalue):
    return getGap(value, referencevalue, True)

def getGap(value, referencevalue, useCplexGap=False):
    '''
    calculate the gap between value and reference value in percent. Gap is either calculated
    w.r.t the referencevalue, i.e., abs(value-referencevalue)/abs(referencevalue) * 100,
    or in 'Cplex'-fashion, that is,  abs(value-referencevalue)/max(abs(referencevalue), abs(value)) * 100
    '''
    if value in [None, FLOAT_INFINITY] or referencevalue in [None, FLOAT_INFINITY]:
        return FLOAT_INFINITY

    if not useCplexGap:
        if referencevalue == 0.0:
            if value == 0.0:
                return 0.0
            else:
                return FLOAT_INFINITY
        else:
            return abs( value - referencevalue )/float(abs(referencevalue)) * 100
    else: # use the CPLEX gap
        maximum = max(abs(value), abs(referencevalue))
        if maximum <= 10e-9:
            return 0.0
        else:
            return abs(value - referencevalue) / maximum * 100


def listGetArithmeticMean(listofnumbers):
    '''
    returns the arithmetic mean of a list of numbers
    '''
    arithmeticmean = sum(listofnumbers)
    arithmeticmean /= max(len(listofnumbers),1)*1.0
    return arithmeticmean

def shmean(listofnumbers, shiftby=10.0):
    '''
    convenience function to have shorter access to shifted geometric mean
    '''
    return listGetShiftedGeometricMean(listofnumbers, shiftby)

def gemean(listofnumbers, mingeommean=DEFAULT_MIN_GEOM_MEAN):
    '''
    convenience function to have shorter access to geometric mean
    '''
    return listGetGeomMean(listofnumbers, mingeommean)

def listGetGeomMean(listofnumbers, mingeommean=DEFAULT_MIN_GEOM_MEAN):
    '''
    returns the geometric mean of a list of numbers, where each element under consideration
    has value min(element, mingeommean)
    '''
    geommean = 1.0
    nitems = 0
    for number in listofnumbers:
        nitems = nitems + 1
        nextnumber = max(number, mingeommean)
        geommean = pow(geommean, (nitems - 1)/float(nitems)) * pow(nextnumber, 1 / float(nitems))
    return geommean

def listGetShiftedGeometricMean(listofnumbers, shiftby=10.0):
    '''
    returns the shifted geometric mean of a list of numbers, where the additional shift defaults to
    10.0 and can be set via shiftby
    '''
    geommean = 1.0
    nitems = 0
    for number in listofnumbers:
        nitems = nitems + 1
        nextnumber = number + shiftby
        geommean = pow(geommean, (nitems - 1)/float(nitems)) * pow(nextnumber, 1 / float(nitems))
    return geommean - shiftby

def getVariabilityScore(listofnumbers):
    if len(listofnumbers) == 0:
        return 0.0
    arrayofnumbers = np.array(listofnumbers)

    return np.sqrt(np.sum((arrayofnumbers - arrayofnumbers.mean()) ** 2)) / arrayofnumbers.sum()

def cutString(string, char = '_', maxlength = -1):
    iscuttable = True
    stringcopy = string[0:len(string)]
    while len(stringcopy) > maxlength and iscuttable:
        iscuttable = False
        listofstrings = stringcopy.split(char)
        maxlen = 2
        index = -1
        for stringpart in listofstrings:
            if len(stringpart) >= 3 and len(stringpart) > maxlen:
                index = listofstrings.index(stringpart)
                maxlen = len(stringpart)
                iscuttable = True
        else:
            if iscuttable:
                stringtocut = listofstrings[index]
                assert len(stringtocut) >= 3
                listofstrings[index]= stringtocut[0] + stringtocut[len(stringtocut)-1]
                stringcopy = ''
                for stringitem in listofstrings:
                    stringcopy = stringcopy + stringitem + char
                else:
                    stringcopy.rstrip(char)

    return stringcopy.rstrip(char)

def listGetMinColWidth(listofitems):
    maxlen = -1
    for item in listofitems:
        if len(item) > maxlen:
            maxlen = len(item)
    return maxlen

def saveAsXML(nodeobject, filename):
    '''
    save object as XML file under the specified filename

    object must have a 'toXMLElem'-method
    '''

    xml = nodeobject.toXMLElem()

    dom = parseString(ElementTree.tostring(xml))

    with open(filename, 'w') as thefile:
        thefile.write(dom.toprettyxml())


