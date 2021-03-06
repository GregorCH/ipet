"""
The MIT License (MIT)

Copyright (c) 2018 Zuse Institute Berlin, www.zib.de

Permissions are granted as stated in the license file you have obtained
with this software. If you find the library useful for your purpose,
please refer to README.md for how to cite IPET.

@author: Gregor Hendel
"""
import pandas as pd
import numpy as np
import itertools
from scipy import stats

default_to_latex_kw = dict(float_format=lambda x:"%.1f" % x, index_names=False)
colformatlatex = lambda x: "\\%s" % x

def quickAggregateAndPercentage(df, collist, rowlist, aggfunc=np.mean, defindex=0):
   parts = []
   if type(aggfunc) is not list:
      aggfuncs = [aggfunc] * len(collist)
   else:
      aggfuncs = aggfunc

   for col, aggfunc in zip(collist, aggfuncs):
      resultser = df.pivot_table(col, rows=rowlist, aggfunc=aggfunc)
      percentage = resultser / resultser[defindex] * 100
      percentage.name = '%'
      parts.append(resultser)
      parts.append(percentage)
   return pd.concat(parts, axis=1)

def quickToLatex(df, index_makros=False, **to_latex_kw):
   newdf = df.rename(columns={col:colformatlatex(col) for col in df.columns if col != '%'})
   if index_makros:
      newdf.rename(index={idx:colformatlatex(idx) for idx in newdf.index}, inplace=True)

   to_latex_kws = {key:val for key, val in itertools.chain(list(default_to_latex_kw.items()), list(to_latex_kw.items()))}
   return newdf.to_latex(**to_latex_kw)

def quickAggregationOnIndex(df, col, aggfunc=np.min, threshold=None):
    aggforindex = pd.Series(df.groupby(level=0).apply(lambda x:aggfunc(x[col])))
    newcolname = aggfunc.__name__ + col
    aggforindex.name = newcolname
    if threshold is None:
        return aggforindex
    else:
        newcolname += 'LE' + repr(threshold)
        return pd.Series(aggforindex <= threshold, name=newcolname)

def getWilcoxonQuotientSignificance(x, y, shiftby=10):
    shiftedquotients = (x + shiftby) / (y + shiftby)
    logshifted = np.log2(shiftedquotients)

    # filter elements that are too close to zero
    logshifted = logshifted[np.abs(logshifted) >= np.log2(1 + 1e-2)]
    if logshifted.size < 10:
        return np.nan
    try:
        return stats.wilcoxon(logshifted.values)[1]
    except ValueError:
        return np.nan

def quickAggregateAndSignificance(df, collist, rowlist, aggfunc=np.mean, wilcoxonfuncs=None, defindex=0):
   parts = []
   if type(aggfunc) is not list:
      aggfuncs = [aggfunc] * len(collist)
   else:
      aggfuncs = aggfunc

   pieces = dict(list(df.groupby(rowlist)[collist]))


   if wilcoxonfuncs is None:
      wilcoxonfuncs = [getWilcoxonQuotientSignificance] * len(collist)
   elif type(wilcoxonfuncs) is not list:
      wilcoxonfuncs = [wilcoxonfuncs] * len(collist)

   for col, aggfunc, wilcoxonfunc in zip(collist, aggfuncs, wilcoxonfuncs):
      resultser = df.pivot_table(col, rows=rowlist, aggfunc=aggfunc)
      percentage = resultser / resultser[defindex] * 100

      significance = pd.Series([wilcoxonfunc(pieces[resultser.index[defindex]][col], pieces[idx][col]) for idx in resultser.index], index=resultser.index)


      percentage.name = '%'
      significance.name = 'Wilcox'
      parts.append(resultser)
      parts.append(percentage)
      parts.append(significance)
   return pd.concat(parts, axis=1)
