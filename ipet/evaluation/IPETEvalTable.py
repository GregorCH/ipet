"""
The MIT License (MIT)

Copyright (c) 2018 Zuse Institute Berlin, www.zib.de

Permissions are granted as stated in the license file you have obtained
with this software. If you find the library useful for your purpose,
please refer to README.md for how to cite IPET.

@author: Gregor Hendel
"""
import pandas as pd
from toposort import toposort
from ipet.evaluation import Aggregation
import xml.etree.ElementTree as ElementTree
from .IPETFilter import IPETFilterGroup, IPETFilter
import numpy
from ipet.concepts.IPETNode import IpetNode, IpetNodeAttributeError
from ipet.misc import misc
import logging
from ipet import Experiment
from ipet import Key
from pandas.core.frame import DataFrame
from numpy import isnan
from ipet.evaluation.IPETFilter import IPETValue
from ipet.misc.misc import meanOrConcat
from ipet.validation import Validation
import sys

logger = logging.getLogger(__name__)


class IPETEvaluationColumn(IpetNode):

    DEFAULT_REDUCTION = "meanOrConcat"

    nodetag = "Column"

    editableAttributes = ["name", "origcolname", "formatstr", "transformfunc", "reduction", "constant",
                 "alternative", "minval", "maxval", "comp", "regex", "reductionindex"]

    possibletransformations = {None:(0, 0),
                               "abs":(1, 1),
                               "getGap":(2, 2),
                               "getCplexGap":(2, 2),
                               "getVariabilityScore":(1, -1),
                               "prod":(1, -1),
                               "sum":(1, -1),
                               "subtract":(2, 2),
                               "divide":(2, 2),
                               "log10":(1, 1),
                               "log":(1, 1),
                               "mean":(1, -1),
                               "shmean":(1, -1),
                               "median":(1, -1),
                               "std":(1, -1),
                               "min":(1, -1),
                               "max":(1, -1),
                               "getBestStatus" : (1, -1),
                               "getWorstStatus" : (1, -1),
                               "convertTimeStamp" : (1, 1),
                               "iqr" : (1, -1),
                               "lQuart" : (1, -1),
                               "uQuart" : (1, -1),
                               "strConcat" : (1, -1),
                               "meanOrConcat" : (1, -1)}

    possiblereductions = [None] + \
                        [k for k, v in possibletransformations.items() if v == (1, -1)] + \
                        ["shmean shift. by %d" % shift for shift in (1, 5, 10, 100, 1000)]

    possiblecomparisons = [None, "quot", "difference"] + ["quot shift. by %d" % shift for shift in (1, 5, 10, 100, 1000)]

    requiredOptions = {"comp":possiblecomparisons,
                       "origcolname":"datakey",
                       "transformfunc":list(possibletransformations.keys()),
                       "reduction" : possiblereductions}

    deprecatedattrdir = {"nanrep" : "has been replaced by 'alternative'",
                        "translevel" : "use a suitable reduction index instead"}

    def __init__(self, origcolname = None, name = None, formatstr = None, transformfunc = None, constant = None,
                 alternative = None, minval = None, maxval = None, comp = None, regex = None,
                 active = True, reduction = DEFAULT_REDUCTION, reductionindex = None, **kw):
        """
        constructor of a column for the IPET evaluation

        Parameters
        ----------
        origcolname : column name in the original data frame
        name : column name that will be displayed for this column
        formatstr : a format string to define how the column gets printed, if no format

        transformfunc : a transformation function, that should be applied to all children
                        columns of this column recursively. See also the 'translevel' attribute

        constant : should this column represent a constant value?

        alternative : conditional alternative constant or column name (also used to replace nans)

        minval : a minimum value for all elements in this column

        maxval : a maximum value for all elements in this column

        comp : should a comparison for this column with the default group be made? This will append one column per group with this column
               name and an appropriate suffix. Any nonexistent comp will raise a ValueError

        regex : use for selecting a set of columns at once by including regular expression wildcards such as '*+?' etc.

        active : True or "True" if this column should be active, False otherwise

        reduction : aggregation function that is applied to reduce multiple occurrences of index

        reductionindex : integer or string tuple (space separated)
        """

        super(IPETEvaluationColumn, self).__init__(active, **kw)
        self.origcolname = origcolname
        self.name = name

        self.formatstr = formatstr
        self.transformfunc = transformfunc
        self.constant = constant

        self.alternative = alternative
        self.minval = minval
        self.maxval = maxval
        self.set_comp(comp)
        self.regex = regex
        self.set_reduction(reduction)
        self.set_reductionindex(reductionindex)

        self.aggregations = []
        self.filters = []
        self.children = []

    def checkAttributes(self):
        if self.origcolname is None and self.regex is None and self.transformfunc is None and self.constant is None:
            raise IpetNodeAttributeError("origcolname", "No origcolname, regex, constant, or transformfunction specified")
        if self.transformfunc is not None:
            if self.transformfunc not in self.possibletransformations:
                raise IpetNodeAttributeError("transformfunc", "Unknown transformation <%s>" % (self.transformfunc))
            minval, maxval = self.possibletransformations[self.transformfunc]
            if len(self.children) < minval or maxval != -1 and len(self.children) > maxval:
                raise IpetNodeAttributeError("transformfunc", "wrong number of children for transformation <%s>" % (self.transformfunc))

        if self.reduction is not None:
            if self.reduction not in self.possiblereductions:
                raise IpetNodeAttributeError("Attribute 'reduction' has illegal value '%s'" % self.reduction)
        return True

    def isRegex(self) -> bool:
        """Is this a regular expression column

        Returns
        -------
        bool
            True if this column will search the data keys with a regular expression
        """
        return (self.regex is not None)

    def addChild(self, child):
        if not self.acceptsAsChild(child):
            raise ValueError("Cannot accept child %s as child of a column node" % child)
        if child.__class__ is IPETEvaluationColumn:
            self.children.append(child)
        elif child.__class__ is Aggregation:
            self.aggregations.append(child)
        elif child.__class__ is IPETFilter:
            self.filters.append(child)

    def getChildren(self):
        return self.children + self.aggregations + self.filters

    def acceptsAsChild(self, child):
        return child.__class__ in (IPETEvaluationColumn, Aggregation, IPETFilter)

    def removeChild(self, child):
        if child.__class__ is IPETEvaluationColumn:
            self.children.remove(child)
        elif child.__class__ is Aggregation:
            self.aggregations.remove(child)
        elif child.__class__ is IPETFilter:
            self.filters.remove(child)

    @staticmethod
    def getNodeTag():
        return IPETEvaluationColumn.nodetag

    def getEditableAttributes(self):
        return self.editableAttributes + super(IPETEvaluationColumn, self).getEditableAttributes()

    def getRequiredOptionsByAttribute(self, attr):
        return self.requiredOptions.get(attr, super(IPETEvaluationColumn, self).getRequiredOptionsByAttribute(attr))

    def getName(self):
        """
        infer the name for this column

        if this column was constructed with a column name, the name is used
        else if this column represents an original column of the data frame,
        the original column name is used, otherwise, we construct an
        artificial name that represents how this column is constructed
        """
        if self.name is not None:
            return self.name
        elif self.origcolname is not None:
            return self.origcolname
        elif self.regex is not None:
            return self.regex
        elif self.constant is not None:
            return "Const_%s" % self.constant
        else:
            prefix = self.transformfunc
            if prefix is None:
                prefix = ""
            return prefix + ','.join((child.getName() for child in self.children))

    def parseValue(self, val, df = None):
        """
        parse a value into an integer (prioritized) or float
        """
        if val in [None, ""]:
            return None
        for conversion in [int, float]:
            try:
                return conversion(val)
            except:
                pass
        if df is not None and val in df.columns:
            return df[val]
        return val

    def parseConstant(self):
        """
        parse the constant attribute, which is a string, into an integer (prioritized) or float
        """
        return self.parseValue(self.constant)

    def getActiveFilters(self):
        return [f for f in self.filters if f.isActive()]

    def addAggregation(self, agg):
        self.aggregations.append(agg)

    def addFilter(self, filter_):
        self.filters.append(filter_)

    def getFormatString(self):
        return self.formatstr

    def set_comp(self, newvalue):
        self.comp = None
        if not newvalue:
            self.comp = newvalue
        elif newvalue == "quot" or newvalue == "difference":
            self.comp = newvalue
        elif newvalue.startswith("quot shift"):
            try:
                _ = float(newvalue[newvalue.rindex(" "):])
                self.comp = newvalue
            except ValueError:
                raise ValueError("Trying to set an unknown comparison method '%s' for column '%s', should be in\n %s" % (newvalue, self.getName(), ", ".join((repr(c) for c in self.possiblecomparisons))))

    def set_reduction(self, reduction):
        """Set the reduction function
        """
        self.reduction = reduction

    def set_reductionindex(self, reductionindex):
        """Set the reduction index of this column
        None
        a custom reduction index to apply this columns reduction function.
        An integer n can be used to cause the reduction after the n'th
        index column (starting at zero) of the corresponding evaluation.
        If a negative integer -n is passed, this column creates its reduction index
        from the evaluation index before the element indexed by '-n'.
        If the desired reduction index is not a subset of the corresponding evaluation
        index, a string tuple can be passed to uniquely define the columns by which
        the reduced column should be indexed.

        Example: The parent evaluation uses a three-level index 'A', 'B', 'C'. The column
        should be reduced along the dimension 'B', meaning that the reduction yields
        a unique index consisting of all combinations of 'A' X 'C'. This reduction can
        be achieved by using "A C" as reduction index for this column.

        Note that the reduction index must be a subset of the parent evaluation index.

        Parameters
        ----------
        reductionindex
            integer or string (comma separated) reduction index for this column. None to use the entire index of the parent evaluation.

        """
        if reductionindex is None or type(reductionindex) is int or isinstance(reductionindex, StrList):
            self._reductionindex = reductionindex
        elif type(reductionindex) is str:
            try:
                self._reductionindex = int(reductionindex)
            except ValueError:
                self._reductionindex = StrList(reductionindex)
        self.reductionindex = reductionindex

    def getCompareColName(self):
        return self.getName() + self.getCompareSuffix()

    def getCompareMethod(self):
        if self.comp is None or self.comp == "":
            return None
        else:
            if self.comp == "quot":
                return numpy.true_divide
            elif self.comp == "difference":
                return numpy.subtract
            else:
                try:
                    shift = float(self.comp[self.comp.rindex(" "):])
                    return lambda x, y:numpy.true_divide(x + shift, y + shift)
                except ValueError:
                    return None

    def getCompareSuffix(self):
        if self.getCompareMethod() is not None:
            if self.comp == "quot":
                return "Q"
            elif self.comp == 'difference':
                return "D"
            else:
                return "Q+" + (self.comp[self.comp.rindex(" ") + 1:])
        return ""

    def attributesToStringDict(self):
        return {k:str(v) for k, v in self.attributesToDict().items() if v is not None}

    def toXMLElem(self):
        """
        convert this Column into an XML node
        """
        me = ElementTree.Element(IPETEvaluationColumn.getNodeTag(), self.attributesToStringDict())

        # iterate through children and aggregations and convert them to xml nodes
        for child in self.children:
            me.append(child.toXMLElem())

        for agg in self.aggregations:
            me.append(agg.toXMLElem())

        for filter_ in self.filters:
            me.append(filter_.toXMLElem())

        return me

    @staticmethod
    def processXMLElem(elem):

        if elem.tag == IPETEvaluationColumn.getNodeTag():
            column = IPETEvaluationColumn(**elem.attrib)
            for child in elem:
                if child.tag == 'Aggregation':
                    column.addAggregation(Aggregation.processXMLElem(child))
                elif child.tag == IPETFilter.getNodeTag():
                    column.addFilter(IPETFilter.processXMLElem(child))
                elif child.tag == IPETEvaluationColumn.getNodeTag():
                    column.addChild(IPETEvaluationColumn.processXMLElem(child))
            return column

    @staticmethod
    def getMethodByStr(funcname : str = DEFAULT_REDUCTION , modules = [numpy, misc]):
        """
        Find a method via name.

        Parameters
        ----------
        funcname
            string containing the name of the function
        modules
            list of modules to search for the function

        Return
        ------
            the requested function if it was found. Else an IpetNodeAttributeError is thrown.
        """
        for module in modules:
            try:
                return getattr(module, funcname)
            except AttributeError:
                pass
        raise IpetNodeAttributeError(funcname, "Unknown function %s" % funcname)

    def getTransformationFunction(self):
        """
        tries to find the transformation function from the numpy, misc, or Experiment modules
        """
        # Do we also have to search in module Key (for getWorstStatus etc)?
        return IPETEvaluationColumn.getMethodByStr(self.transformfunc, [numpy, misc, Experiment])

    def getReductionFunction(self):
        """
        tries to find the reduction function from the numpy, misc, or Experiment modules
        """
        if self.reduction is not None and self.reduction.startswith("shmean shift. by"):
            return lambda x:misc.shmean(x, shiftby = float(self.reduction.split()[-1]))
        else:
            return IPETEvaluationColumn.getMethodByStr(self.reduction, [numpy, misc, Experiment, Key.ProblemStatusCodes])

    def getReductionIndex(self, evalindexcols : list) -> list:
        """Return this columns reduction index, which is a subset of the evaluation index columns

        Parameters
        ----------
        evalindexcols
            list of evaluation index columns, may only contain a single element

        Returns
        -------
        list
            a list representing the (sub)set of columns representing this columns individual
            reduction index
        """
        if self._reductionindex is None:
            return list(evalindexcols)
        if type(self._reductionindex) is int:
            reductionindex = min(self._reductionindex, len(evalindexcols))
            # negative indices are also allowed
            reductionindex = max(reductionindex, -len(evalindexcols))
            return list(evalindexcols[:reductionindex])

        else:  # reduction index is a string tuple
            for c in self._reductionindex.getList():
                if c not in evalindexcols:
                    raise IpetNodeAttributeError(self.reduction, "reduction index column {} is not contained in evaluation index columns {}".format(c, evalindexcols))
            return self._reductionindex.getList()

    def getColumnData(self, df_long : DataFrame, df_target : DataFrame, evalindexcols : list) -> tuple:
        """
        Retrieve the data associated with this column

        Parameters
        ----------
        df_long
            DataFrame that contains original, raw data and already evaluated columns

        df_target
            DataFrame that has already been grouped to only been reduced to the target index columns

        Returns
        tuple
            (df_long, df_target, result)
                - df_long and df_target to which columns may have been appended
                - result is the column (or data frame) view in df_long

        """
        # if no children are associated with this column, it is either
        # a column represented in the data frame by an 'origcolname',
        # or a constant
        if len(self.children) == 0:
            if self.origcolname is not None:
                try:
                    result = df_long[self.origcolname]
                except KeyError as e:
                    # print an error message and make a series with NaN's
                    logger.warning("Could not retrieve data %s" % self.origcolname)
                    result = pd.Series(numpy.nan, index = df_long.index)

            #
            # filter for columns that match the regular expression
            #
            elif self.regex is not None:
                result = df_long.filter(regex = self.regex)

            #
            # store scalar constant
            #
            elif self.constant is not None:
                df_long[self.getName()] = self.parseConstant()
                result = df_long[self.getName()]
        else:
            # try to apply an element-wise transformation function to the children of this column
            # gettattr is equivalent to numpy.__dict__[self.transformfunc]
            transformfunc = self.getTransformationFunction()

            # concatenate the children data into a new data frame object
            childframes = []
            for child in self.children:
                df_long, df_target, childresult = child.getColumnData(df_long, df_target, evalindexcols)
                childframes.append(childresult)
            # argdf = df_long[[child.getName() for child in self.children if child.isActive()]]
            argdf = pd.concat(childframes, axis = 1)

            applydict = dict(axis = 1)

            try:
                # try to directly apply the transformation function, this might fail for
                # some transformations, e.g., the 'divide'-function of numpy because it
                # requires two arguments instead of the series associated with each row
                result = argdf.apply(transformfunc, **applydict)
            except (TypeError, ValueError):

                # try to wrap things up in a temporary wrapper function that unpacks
                # the series argument into its single values
                # e.g., wrap transformfunc((x,y)) as transformfunc(x,y)
                def tmpwrapper(*args):
                    return transformfunc(*(args[0].values))

                # apply the wrapper function instead
                result = argdf.apply(tmpwrapper, **applydict)

        if self.alternative is not None:
            alternative = self.parseValue(self.alternative, df_long)
            if alternative is not None:
                booleanseries = pd.isnull(result)
                for f in self.getActiveFilters():
                    booleanseries = numpy.logical_or(booleanseries, f.applyFilter(df_long).iloc[:, 0])
                result = result.where(~booleanseries, alternative)
        if self.minval is not None:
            minval = self.parseValue(self.minval, df_long)
            if minval is not None:
                if type(minval) in [int, float]:
                    result = numpy.maximum(result, minval)
                else:
                    comp = minval.astype(result.dtype)
                    try:
                        result = numpy.maximum(result, comp)
                    except:
                        logger.warning("When filling in the minimum, an error occurred for the column '{}':\n{}".format(self.getName(), self.attributesToStringDict()))
                        result = pd.concat([result, comp], axis = 1).max(axis = 1)
        if self.maxval is not None:
            maxval = self.parseValue(self.maxval, df_long)
            if maxval is not None:
                if type(maxval) in [int, float]:
                    result = numpy.minimum(result, maxval)
                else:
                    comp = maxval.astype(result.dtype)
                    try:
                        result = numpy.minimum(result, comp)
                    except:
                        logger.warning("When filling in the maximum, an error occurred for the column '{}':\n{}".format(self.getName(), self.attributesToStringDict()))
                        result = pd.concat([result, comp], axis = 1).min(axis = 1)

        reductionindex = self.getReductionIndex(evalindexcols)

        #
        # do not append frames with more than column. (They will be transformed at a higher level)
        #
        if len(result.shape) > 1:
            if result.shape[1] > 1:
                return df_long, df_target, result
            else:
                # a dataframe with only one column: select that one to get a series to work with in further code
                result = result[result.columns[0]]

        if len(reductionindex) > 0:
            # apply reduction and save the result by joining it into both data frames
            nrows_long = df_long.shape[0]
            nrows_target = df_target.shape[0]

            df_long[self.getName()] = result
            # the number of rows in the long and the target data frame is equal
            # computations are faster in this case because the target result
            # is simply a permutation of the result
            #
            if nrows_long == nrows_target and reductionindex == evalindexcols:

                # ## set index for the join operation
                targetresult = result.copy()
                targetresult.index = df_long.set_index(evalindexcols).index
                targetresult = targetresult.rename(self.getName())

            else:
                #
                # reduction index is smaller than the evalindex, perform a reduction
                # based on the defined reduction index
                targetresult = df_long.groupby(by = reductionindex)[self.getName()].apply(self.getReductionFunction())

                #
                # The join operations resamples the possibly reduced result based on the reduction index
                #
                df_long = df_long.join(targetresult, on = reductionindex, lsuffix = "_old")

            #
            # this column should usually not appear in the target, yet. A join operation is necessary
            # because the index of this frame is a permuted version of the original data frame
            #
            if not self.getName() in df_target:
                df_target = df_target.join(targetresult, on = reductionindex, lsuffix = "_old")
        else:
            #
            # add scalar to both data frames
            #
            scalar = self.getReductionFunction()(result)
            df_long[self.getName()] = scalar
            if not self.getName() in df_target:
                df_target[self.getName()] = scalar

        return df_long, df_target, result

    def getStatsTests(self):
        return [agg.getStatsTest() for agg in self.aggregations if agg.getStatsTest() is not None]

    def addDependency(self, dependencies, dep):
        if dep not in dependencies[self.getName()]:
            dependencies[self.getName()].add(dep)

    def getDependencies(self):
        """Return a list of data frame column names that this column requires
        """
        dependencies = {self.getName() : set()}
        if self.origcolname is not None:
            self.addDependency(dependencies, self.origcolname)
        for c in [self.minval, self.alternative, self.maxval]:
            if c is not None and self.parseValue(c) is None:
                self.addDependency(dependencies, c)
        for i in self.children:
            self.addDependency(dependencies, i.getName())
            dependencies.update(i.getDependencies())
        for i in self.filters:
            for j in [1, 2]:
                dep = i.getDependency(j)
                if dep is not None:
                    self.addDependency(dependencies, dep)

        return dependencies

    def getStatsColName(self, statstest):
        """Return the column name of the statstest"""
        return '_'.join((self.getName(), statstest.__name__))

    def getAllStatsColNames(self, statstest):
        """Return a list of the column names of all statstests"""
        return [self.getStatsColName(statstest) for statstest in self.getStatsTests()]

    def getAggColName(self, aggr):
        """Return the column name of the aggrecation"""
        return '_'.join((self.getName(), aggr.getName()))

    def getAllAggColNames(self):
        """Return a list of the column names of all aggregations"""
        return [self.getAggColName(aggr) for aggr in self.aggregations]

    def hasCompareColumn(self, title):
        if title == "":
            return False
        if title == self.getCompareColName():
            # title is a compare column of the long table
            return True
        if title[-1] in ["Q", "p"]:
            if title[:-1] in self.getAllAggColNames():
                # title is a compare column of aggregated table or statistical test column
                return True
        return False

    def hasDataColumn(self, title):
        if title == "":
            return False
        if title == self.getName():
            # title is a data column of the long table
            return True
        if title in self.getAllAggColNames():
            # title is a compare column of aggregated table or statistical test column
            return True
        return False


