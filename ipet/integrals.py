'''
Created on 14.03.2014

this module features methods that facilitate the handling of integrals for various histories.

@author: bzfhende
'''
import numpy as np
import Misc
import numpy

DEFAULT_HISTORYTOUSE = 'PrimalBoundHistory'
DEFAULT_XAFTERSOLVEKEY = 'SolvingTime'
DEFAULT_XLIMITKEY = 'TimeLimit'
DEFAULT_CUTOFFGAP = 100
DEFAULT_BOUNDKEY = 'PrimalBound'

def calcIntegralValue(thedatalist, pwlinear=False):
    '''
       calculates the integral value of a piece-wise constant or piece-wise linear function represented as data list.
    
       Keyword arguments:
       thedatalist -- a list of tuples (x_i,f(x_i)) (sorted by x_i-1 <= x_i)
                      interpreted as step-wise constant function f between the x_i, and 0 outside the range of the x_i
       pwlinear -- optional : should the method treat the function as piece-wise linear (True) or piece-wise constant
                              step-function.
    
    '''
    assert len(thedatalist) >= 2
    
    # unzip the datalist
    times, gaps = zip(*thedatalist)
    times = np.array(times)
    gaps = np.array(gaps)
    
    # for piece-wise linear functions, use trapez triangulation
    # note that only n - 1 gaps are used
    if pwlinear:
        gaps = (gaps[1:] + gaps[:-1]) / 2
    else:
        gaps = gaps[:-1]
    return np.sum((times[1:] - times[:-1]) * gaps)
    
def getProcessPlotData(testrun, probname, normalize=True, **kw):
    '''
    get process plot data for a selected history (X_i,Y_i)
    
    returns a list of tuples, where the second value of the history (Y's) are mapped via a gap function
    '''
    # read keys from kw dictionary
    historytouse = kw.get('historytouse', DEFAULT_HISTORYTOUSE)
    history = testrun.problemGetData(probname, historytouse)
    
    xaftersolvekey = kw.get('xaftersolvekey', DEFAULT_XAFTERSOLVEKEY)
    xaftersolve = testrun.problemGetData(probname, xaftersolvekey)
    
    xlimitkey = kw.get('xlimitkey', DEFAULT_XLIMITKEY)
    xlim = testrun.problemGetData(probname, xlimitkey)
    
    cutoffgap = kw.get('cutoffgap', DEFAULT_CUTOFFGAP)
    
    optimum = testrun.problemGetData(probname, 'OptVal')
    
    if xlim is None and xaftersolve is None:
        return None
    if history is None:
        history = []
    
    lastboundkey = kw.get('boundkey', DEFAULT_BOUNDKEY)
    lastbound = testrun.problemGetData(probname, lastboundkey)
    if lastbound is None:
        try:
            lastbound = history[-1][1]
        except:
            pass 
        
    if len(history) > 0 and xlim is not None:
        history.append((xlim, lastbound))
         
    if normalize:
        history.insert(0, (0.0, Misc.FLOAT_INFINITY))
         
    thelist = map(list, zip(*history))
    x = numpy.array(thelist[0])
         
    # depending on the normalization parameter, the normfunction used is either the CPlex gap, or the identity  
    if normalize:
        normfunction = lambda x : min(cutoffgap, Misc.getGap(x, optimum, True))
    else:
        normfunction = lambda x : x
    y = numpy.array(map(normfunction, thelist[1]))
        
    
    return zip(x,y)

def getMeanIntegral(testrun, problemlist, meanintegralpoints, **kw):
    '''
    returns a numpy array that represents the mean integral over the selected problem list.
    
    '''
    # initialize mean integral to be zero at all points of the chosen granularity
    meanintegral = np.zeros(meanintegralpoints)
    
    # get the x axis limit, usually the
    THE_XLIMIT = max(testrun.problemlistGetData(problemlist, kw.get('xlimitkey', DEFAULT_XLIMITKEY)))
    scale = THE_XLIMIT / float(meanintegralpoints)
    
    # go through problem list and add up integrals for every problem
    for probname in problemlist:
        plotpoints = getProcessPlotData(testrun, probname, **kw)
        it = plotpoints[1:].__iter__()
        lastX = -1.0
        lastgap = kw.get('cutoffgap', DEFAULT_CUTOFFGAP)
        for xi, itgap in it:
            startindex = int(lastX + 1)/scale
            lastindex = int(xi + 1) / scale
            meanintegral[startindex:lastindex] += lastgap
            lastX = xi
            lastgap = itgap
    
    # divide integral by problem number
    meanintegral = np.true_divide(meanintegral, len(problemlist))
    
    return (meanintegral, scale)
