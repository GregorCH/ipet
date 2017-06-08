"""
The MIT License (MIT)

Copyright (c) 2016 Zuse Institute Berlin, www.zib.de

Permissions are granted as stated in the license file you have obtained
with this software. If you find the library useful for your purpose,
please refer to README.md for how to cite IPET.

@author: Gregor Hendel
"""
import re
from xml.dom.minidom import parseString
import xml.etree.ElementTree as ElementTree
import numpy as np
import datetime
import os
from ipet import Key
"""
   Various methods for evaluation such as gap calculation, geometric means etc. and some printing methods
"""
FLOAT_INFINITY = 1e20
FLOAT_LARGE = 1e15
INT_INFINITY = 1e09
DEFAULT_MIN_GEOM_MEAN = 1.0
numericExpression = re.compile("([+\-]*[\d]+[.\d]*(?:e[+-])?-*[\d]*[kMG]{0,1}|[\-]+)")
numericExpressionOrInf = re.compile("([+\-]*[\d]+[.\d]*(?:e[+-])?-*[\d]*[kMG]{0,1}|[\-]+|inf)")
tablenumericExpression = re.compile("([+\-]*[\d]+[.\d]*(?:e[+-])?-*[\d]*[kMG]{0,1}|[\-]+|cutoff)")
wordExpression = re.compile(r'[^\s]+')
useStringSplit = False

def sortingKeyContext(context):
    """
    returns sortkey belonging to context
    """
    try:
        return Key.context2Sortkey[context]
    except IndexError:
        raise IndexError("Unknown context %d" % context)

def filenameGetContext(filename):
    """
    get filecontext via fileextension
    """
    extension = os.path.splitext(os.path.basename(filename))[1]
    return Key.fileextension2context[extension]

def getWordAtIndex(line : str, index : int) -> str:
    """ Get the i'th word in a space separated string of words.
    
    Parameters
    ----------
    line
        The string from which the word should be extracted.
    index
        The integer indicating which word to extract. 
    
    Returns
    -------
    str
        The index'th word from line.
    """
    if index < 0 or useStringSplit:
        try:
            return line.split()[index]
        except:
            return None
    else:
        for idx, word in enumerate(wordExpression.finditer(line)):
            if idx == index:
                return word.group()
    return None

def getNumberAtIndex(line : str, index : int) -> str:
    """ Get the i'th number from the list of numbers in this line.
    
    Parameters
    ----------
    line
        The string from which the number should be extracted.
    index
        The integer indicating which number to extract. 
    
    Returns
    -------
    str
        The index'th number from line.
    """
    try:
        if index < 0:
            return numericExpression.findall(line)[index]
        else:
            for idx, word in enumerate(numericExpression.finditer(line)):
                if idx == index:
                    return word.group()
            else:
                return None
    except IndexError:
        return None

def getSoluFileProbName(probname):
    return probname.split('.')[0]

def floatPrint(number, digitsbef=16, digitsafter=9, dispchar='g'):
    formatstring = '%' + repr(digitsbef) + '.' + repr(digitsafter) + dispchar
    if number >= FLOAT_INFINITY:
        return 'Inf'
    else:
        return formatstring % (number)

def getTexName(name):
    return name.replace('_', '\_')

def getCplexGap(value, referencevalue):
    return getGap(value, referencevalue, True)

def getGap(value : float, referencevalue : float, useCplexGap : bool = False) -> float:
    """ Calculate the gap between two values in percent. 
    
    Gap is calculated w.r.t the referencevalue, 
    i.e., abs(value-referencevalue)/abs(referencevalue) * 100.
    
    Parameters
    ----------
    value
        One of the two values.
    referencevalue
        The reference value.
    useCplexGap
        Calculate the gap in 'Cplex'-fashion, that is,  
        abs(value-referencevalue)/max(abs(referencevalue), abs(value)) * 100.
    
    Returns
    -------
    float 
        the gap between value and reference value in percent.
    """
    if value in [None, FLOAT_INFINITY] or referencevalue in [None, FLOAT_INFINITY]:
        return FLOAT_INFINITY

    if not useCplexGap:
        if referencevalue == 0.0:
            if value == 0.0:
                return 0.0
            else:
                return FLOAT_INFINITY
        else:
            return abs(value - referencevalue) / float(abs(referencevalue)) * 100
    else:  # use the CPLEX gap
        maximum = max(abs(value), abs(referencevalue))
        if maximum <= 10e-9:
            return 0.0
        else:
            return abs(value - referencevalue) / maximum * 100