class FormatFunc:

    def __init__(self, formatstr):
        self.formatstr = formatstr[:]

    def beautify(self, x):
        return (self.formatstr % x)


class StrList:
    """
    Represents an easier readible and parsable list of strings
    """

    def __init__(self, strList, splitChar = " "):
        self.list = StrList.splitStringList(strList, splitChar)
        self.splitChar = splitChar

    @staticmethod
    def splitStringList(strList, splitChar = " "):
        """Split a string that represents list elements separated by optional split-character
        """
        if strList is None or strList == "":
            return None
        elif type(strList) is str:
            if splitChar == " ":
                return strList.split()
            else:
                return strList.split(splitChar)
        else:
            return list(strList)

    def getList(self):
        if self.list is None:
            return []
        return self.list

    def __str__(self):
        if self.list is None:
            return ""
        return self.splitChar.join(self.list)


class IPETEvaluation(IpetNode):
    """
    evaluates a comparator with given group keys, columns, and filter groups

    An evaluation transfers raw, collected data from a collection of testruns
    into tables based on selected columns, filter groups, and aggregations.
    An evaluation and its friends come with an easy-to-modify XML language
    for modification.
    By defining multiple evaluations,
    it is therefore possible to view the same raw data through multiple angles

    """
    nodetag = "Evaluation"
    # todo put tex, csv etc. here as other possible streams for filter group output
    possiblestreams = ['stdout', 'tex', 'txt', 'csv']
