"""
The MIT License (MIT)

Copyright (c) 2018 Zuse Institute Berlin, www.zib.de

Permissions are granted as stated in the license file you have obtained
with this software. If you find the library useful for your purpose,
please refer to README.md for how to cite IPET.

@author: Gregor Hendel
"""
import numpy as np
from ipet.misc import misc
import numpy
from ipet import Key
from queue import PriorityQueue

DEFAULT_HISTORYTOUSE = Key.PrimalBoundHistory
DEFAULT_XAFTERSOLVEKEY = Key.SolvingTime
DEFAULT_XLIMITKEY = Key.TimeLimit
DEFAULT_CUTOFFGAP = 100
DEFAULT_BOUNDKEY = Key.PrimalBound

def calcIntegralValue(thedatalist, pwlinear = False):
    """
    calculates the integral value of a piece-wise constant or piece-wise linear function represented as data list.
    Parameters
    ----------
    thedatalist: a list of tuples (x_i,f(x_i)) (sorted by x_i-1 <= x_i)
        interpreted as step-wise constant function f between the x_i, and 0 outside the range of the x_i
    pwlinear: optional : should the method treat the function as piece-wise linear (True) or piece-wise constant
        step-function.
    """
    assert len(thedatalist) >= 2

    # unzip the datalist
    times, gaps = thedatalist

    # for piece-wise linear functions, use trapez triangulation
    # note that only n - 1 gaps are used
    if pwlinear:
        gaps = (gaps[1:] + gaps[:-1]) / 2
    else:
        gaps = gaps[:-1]
    return np.sum((times[1:] - times[:-1]) * gaps)

def getProcessPlotData(testrun, probid, normalize = True, access = "id", reference = None,
    historytouse = DEFAULT_HISTORYTOUSE, xaftersolvekey = DEFAULT_XAFTERSOLVEKEY, xlimitkey = DEFAULT_XLIMITKEY,
    cutoffgap = DEFAULT_CUTOFFGAP, scale=False, lim=(None, None) ,
    boundkey=None
    ):
    """
    get process plot data for a selected history (X_i,Y_i)

    returns a list of tuples, where the second value of the history (Y's) are mapped via a gap function

    Parameters
    ----------
    access : str
        either "id" or "name" to determine if testrun data should be accessed by name or by id
    scale : bool
        should all x-coordinates be scaled by the limit (and therefore lie in the range [0,1])? This makes
        sense for tests where different time limits apply.
    lim : tuple
        tuple of lower and upper limit for x, or None if unspecified.
    """
    # read keys from kw dictionary
    if access == "id":
        getmethod = testrun.getProblemDataById
    else:
        getmethod = testrun.getProblemDataByName

    history = getmethod(probid, historytouse)

    xaftersolve = getmethod(probid, xaftersolvekey)

    xlim = getmethod(probid, xlimitkey)

    if lim[0] is not None and lim[1] is not None and lim[1] < lim[0]:
        raise Exception("Empty integration interval [{},{}]".format(*lim))

    if xlim is None and xaftersolve is None:
        return None
    if history is None:
        history = []

    try:
        lastbound = history[-1][1]
    except:
        lastbound = misc.FLOAT_INFINITY

    if len(history) > 0:
        x, y = list(zip(*history))
        x = list(x)
        y = list(y)
    else:
        x = []
        y = []

    if normalize:
        x.insert(0, 0.0)
        y.insert(0, misc.FLOAT_INFINITY)

    if xaftersolve is not None and lastbound is not None:
        if len(history) > 0:
            xaftersolve = max(xaftersolve, history[-1][0])
        x.append(xaftersolve)
        y.append(lastbound)

    # depending on the normalization parameter, the normfunction used is either the CPlex gap, or the identity
    if normalize:
        normfunction = lambda z : min(cutoffgap, misc.getGap(z, reference, True))
    else:
        normfunction = lambda z : z

    x = numpy.array(x)

    if scale:
        x = x / xlim

    for thelim,func in zip(lim,(numpy.maximum,numpy.minimum)):
        if thelim is not None:
            x = func(x,thelim)

    y = numpy.array(list(map(normfunction, y)))

    return x, y

def getMeanIntegral(testrun, problemlist, access = "id", **kw):
    """
    returns a numpy array that represents the mean integral over the selected problem list.

    Parameters
    ----------
    access : str
        access modifier to determine if data should be accessed by 'id' or by 'name'

    """

    history = PriorityQueue()
    for probname in problemlist:
        # plotpoints contains time, data
        plotpoints = getProcessPlotData(testrun, probname, access = access, ** kw)
        lastgap = None
        for xi, itgap in zip(plotpoints[0], plotpoints[1]):
            if lastgap is None:
                change = itgap
            else:
                change = itgap - lastgap
            lastgap = itgap
            history.put((xi, change))

    # initialize mean integral: [ [x_0, f(x_0)], [x_1, f(x_1)], ...] ]
    meanintegral = []
    currmean = 0
    while not history.empty():
        # gets item with lowest priority value
        xi, change = history.get()
        # compute the new mean
        currmean = currmean + change
        # remove duplicate datapoints [xi,*]
        while len(meanintegral) > 0 and meanintegral[-1][0] == xi:
            del meanintegral[-1]
        meanintegral.append([xi, currmean])

    xvals, gapvals = zip(*meanintegral)

    # divide integral by problem number
    gapvals = np.true_divide(gapvals, len(problemlist))

    return xvals, gapvals