def listGetArithmeticMean(listofnumbers):
    """ Return the arithmetic mean of a list of numbers
    """
    arithmeticmean = sum(listofnumbers)
    arithmeticmean /= max(len(listofnumbers), 1) * 1.0
    return arithmeticmean

def iqr(listofnumbers):
    """ Convenience function to have better access to interQuartileRange
    """
    return np.percentile(listofnumbers, 75) - np.percentile(listofnumbers, 25)

def lQuart(listofnumbers):
    """ Convenience function to have better access to first quartile
    """
    return np.percentile(listofnumbers, 25)

def uQuart(listofnumbers):
    """ Convenience function to have better access to third quartile
    """
    return np.percentile(listofnumbers, 75)

def shmean(listofnumbers, shiftby=10.0):
    """ Convenience function to have shorter access to shifted geometric mean
    """
    return listGetShiftedGeometricMean(listofnumbers, shiftby)

def gemean(listofnumbers, mingeommean=DEFAULT_MIN_GEOM_MEAN):
    """ Convenience function to have shorter access to geometric mean
    """
    return listGetGeomMean(listofnumbers, mingeommean)

def listGetGeomMean(listofnumbers, mingeommean=DEFAULT_MIN_GEOM_MEAN):
    """ Return the geometric mean of a list of numbers, where each element under consideration
    has value min(element, mingeommean)
    """
    geommean = 1.0
    nitems = 0
    for number in listofnumbers:
        nitems = nitems + 1
        nextnumber = max(number, mingeommean)
        geommean = pow(geommean, (nitems - 1) / float(nitems)) * pow(nextnumber, 1 / float(nitems))
    return geommean

def listGetShiftedGeometricMean(listofnumbers, shiftby=10.0):
    """ Return the shifted geometric mean of a list of numbers, where the additional shift defaults to
    10.0 and can be set via shiftby
    """
    geommean = 1.0
    nitems = 0
    for number in listofnumbers:
        nitems = nitems + 1
        nextnumber = number + shiftby
        geommean = pow(geommean, (nitems - 1) / float(nitems)) * pow(nextnumber, 1 / float(nitems))
    return geommean - shiftby

def getVariabilityScore(listofnumbers):
    if len(listofnumbers) == 0:
        return 0.0
    arrayofnumbers = np.array(listofnumbers)

    return np.sqrt(np.sum((arrayofnumbers - arrayofnumbers.mean()) ** 2)) / arrayofnumbers.sum()

def isInfinite(value : float) -> bool:
    """Return if absolute value is larger than float infinity
    """
    return abs(value) >= FLOAT_INFINITY

def cutString(string, char='_', maxlength=-1):
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
                listofstrings[index] = stringtocut[0] + stringtocut[len(stringtocut) - 1]
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

def strConcat(strings : list) -> str:
    """Concatenate a list of string objects

    Parameters
    ----------
    strings
        list of input strings to concatenate

    Returns
    -------
    concatenated string
    """
    return "".join(strings)

def saveAsXML(nodeobject, filename : str) -> None:
    """ Save object as XML file.

    Object must have a 'toXMLElem'-method.
    
    Parameters
    ----------
    filename
        Name of new XML file.
        
    Returns
    -------
    None
    """
    xml = nodeobject.toXMLElem()

    dom = parseString(ElementTree.tostring(xml))

    with open(filename, 'w') as thefile:
        thefile.write(dom.toprettyxml())

def convertTimeStamp(timestamp : float) -> str:
    """ Convert a timestamp into a readable string format
    
    Parameters
    ----------
    timestamp
        Raw timestamp as int or float
        
    Returns
    -------
    str
        The human readable timestamp as in Y-m-d H:M:S
    """
    return datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")