#    DEFAULT_GROUPKEY = "Settings"
    DEFAULT_GROUPKEY = Key.ProblemStatus
    DEFAULT_COMPARECOLFORMAT = "%.3f"
    DEFAULT_INDEX = " ".join([Key.ProblemName, Key.LogFileName])
    DEFAULT_INDEXSPLIT = -1
    ALLTOGETHER = "_alltogether_"

    editableAttributes = ["defaultgroup", "sortlevel", "comparecolformat", "grouptags", "index", "indexsplit", "validate", "suppressions", "fillin", "integral"]
    attributes2Options = {
        "grouptags" : [True, False],
        "fillin" : [True, False]
    }

    deprecatedattrdir = {"groupkey" : "groupkey is specified using 'index' and 'indexsplit'",
                         "evaluateoptauto" : "Optimal auto settings are no longer available, use reductions instead"}

    def __init__(self, defaultgroup = None,
                 sortlevel = None, comparecolformat = DEFAULT_COMPARECOLFORMAT,
                 index = DEFAULT_INDEX, indexsplit = DEFAULT_INDEXSPLIT,
                 validate = None, suppressions = None, grouptags = None, fillin = None, integral = None, **kw):
        """
        constructs an Ipet-Evaluation

        Parameters
        ----------
        defaultgroup : the values of the default group to be compared with, if left empty a defaultgroup is generated
        sortlevel : int or None, level on which to base column sorting, default: None (for no sorting)
        comparecolformat : format string for comparison columns
        index : (string or list or None) single or multiple column names that serve as (row) and column index levels, if 'auto' an index is generated.
        indexsplit : (int) position to split index into row and column levels, negative to count from the end.
        validate : (string) for the relative or absolute location of a solu file for validation.
        suppressions : (string) column names that should be excluded from output (as comma separated list of simple strings or regular expressions).
        grouptags : (bool) True if group tags should be displayed in long table, otherwise False
        fillin : (bool) True if missing data should be filled in, otherwise False
        integral : a string that specifies how to compute primal and dual integrals. Examples are 'unscaled 600 None' or 'scaled 0.5 1.0'.
                    Specifying an integral leads to a recomputation of integrals by the experiment.
        """

        # construct super class first, Evaluation is currently always active
        super(IPETEvaluation, self).__init__(True, **kw)

        self.filtergroups = []
        self.comparecolformat = comparecolformat[:]
        self.columns = []
        self.evaluated = False
        self.feastol = None
        self.gaptol = None

        self.defaultgroup = defaultgroup
        self.set_index(index)
        self.set_indexsplit(indexsplit)
        self.set_sortlevel(sortlevel)
        self.set_grouptags(grouptags)
        self.set_fillin(fillin)
        self.integral = integral

        self.set_validate(validate)
        self.suppressions = suppressions

    def getName(self):
        return self.nodetag

    def set_grouptags(self, grouptags):

        if grouptags not in [None, "", False, "False"]:
            self.grouptags = True
        else:
            self.grouptags = False

    def set_fillin(self, fillin):

        if fillin not in [None, "", False, "False"]:
            self.fillin = True
        else:
            self.fillin = False

    def isEvaluated(self):
        """
        returns whether this evaluation has been evaluated since its columns or filter groups have been modified
        """
        return self.evaluated

    def setEvaluated(self, evaluated):
        """
        change the flag if this evaluation has been evaluated since its last modification
        """
        self.evaluated = evaluated

    def set_sortlevel(self, sortlevel):
        self.sortlevel = int(sortlevel) if sortlevel is not None else None

        if self.sortlevel is not None and self.getColIndex() != []:
            ncols = len(self.getColIndex()) + 1
            if self.sortlevel >= ncols:
                logger.warning("Sortlevel too large: Value ({}) needs to be in [0, {}].".format(self.sortlevel, ncols - 1))

    def setCompareColFormat(self, comparecolformat):
        self.comparecolformat = comparecolformat[:]

    def attributesToStringDict(self):
        return {k:str(v) for k, v in self.attributesToDict().items() if v is not None and str(v) != ""}

    @staticmethod
    def getNodeTag():
        return IPETEvaluation.nodetag

    def getEditableAttributes(self):
        return self.editableAttributes

    def getChildren(self):
        return self.columns + self.filtergroups

    def acceptsAsChild(self, child):
        return child.__class__ in (IPETEvaluationColumn, IPETFilterGroup)

    def addChild(self, child):
        if not self.acceptsAsChild(child):
            raise ValueError("Cannot accept child %s as child of an evaluation node" % child)
        if child.__class__ is IPETEvaluationColumn:
            self.columns.append(child)
        elif child.__class__ is IPETFilterGroup:
            self.filtergroups.append(child)

        self.setEvaluated(False)

    def removeChild(self, child):
        if child.__class__ is IPETEvaluationColumn:
            self.columns.remove(child)
        elif child.__class__ is IPETFilterGroup:
            self.filtergroups.remove(child)

        self.setEvaluated(False)

    def getRequiredOptionsByAttribute(self, attr):
        return self.attributes2Options.get(attr, super(IPETEvaluation, self).getRequiredOptionsByAttribute(attr))

    def addFilterGroup(self, fg):
        # check if a filter group of the same name already exists
        if fg.getName() in (fgroup.getName() for fgroup in self.filtergroups):
            raise ValueError("Error: Filter group of name <%s> already existing in current evaluation!" % fg.getName())

        self.filtergroups.append(fg)
        self.setEvaluated(False)

    def removeFilterGroup(self, fg):
        self.filtergroups.remove(fg)
        self.setEvaluated(False)

    def set_index(self, index : list):
        """Set index identifier list
        """
        self.autoIndex = False
        self.index = index
        self._index = StrList(index)
        logger.debug("Set index to '{}'".format(index))
        if index == "auto":
            self.autoIndex = True
            return

    def getRowIndex(self) -> list:
        """Return (list of) keys to create row index
        """
        return self.getIndex()[:self.indexsplit]

    def getColIndex(self) -> list:
        """Return (list of) keys to create column index
        """
        return self.getIndex()[self.indexsplit:]

    def getIndex(self) -> list:
        """Return all index columns as a list
        """
        return self._index.getList()

    def getDefaultgroup(self, data):
        """Return tuple representation of defaultgroup

        Parameters:
        data
            data frame object with columns that match the specified column index
        """

        # split the default group on colons
        dg = StrList.splitStringList(self.defaultgroup, ":")
        if dg is None:
            x = None
        else:
            # try casting as many to float as possible
            x = list(dg)
            for i in range(len(x)):
                try:
                    x[i] = float(x[i])
                except:
                    pass

        defaultgroup = None

        # try to match the length of x to the length of the specified column index
        if x is not None:
            if len(x) > len(self.getColIndex()):
                x = x[:len(self.getColIndex())]
            if len(x) == 1:
                defaultgroup = x[0]
            else:
                defaultgroup = tuple(x)
            #
            # check if this group is contained
            #
            if self.defaultgroupIsContained(defaultgroup, data):
                return defaultgroup

        #
        # the default group is None or not contained
        # -> use first element in the data frame
        #
        if len(self.getColIndex()) == 1:
            return data[self.getColIndex()].iloc[0, :].values[0]
        else:
            return tuple(data.iloc[0][self.getColIndex()])

    def set_defaultgroup(self, dg : str):
        """Set defaultgroup

        Parameters
        ----------
        dg
            string representation of the defaultgroup in format "val1:val2:val3", or None
        """
        self.defaultgroup = dg
        logger.debug("Set defaultgroup to {}".format(self.defaultgroup))
        self.setEvaluated(False)

    def set_indexsplit(self, indexsplit):
        self.indexsplit = int(indexsplit)
        # make sure that we have at least one col as rowindex
        if self.index is not None and not self.autoIndex:
            self.indexsplit = min(len(self.index), self.indexsplit)

    def addColumn(self, col):
        self.columns.append(col)
        self.setEvaluated(False)

    def removeColumn(self, col):
        self.columns.remove(col)
        self.setEvaluated(False)

    def set_suppressions(self, suppressions: str):
        """Sets suppressions attribute to the argument of this function
        """
        self.suppressions = suppressions

    def addComparisonColumns(self, df: DataFrame) -> DataFrame:
        """ Add the comparison columns.

        Add the specified comparison columns to df, returns extended df in the same format

        Parameters
        ----------
        df
            DataFrame containing only relevant data.
            df has ids as index. The indexkeys are columns.

        Returns
        -------
        DataFrame
            The original DataFrame with the extra columns appended.
        """
        if self.getColIndex() == []:
            return df
        usercolumns = []

        dg = self.getDefaultgroup(df)

        for col in self.toposortColumns(self.getActiveColumns()):
            # look if a comparison with the default group should be made
            if col.getCompareMethod() is not None:

                df_bar = df.set_index(self.getRowIndex(), drop = True)
                grouped = df_bar.groupby(by = self.getColIndex())[col.getName()]
                compcol = dict(list(grouped))[dg]
                comparecolname = col.getCompareColName()

                # apply the correct comparison method to the original and the temporary column
                compmethod = col.getCompareMethod()
                method = lambda x:compmethod(*x)

                df[comparecolname] = 0
                df.set_index(self.getIndex(), inplace = True)
                for name, group in grouped:
                    tmpgroup = DataFrame(group)
                    tmpgroup["_tmpcol_"] = compcol
                    tmpgroup[comparecolname] = tmpgroup[[col.getName(), "_tmpcol_"]].apply(method, axis = 1)  # .set_index(group.index)
#
                    colindex = self.getColIndex()
                    if len(colindex) > 1:
                        for n, i in zip(name, colindex):
                            tmpgroup[i] = n
                    else:
                        tmpgroup[colindex[0]] = name

                    tmpgroup.reset_index(drop = False, inplace = True)
                    tmpgroup.set_index(self.getIndex(), inplace = True)

                    newvals = tmpgroup[comparecolname]

                    df[comparecolname].update(newvals)

                df.reset_index(drop = False, inplace = True)
                usercolumns.append(comparecolname)

        # TODO Sort usercolumns?
        self.usercolumns = self.usercolumns + usercolumns
        return df

    def reduceToColumns(self, df_long : DataFrame, df_target : DataFrame) -> tuple:
        """ Reduce the huge number of columns

        The data frame is reduced to the columns of the evaluation.
        (concatenate usercolumns, neededcolumns and additionalfiltercolumns from df_long)

        Parameters
        ----------
        df_long
            DataFrame returned by Experiment with preprocessed columns '_count_', '_solved_', etc..

            Dataframe to evaluate, mostly joined data from an experiment,
            that contains the necessary columns required by this evaluation.
            For example: A dataframe containing the parsed data from one or
            multiple .trn files created by ipet-parse.

        df_target
            DataFrame with preprocessed columns that contain the index column

        Returns
        -------
        tuple
            df_long, df_target after processing the user columns
        """

        # We are only interested in the columns that are currently active
        usercolumns = [c.getName() for c in self.getActiveColumns()]
        evalindexcols = self.getIndex()

        #
        # loop over a topological sorting of the active columns to compute
        #
        for col in self.toposortColumns(self.getActiveColumns()):
            try:
                df_long, df_target, _ = col.getColumnData(df_long, df_target, evalindexcols)
            except Exception as e:
                logger.warning("An error occurred for the column '{}':\n{}".format(col.getName(), col.attributesToStringDict()))
                raise e
            logger.debug("Target data frame : \n{}\n".format(df_target))

        newcols = [Key.ProblemStatus, Key.SolvingTime, Key.TimeLimit, Key.ProblemName]

        self.usercolumns = usercolumns

        return df_target

    def fillMissingData(self, data):
        """
        Fill in missing elements to ensure that all possible index combinations are available.

        Parameters
        ----------
        data
            the dataframe

        Returns
        -------
        newdata
            dataframe filled with missing data
        """
        list_list = [list(set(data[i])) for i in self.getIndex()]
        data["_miss_"] = False
        newind = pd.MultiIndex.from_product(list_list, names=self.getIndex())
        if len(newind) < len(data):
            raise AttributeError("Index not unique, cannot fill in data. Exiting.")
        newdata = data.set_index(self.getIndex()).reindex(newind).reset_index()

        newdata["_miss_"].fillna(value=True, inplace=True)
        newdata[Key.ProblemStatus].fillna(Key.ProblemStatusCodes.Missing, inplace=True)

        return newdata

    def toposortColumns(self, columns : list) -> list:
        """ Compute a topological ordering respecting the data dependencies of the specified column list.

        Parameters
        ----------
        columns
            A list of the column-objects to be sorted.

        Returns
        -------
        list
            A list of topologically sorted column objects.
        """
        adj = self.getDependencies(columns)

        toposorted = list(toposort(adj))
        logger.debug("TOPOSORT:\nDependency List: {},\nTopological Ordering: {}".format(adj, toposorted))

        def getIndex(name, toposorted):
            for idx, topo in enumerate(toposorted):
                if name in topo: return idx
            return -1

        indices = {col.getName() : getIndex(col.getName(), toposorted) for col in columns}

        return sorted(columns, key = lambda x: indices.get(x.getName(), -1))

    def getDependencies(self, columns : list) -> dict:
        """ Recursively collect the dependencies of a list of columns.

        Parameters
        ----------
        columns
            A list of columns

        Returns
        -------
            A dictionary containing the names and dependencies of the columns.
        """
        adj = {}
        for col in columns:
            newdeps = col.getDependencies()
            for key, val in newdeps.items():
                adj.setdefault(key, set()).update(val)
        return adj

    def getValidate(self):
        """this evaluations validation attribute

        Returns
        -------
        string
            either the current validation file as a string, or None if unspecified.
        """
        return self.validate

    def set_validate(self, validate):
        """sets this evaluation's validation attribute

        Parameters
        ----------

        validate : str or None
            new value for the source of validation information for this evaluation
        """
        self.validate = validate

    def set_gaptol(self, gaptol):
        """sets this evaluation's gaptol attribute

        Parameters
        ----------

        gaptol : str or float
            new value for the gaptol for this evaluation
        """
        self.gaptol = gaptol

    def set_feastol(self, feastol):
        """sets this evaluation's feastol attribute

        Parameters
        ----------

        feastol : str or float
            new value for the feastol for this evaluation
        """
        self.feastol = feastol

    def validateData(self, df : DataFrame) -> DataFrame:
        """validate data based on external solution information
        """

        if not self.validate:

            logger.info("No validation information specified")
            file_exists = False
        else:
            try:
                f = open(self.validate, "r")
                f.close()
                file_exists = True
                logger.info("Validation information provided: '{}'".format(self.validate))
            except:
                file_exists = False
                logger.warning("Could not open validation file '{}'".format(self.validate))

        if file_exists:
            v = Validation(self.validate)
        else:
            v = Validation(None)
        if self.feastol:
            try:
                v.set_feastol(float(self.feastol))
            except:
                pass
        if self.gaptol:
            try:
                v.set_tol(float(self.gaptol))
            except:
                pass

        result = v.validate(df)

        logger.info("Validation resulted in the following status codes: [{}]".format(
            "|".join([" {}: {} ".format(k, v) for k, v in result.value_counts().items()])))

        df[Key.ProblemStatus] = result
        return df

    def calculateNeededData(self, df : DataFrame) -> DataFrame:
        """ Add the status columns.

        Calculate and append needed data about statuses

        Parameters
        ----------
        df
            DataFrame containing only relevant data.
            df has ids as index. The indexkeys are columns.

        Returns
        -------
        DataFrame
            The original DataFrame with the extra columns appended.
        """

        df['_time_'] = (df[Key.ProblemStatus].isin((Key.ProblemStatusCodes.Better, Key.ProblemStatusCodes.TimeLimit)))
        # df['_time_'] = (df[Key.ProblemStatus] == Key.ProblemStatusCodes.TimeLimit)
        df['_limit_'] = ((df['_time_']) | df[Key.ProblemStatus].isin([Key.ProblemStatusCodes.NodeLimit,
                                                                      Key.ProblemStatusCodes.MemoryLimit,
                                                                      Key.ProblemStatusCodes.Interrupted
                                                                      ]))
        df['_primfail_'] = df[Key.ProblemStatus].isin([
                                                    Key.ProblemStatusCodes.FailObjectiveValue,
                                                    Key.ProblemStatusCodes.FailSolInfeasible,
                                                    Key.ProblemStatusCodes.FailSolOnInfeasibleInstance,
                                        ])

        df['_dualfail_'] = df[Key.ProblemStatus].isin([Key.ProblemStatusCodes.FailDualBound])

        df['_fail_'] = df['_primfail_'] | \
            df['_dualfail_'] | \
            df[Key.ProblemStatus].isin([Key.ProblemStatusCodes.FailReaderror,
                                         Key.ProblemStatusCodes.FailInconsistent,
                                         Key.ProblemStatusCodes.Fail])

        df['_abort_'] = (df[Key.ProblemStatus] == Key.ProblemStatusCodes.FailAbort)

        df['_solved_'] = (~df['_limit_']) & (~df['_fail_']) & (~df['_abort_']) & (~df['_miss_'])

        df['_count_'] = 1
        df['_unkn_'] = (df[Key.ProblemStatus] == Key.ProblemStatusCodes.Unknown)
        self.countercolumns = ['_time_', '_limit_', '_primfail_', '_dualfail_', '_fail_', '_abort_', '_solved_', '_unkn_', '_count_', '_miss_']
        return df

    def toXMLElem(self):
        me = ElementTree.Element(IPETEvaluation.getNodeTag(), self.attributesToStringDict())
        for col in self.columns:
            me.append(col.toXMLElem())
        for fg in self.filtergroups:
            fgelem = fg.toXMLElem()
            me.append(fgelem)
        return me

    @staticmethod
    def fromXML(xmlstring):
        tree = ElementTree.fromstring(xmlstring)
        return IPETEvaluation.processXMLElem(tree)

    @staticmethod
    def fromXMLFile(xmlfilename):
        tree = ElementTree.parse(xmlfilename)
        return IPETEvaluation.processXMLElem(tree.getroot())

    @staticmethod
    def processXMLElem(elem):
        if elem.tag == IPETEvaluation.getNodeTag():
            logger.debug("Construct IPET Evaluation with attributes : \n{}".format(elem.attrib))
            ev = IPETEvaluation(**elem.attrib)

        for child in elem:
            if child.tag == IPETFilterGroup.getNodeTag():
                # add the filter group to the list of filter groups
                fg = IPETFilterGroup.processXMLElem(child)
                ev.addFilterGroup(fg)

            elif child.tag == IPETEvaluationColumn.getNodeTag():
                ev.addColumn(IPETEvaluationColumn.processXMLElem(child))
        return ev

    def reduceByIndex(self, df : DataFrame) -> DataFrame:
        """ Reduce data to have a unique index given by indexkeys.

        Each column is reduced by it's reduction function such that indexkeys yield a unique hierarchical index.

        Parameters
        ----------
        df
            DataFrame containing data to be reduced.
            df has ids as index. The indexkeys are columns.

        Returns
        -------
        DataFrame
            The reduced DataFrame.
        """
        grouped = df.groupby(by = self.getIndex())

        newcols = []

        reductionMap = {'_solved_' : numpy.all, '_count_' : numpy.max}
        for col in self.countercolumns:
            newcols.append(grouped[col].apply(reductionMap.get(col, numpy.any)))

        #
        # compute additional, requested columns for filters
        #
        activecolumns = [c.getName() for c in self.getActiveColumns()]
        additionalfiltercolumns = []
        for fg in self.getActiveFilterGroups():
            additionalfiltercolumns += fg.getNeededColumns(df)

        additionalfiltercolumns = list(set(additionalfiltercolumns))
        additionalfiltercolumns = [afc for afc in additionalfiltercolumns if afc not in set(activecolumns + self.countercolumns + self.getIndex())]

        for col in additionalfiltercolumns:
            newcols.append(grouped[col].apply(meanOrConcat))

        reduceddf = pd.concat(newcols, axis = 1)
        ind = self.getIndex()
        index_uniq = [i for i in ind if i not in reduceddf.columns]
        index_dupl = [i for i in ind if i in reduceddf.columns]

        reduceddf = reduceddf.reset_index(index_uniq)
        reduceddf = reduceddf.reset_index(index_dupl, drop = True)

        #
        # search for duplicate column names to avoid cryptic error messages later
        #

        if True in reduceddf.columns.duplicated():
            raise ValueError("Duplicate columns {} in reduced data frame, aborting".format(reduceddf.columns.get_duplicates()))

        return reduceddf

    def convertToHorizontalFormat(self, df : DataFrame) -> DataFrame:
        """ Convert data to have an index given by indexkeys.

        Indexkeys are defined by "index" and "columnindex", these yield a unique index.
        indexkeys[0] is taken as (hierarchical) row index,
        indexkeys[1] is taken as (hierarchical) column index.

        Parameters
        ----------
        df
            DataFrame containing data to be converted.
            df has ids as index. The indexkeys are columns.

        Returns
        -------
        DataFrame
            The converted DataFrame.
        """
        #
        # restrict the columns to those that should appear in
        # the final table, but make sure that no columns
        # appear twice. Respect also the order of the columns
        #
        columns = []
        colset = set()
        for c in self.usercolumns + self.getIndex() + ["groupTags"]:
            if c not in colset and c not in self.countercolumns and c in df.columns:
                columns.append(c)
                colset.add(c)

        df = df[columns].set_index(self.getIndex()).sort_index(level = 0)
        df = df.unstack(self.getColIndex())
        if len(self.getColIndex()) > 0 :
            df = df.swaplevel(0, len(self.getColIndex()), axis = 1)
        return df

    def checkStreamType(self, streamtype):
        if streamtype not in self.possiblestreams:
            return False
        else:
            return True

    def getActiveFilterGroups(self):
        return [fg for fg in self.filtergroups if fg.isActive()]

    def getActiveColumns(self):
        return [col for col in self.columns if col.isActive()]

    def getColumnFormatters(self, df):
        """
        returns a formatter dictionary for all columns of this data frame

        expects a Multiindex column data frame df
        """
        all_colnames = df.columns
        if len(all_colnames) == 0:
            return {}
        formatters = {}
        l = 0
        if not isinstance(all_colnames[0], str):
            l = len(all_colnames[0]) - 1

        comptuples = []
        # loop over columns
        for col in self.getActiveColumns():

            colname = col.getName()

            # determine all comparison columns and append them to the list
            if col.getCompareMethod() is not None:
                if l == 0:
                    comptuples += [dfcol for dfcol in all_colnames if col.hasCompareColumn(dfcol)]
                else:
                    comptuples += [dfcol for dfcol in all_colnames if col.hasCompareColumn(dfcol[l])]

            # if the column has no formatstr attribute, continue
            colformatstr = col.getFormatString()
            if not colformatstr:
                continue

            # for long table: retrieve all columns as tuples that contain the column name, ie. for column 'Time' and
            # settings 'default' and 'heuroff', the result should be [('default', 'Time'),('heuroff', 'Time')]
            if l == 0:
                tuples = [dfcol for dfcol in all_colnames if col.hasDataColumn(dfcol)]
            else:
                tuples = [dfcol for dfcol in all_colnames if col.hasDataColumn(dfcol[l])]

            # add new formatting function to the map of formatting functions
            for thetuple in tuples:
                formatters.update({thetuple:FormatFunc(colformatstr).beautify})

        # display countercolumns as integer
        counting_columns = [dfcol for dfcol in all_colnames if dfcol[l].startswith("_") and dfcol[l].endswith("_")]
        for cctup in counting_columns:
            formatters.update({cctup:FormatFunc("%.0f").beautify})

        for comptuple in comptuples:
            formatters.update({comptuple:FormatFunc(self.comparecolformat).beautify})

        return formatters

    def sortDataFrame(self, df):
        if self.sortlevel is not None:
            return df.sort_index(level = self.sortlevel, axis = 1, inplace = False)
        else:
            return df

    def suppressColumns(self, df : DataFrame) -> DataFrame:
        """Returns a new data frame with all columns removed that match the suppressions attribute
        """
        if not self.suppressions:  # None or empty string
            return df

        suppressions = self.suppressions.split()
        df_reduced = df.copy()

        for suppression in suppressions:
            df_reduced.drop(list(df_reduced.filter(regex = suppression)), axis = 1, inplace = True)

        return df_reduced

    def streamDataFrame(self, df, filebasename, streamtype):
        df = self.sortDataFrame(df)

        df = self.suppressColumns(df)

        if not self.checkStreamType(streamtype):
            raise ValueError("Stream error: Unknown stream type %s" % streamtype)
        streammethod = getattr(self, "streamDataFrame_%s" % streamtype)

        formatters = self.getColumnFormatters(df)

        streammethod(df, filebasename, formatters)

    def streamDataFrame_stdout(self, df, filebasename, formatters = {}):
        """
        print to console
        """
        print("%s:" % filebasename)
        print(df.to_string(formatters = formatters))

    def streamDataFrame_tex(self, df : DataFrame, filebasename, formatters = {}):
        """
        write tex output
        """
        with open("%s.tex" % filebasename, "w") as texfile:
            texfile.write(df.to_latex(formatters = formatters))

    def flatten_index(self, col) -> str:
        if type(col) is tuple:
            return '_'.join(map(str, col[::-1]))
        else:
            return col

    def streamDataFrame_csv(self, df : DataFrame, filebasename, formatters = {}):
        with open("%s.csv" % filebasename, "w") as csvfile:
            #
            # obviously, the support for custom csv formatters was dropped
            # at some pandas update. This is not terrible as
            # usually, a csv file is an intermediate product, anyway,
            # and the tool that gets the csv as input can handle
            # the final formatting.
            #
            logger.warn("Warning. Custom formatting ignored for csv output")

            df.columns = [self.flatten_index(col) for col in df.columns]
            df.to_csv(csvfile)

    def streamDataFrame_txt(self, df : DataFrame, filebasename, formatters = {}):
        """
        write txt output
        """
        with open("%s.txt" % filebasename, "w") as txtfile:
            df.to_string(txtfile, formatters = formatters, index_names = False, sparsify = False)

    def findStatus(self, statuscol):
        uniques = set(statuscol.unique())
        for status in ["ok", "timelimit", "nodelimit", "memlimit", "unknown", "fail", "abort"]:
            if status in uniques:
                return status
        else:
            return statuscol.unique()[0]

    def checkMembers(self):
        """
        checks the evaluation members for inconsistencies
        """
        if self.columns == []:
            raise AttributeError("Please specify at least one column.")
        for col in self.columns:
            try:
                col.checkAttributes()
            except Exception as e:
                raise AttributeError("Error in column definition of column %s:\n   %s" % (col.getName(), e))
            if col.isRegex():
                raise AttributeError("Top level column {} must not specify a regular expression".format(col.getName()))

    def getAggregatedGroupData(self, filtergroup):
        if not filtergroup in self.filtergroups:
            raise ValueError("Filter group %s (name:%s) is not contained in evaluation filter groups" % (filtergroup, filtergroup.getName()))
        if  not filtergroup.isActive():
            raise ValueError("Filter group %s is currently not active" % filtergroup.getName())

        return self.filtered_agg.get(filtergroup.getName(), DataFrame())

    def getInstanceGroupData(self, filtergroup):
        if not filtergroup in self.filtergroups:
            raise ValueError("Filter group %s (name:%s) is not contained in evaluation filter groups" % (filtergroup, filtergroup.getName()))
        if  not filtergroup.isActive():
            raise ValueError("Filter group %s is currently not active" % filtergroup.getName())
        return self.filtered_instancewise.get(filtergroup.getName(), DataFrame())

    def getAggregatedData(self):
        return self.retagg

    def getInstanceData(self):
        return self.rettab

    def defaultgroupIsContained(self, group, data) -> bool:
        '''
        Check if the given group is contained in the data.

        Parameters
        ----------
        group
            scalar or tuple representing a default group
        data
            raw DataFrame
        Returns
        -------
        bool
            True if the group is found, else False
        '''
        #
        # check if the column index and the group have equal length
        # (be careful about group being string)
        #
        cIndex = self.getColIndex()
        if type(group) is tuple and len(group) != len(cIndex):
            return False
        elif type(group) is not tuple and len(cIndex) > 1:
            return False

        #
        # depending on the length of the column index, different methods apply
        #
        if len(cIndex) == 1:
            #
            # use scalar comparison
            #
            return numpy.any(data[self.getColIndex()] == group)
        else:
            #
            # use conjunction of scalar comparisons (this is not fast)
            #
            result = True
            for idx, l in enumerate(cIndex):
                result = result & (data[l] == group[idx])
            return numpy.any(result)

    def tryGenerateIndexAndDefaultgroup(self, data):
        '''
        Generate a reasonable index and defaultgroup based on the given data

        Take a look at the columns: Key.ProblemName, Key.Solver, Key.Settings,
            Key.Version and Key.LogFileName.
        Set indexsplit to 1 and choose the column with the most values as rowindex.
        From the remaining columns choose as columnindex as one or two columns with
            as little values as possible but at least two.
        At last generate a defaultgroup based on the new index.

        Parameters
        ----------
        data
            the data of the experiment
        '''
        # do this only if the user requested an automatic index
        if not self.autoIndex:
            return

        lowerbound = 1  # 1 or bigger
        possible_indices = [Key.ProblemName, Key.Solver, Key.Settings, Key.Version, Key.LogFileName]
        height = data.shape[0]

        # find the indices that are represented in the data with their numbers of unique values
        present_indices = [[key, data[key].nunique()] for key in possible_indices if key in data.columns]
        # take the index with the max value of the previous as rowindex
        first = max(present_indices, key = lambda y: y[1])

        processed_indices = [[key, count] for [key, count] in present_indices if count > lowerbound and key != first[0]]
        sorted_indices = sorted(processed_indices, key = lambda y: y[1])

        # try to find a columnindex
        second = []
        if len(sorted_indices) > 0 and sorted_indices[0][0] != first[0]:
            second = [sorted_indices[0]]
            # check if a second columnindex can be helpful
            if len(sorted_indices) > 1 and (height / first[1]) / second[0][1] > 1:
                second.append(sorted_indices[1])

        # set everything
        self.indexsplit = 1
        self.set_index(" ".join([i[0] for i in [first] + second]))
        logger.info("Automatically set index to ({}, {})".format(self.getRowIndex(), self.getColIndex()))

    def recomputeIntegrals(self, exp):
        """
        recompute primal and dual integrals of experiment if 'integral' property has been set by user.
        """
        if self.integral:
            try:
                scale, a, b = self.integral.split()
                scale = True if scale == "scaled" else False
                if a == "None":
                    a = None
                else:
                    a = float(a)
                if b == "None":
                    b = None
                else:
                    b = float(b)
                logger.info("Recomputing primal and dual integrals with specification '{}': scale: {}, (a,b)=({},{})".format(self.integral, scale, a,b))
                exp.calculateIntegrals(scale=scale, lim=(a,b))
            except:
                raise Exception("Unrecognized format for integral '{}'".format(self.integral))


    def evaluate(self, exp : Experiment):
        """
        evaluate the data of an Experiment instance exp

        Parameters
        ----------
        exp
            an experiment instance for which data has already been collected

        Returns
        -------
        rettab
            an instance-wise table of the specified columns
        retagg
            aggregated results for every filter group and every entry of the specified
        """
        self.checkMembers()

        self.recomputeIntegrals(exp)

        # data is concatenated along the rows and eventually extended by external data
        data = exp.getJoinedData().copy()

        logger.debug("Result of getJoinedData:\n{}\n".format(data))

        self.tryGenerateIndexAndDefaultgroup(data)

#            possiblebasegroups = sorted(data[self.getColIndex()[0]].unique())
#            logger.info(" Default group <%s> not contained, have only: %s" % (self.getDefaultgroup(), ", ".join(possiblebasegroups)))
#            self.defaultgrouptuple = possiblebasegroups[0]
#            logger.info(" Using value <%s> as base group" % (self.getDefaultgroup()))


        data = self.validateData(data)

        # Fill in must happen after index creation and data validation
        if self.fillin:
            data = self.fillMissingData(data)
        else:
            # create the column '_miss_' which is created within self.fillMissingData() otherwise
            data['_miss_'] = False

        data = self.calculateNeededData(data)
        logger.debug("Result of calculateNeededData:\n{}\n".format(data))
        #
        # create a target data frame that has the desired index
        #
        reduceddata = self.reduceByIndex(data)

        reduceddata = self.reduceToColumns(data, reduceddata)
        logger.debug("Result of reduceToColumns:\n{}\n".format(reduceddata))

        reduceddata = self.addComparisonColumns(reduceddata)

#         # TODO Where do we need these following three lines?
#         self.instance_wise = ret
#         self.agg = self.aggregateToPivotTable(reduceddata)
#         logger.debug("Result of aggregateToPivotTable:\n{}\n".format(self.agg))

        self.filtered_agg = {}
        self.filtered_instancewise = {}
        # filter column data and group by group key
        activefiltergroups = self.getActiveFilterGroups()
        nonemptyactivefiltergroups = activefiltergroups[:]

        #
        # set global data frame for filter groups to speed up the computations
        #
        IPETFilterGroup.setGlobalDataFrameAndIndex(reduceddata, self.getRowIndex())
        self.computeFilterResults(reduceddata)

        self.filter_masks = {}
        for fg in activefiltergroups:
            # iterate through filter groups, thereby aggregating results for every group
            filtergroupdata = self.applyFilterGroup(reduceddata, fg, self.getRowIndex())
            if (len(filtergroupdata) == 0):
                nonemptyactivefiltergroups.remove(fg)
                logger.warning("Filtergroup {} is empty and has been deactived.".format(fg.getName()))
                continue
            logger.debug("Reduced data for filtergroup {} is:\n{}".format(fg.getName(), filtergroupdata))
            self.filtered_instancewise[fg.name] = self.convertToHorizontalFormat(filtergroupdata)
            self.filtered_agg[fg.name] = self.aggregateToPivotTable(filtergroupdata)

        if len(nonemptyactivefiltergroups) > 0:
            if self.getColIndex() == []:
                for fg in nonemptyactivefiltergroups:
                    self.filtered_agg[fg.name].index = [fg.name]
            dfs = [self.filtered_agg[fg.name] for fg in nonemptyactivefiltergroups]
            names = [fg.name for fg in nonemptyactivefiltergroups]
            if self.getColIndex() == []:
                self.retagg = pd.concat(dfs)
                self.retagg.index.name = 'Group'
            else:
                self.retagg = pd.concat(dfs, keys = names, names = ['Group'])
        else:
            self.retagg = pd.DataFrame()

        # compile a long table with the requested row and column indices
        ret = reduceddata.copy()
        if self.grouptags:
            group_tags = self.computeGroupTags()
            ret["groupTags"] = group_tags

        ret = self.convertToHorizontalFormat(ret)
        logger.debug("Result of convertToHorizontalFormat:\n{}\n".format(ret))

        self.rettab = ret

        # cast all numeric columns back
        self.rettab = self.rettab.apply(pd.to_numeric, errors = 'ignore')
        self.retagg = self.retagg.apply(pd.to_numeric, errors = 'ignore')
        for d in [self.filtered_agg, self.filtered_instancewise]:
            for k, v in d.items():
                d[k] = v.apply(pd.to_numeric, errors = 'ignore')

        self.setEvaluated(True)
        return self.rettab, self.retagg

    def applyFilterGroup(self, df, fg, index):
        mask = fg.filterDataFrame(df, index)

        self.filter_masks[fg.getName()] = mask

        return df[mask]

    def computeGroupTags(self) -> list:
        """
        returns a list of strings that contains the group tags for every record/row of the original data frame
        """
        string_reps = [numpy.where(self.filter_masks.get(fg.getName()), fg.getName(), "") for fg in self.getActiveFilterGroups()]

        return DataFrame(string_reps).apply("|".join)

    def aggregateToPivotTable(self, df : DataFrame) -> DataFrame:
        """ Aggregates long data to short table

        Aggregate long table to short one.
        Values of columns are aggregated over "index", therefore "columnindex" becomes rowindex.
        In case "columnindex" was empty, the result is a table with only one row.

        Parameters
        ----------
        df
            DataFrame containing the long data (with unique index),
            df has ids as index. The indexkeys are columns.

        Returns
        -------
        DataFrame
            The aggregated DataFrame.
        """
        # the general part sums up the number of instances falling into different categories
        indices = self.countercolumns + self.getColIndex()
        if self.getColIndex() == []:
            generalpart = df[indices].apply(sum)
        else:
            generalpart = df[indices].pivot_table(index = self.getColIndex(),
                    dropna = False,
                    aggfunc = sum)

        # test if there is any aggregation to be calculated
        activecolumns = self.getActiveColumns()
        colsandaggregations = [(col, agg) for col in activecolumns for agg in col.aggregations]
        logger.debug("Cols and aggregations:\n".format([(c.getName(), a.getName()) for (c, a) in colsandaggregations]))

        # if no aggregation was specified, return only the general part
        if len(colsandaggregations) == 0:
            if isinstance(generalpart, pd.Series):
                return generalpart.to_frame().T
            else:
                return generalpart

        # column aggregations aggregate every column and every column aggregation

        if self.getColIndex() == []:
            tabs = (df[[col.getName()]].apply(agg.aggregate) for col, agg in colsandaggregations)

            colaggpart = pd.DataFrame(pd.concat(tabs)).T
        else:
            tabs = (df[[col.getName()] + self.getColIndex()].pivot_table(index = self.getColIndex(),
                dropna = False,
                aggfunc = agg.aggregate) for col, agg in colsandaggregations)
            colaggpart = pd.concat(tabs, axis = 1)
        # rename the column aggregations
        newnames = [col.getAggColName(agg) for col, agg in colsandaggregations]

        # set newnames
        colaggpart.columns = newnames

        if self.getColIndex() == []:
            ret = pd.DataFrame(generalpart.append(colaggpart.iloc[0])).T
            return ret
        else:
            # determine the row in the aggregated table corresponding to the default group
            logger.debug("Index of colaggpart:\n{}".format(colaggpart.index))

            dg = self.getDefaultgroup(df)
            if dg in colaggpart.index:
                defaultrow = colaggpart.loc[dg, :]
            else:
                # if there is no default setting, take the first group as default group
                try:
                    defaultrow = colaggpart.iloc[0, :]
                except:
                    defaultrow = numpy.nan

            # determine quotients
            columns = []
            for col in colaggpart.columns:
                if not numpy.issubdtype(colaggpart[col].dtype, numpy.number):
                    continue
                columns.append(col)
            comppart = colaggpart[columns] / defaultrow[columns]
            comppart.columns = [col + 'Q' for col in columns]

            # apply statistical tests, whereever possible
            statspart = self.applyStatsTests(df)

            # glue the parts together
            parts = [generalpart, colaggpart, comppart]

            logger.debug("Statspart : \n{}".format(statspart))
            if statspart is not None:
                parts.append(statspart)

            return pd.concat(parts, axis = 1)

    def applyStatsTests(self, df):
        """
        apply statistical tests defined by each column
        """
        if self.getColIndex() == []:
            return None
        # group the data
        groupeddata = dict(list(df.groupby(by = self.getColIndex())))
        stats = []
        names = []
        dg = self.getDefaultgroup(df)
        for col in self.getActiveColumns():
            if len(col.getStatsTests()) == 0:
                continue
            defaultvalues = None
            try:
                defaultvalues = groupeddata[dg][col.getName()].reset_index(drop = True)
            except KeyError:
                logger.info("Sorry, cannot retrieve default values for column %s, key %s for applying statistical test)" % (col.getName(), self.getDefaultgroup(df)))
                continue

            # iterate through the stats tests associated with each column
            for statstest in col.getStatsTests():
                stats.append(df[self.getColIndex() + [col.getName()]]
                             .pivot_table(index = self.getColIndex(),
                                          dropna = False,
                                          aggfunc = lambda x:statstest(x.reset_index(drop = True),
                                                                       defaultvalues)))
                names.append(col.getStatsColName(statstest))

        if len(stats) > 0:
            stats = pd.concat(stats, axis = 1)
            stats.columns = names

            return stats
        else:
            return None

    def aggregateTable(self, df):
        results = {}
        columnorder = []
        for col in self.getActiveColumns():
            origcolname = col.getName()
            partialdf = df.xs(origcolname, level = 1, axis = 1, drop_level = False)

            for partialcol in partialdf.columns:
                columnorder.append(partialcol)
                results[partialcol] = {}
                for agg in col.aggregations:
                    results[partialcol][agg.getName()] = agg.aggregate(df[partialcol])

        return pd.DataFrame(results)[columnorder]

    def computeFilterResults(self, df : pd.DataFrame):
        """Compute filter results once and spread them across filters that are equal.
        """
        activefilters = [f for g in self.getActiveFilterGroups() for f in g.getActiveFilters()]

        # sort by name, which is a good proxy for equality
        activefilters = sorted(activefilters, key = lambda x:x.getName())
        for idx, f in enumerate(activefilters):
            if idx > 0:
                previous_f = activefilters[idx - 1]
                stored_result = previous_f.getStoredResult(df)

            else:
                previous_f = None
                stored_result = None

            #
            # try to skip the computation of the filter column if an equal
            # filter already has a stored result
            #
            if f.equals(previous_f) and stored_result is not None:
                logger.debug("Reusing previously stored result for filter {}".format(f.getName()))
                fcol = stored_result
            else:
                fcol = f.applyFilter(df, self.getRowIndex())
            #
            # store the result (either by applying the filter, or by copying)
            #
            f.storeResult(df, fcol)


if __name__ == '__main__':
    pass
