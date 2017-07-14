"""
The MIT License (MIT)

Copyright (c) 2016 Zuse Institute Berlin, www.zib.de

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

class IPETEvaluationColumn(IpetNode):

    nodetag = "Column"

    editableAttributes = ["name", "origcolname", "formatstr", "transformfunc", "reduction", "constant",
                 "alternative", "minval", "maxval", "comp", "translevel", "regex"]

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
    
    possiblereductions = [None] + [k for k, v in possibletransformations.items() if v == (1, -1)]
    
    possiblecomparisons = [None, "quot", "difference"] + ["quot shift. by %d" % shift for shift in (1, 5, 10, 100, 1000)]

    requiredOptions = {"comp":possiblecomparisons,
                       "origcolname":"datakey",
                       "translevel":[0, 1],
                       "transformfunc":list(possibletransformations.keys()),
                       "reduction" : possiblereductions}

    deprecatedattrdir = {"nanrep" : "has been replaced by 'alternative'",
                            "groupkey" : "groupkey is specified using 'index' and 'indexsplit'"}

    def __init__(self, origcolname = None, name = None, formatstr = None, transformfunc = None, constant = None,
                 alternative = None, minval = None, maxval = None, comp = None, regex = None, translevel = None,
                 active = True, reduction = "meanOrConcat", **kw):
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

        translevel : Specifies the level on which to apply the defined transformation for this column. Use translevel=0 to handle every instance
                     and group separately, and translevel=1 for an instance-wise transformation over all groups, e.g., the mean solving time
                     if five permutations were tested. Columns with translevel=1 are appended at the end of the instance-wise table

        active : True or "True" if this column should be active, False otherwise
        
        reduction : aggregation function that is applied to reduce multiple occurrences of index 
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
        self.translevel = translevel
        self.set_comp(comp)
        self.regex = regex
        self.set_reduction(reduction)

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
                raise IpetNodeAttributeError("Attribute 'reduction' has illegal value '%s'"% self.reduction)
        return True

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

    def parseValue(self, val, df=None):
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

    def getTransLevel(self):
        if self.translevel is None or int(self.translevel) == 0:
            return 0
        else:
            return 1

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
                if child.tag == IPETFilter.getNodeTag():
                    elemdict = dict(child.attrib)
                    filter_ = IPETFilter.fromDict(elemdict)
                    column.addFilter(filter_)
                elif child.tag == IPETEvaluationColumn.getNodeTag():
                    column.addChild(IPETEvaluationColumn.processXMLElem(child))
            return column
        
    def getTransformationFunction(self):
        """
        tries to find the transformation function from the numpy, misc, or Experiment modules
        """
        # Do we also have to search in module Key (for getWorstStatus etc)?
        for module in [numpy, misc, Experiment]:
            try:
                return getattr(module, self.transformfunc)
            except AttributeError:
                pass
        raise IpetNodeAttributeError(self.transformfunc, "Unknown transformation function %s" % self.transformfunc)

    def getReductionFunction(self):
        """
        tries to find the reduction function from the numpy, misc, or Experiment modules
        """

        funcname = self.reduction
        # Do we also have to search in module Key (for getWorstStatus etc)?
        for module in [numpy, misc, Experiment, Key.ProblemStatusCodes]:
            try:
                return getattr(module, funcname)
            except AttributeError:
                pass
        raise IpetNodeAttributeError(funcname, "Unknown reduction function %s" % self.reduction)

    def getColumnData(self, df):
        """
        Retrieve the data associated with this column
        """
        # if no children are associated with this column, it is either
        # a column represented in the data frame by an 'origcolname',
        # or a constant
        if len(self.children) == 0:
            if self.origcolname is not None:
                try:
                    result = df[self.origcolname]
                except KeyError as e:
                    # print an error message and make a series with NaN's
                    print(e)
                    print("Could not retrieve data %s" % self.origcolname)
                    result = pd.Series(numpy.nan, index=df.index)


            elif self.regex is not None:
                result = df.filter(regex=self.regex)
            elif self.constant is not None:
                df[self.getName()] = self.parseConstant()
                result = df[self.getName()]
        else:
            # try to apply an element-wise transformation function to the children of this column
            # gettattr is equivalent to numpy.__dict__[self.transformfunc]
            transformfunc = self.getTransformationFunction()

            # concatenate the children data into a new data frame object
            argdf = pd.concat([child.getColumnData(df) for child in self.children], axis=1)

            if self.getTransLevel() == 1:

                # group the whole table per instance #

                argdf = argdf.groupby(level=0)

                # determine the axis along which to apply the transformation later on
                applydict = {}
            else:
                applydict = dict(axis=1)

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
            alternative = self.parseValue(self.alternative, df)
            if alternative is not None:
                booleanseries = pd.isnull(result)
                for f in self.getActiveFilters():
                    booleanseries = numpy.logical_or(booleanseries, f.applyFilter(df).iloc[:, 0])
                result = result.where(~booleanseries, alternative)
        if self.minval is not None:
            minval = self.parseValue(self.minval, df)
            if minval is not None:
                if type(minval) in [int, float]:
                    result = numpy.maximum(result, minval)
                else:
                    result = numpy.maximum(result, minval.astype(result.dtype))
        if self.maxval is not None:
            maxval = self.parseValue(self.maxval, df)
            if maxval is not None:
                if type(maxval) in [int, float]:
                    result = numpy.minimum(result, maxval)
                else:
                    result = numpy.minimum(result, maxval.astype(result.dtype))
        return result

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

class FormatFunc:

    def __init__(self, formatstr):
        self.formatstr = formatstr[:]

    def beautify(self, x):
        return (self.formatstr % x)
    
    
class StrTuple:
    """
    Represents an easier readible and parsable list of strings
    """
    def __init__(self, strList, splitChar = " "):
        self.tuple = StrTuple.splitStringList(strList, splitChar)
        self.splitChar = splitChar

    @staticmethod
    def splitStringList(strList, splitChar = " "):
        """Split a string that represents list elements separated by optional split-character
        """
        if strList is None or strList == "":
            return None
        elif type(strList) is str:
            if splitChar == " ":
                return tuple(strList.split())
            else:
                return tuple(strList.split(splitChar))
        else:
            return tuple(strList)

    def getTuple(self):
        if self.tuple is None:
            return tuple()
        return self.tuple
        
    def __str__(self):
        if self.tuple is None:
            return ""
        return self.splitChar.join(self.tuple)

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
    DEFAULT_INDEX = "ProblemName LogfileName"
    DEFAULT_INDEXSPLIT= -1
    ALLTOGETHER = "_alltogether_"

    editableAttributes = ["groupkey", "defaultgroup", "evaluateoptauto", "sortlevel", "comparecolformat", "index", "indexsplit"]
    attributes2Options = {"evaluateoptauto":[True, False], "sortlevel":[0, 1]}

    def __init__(self, groupkey = DEFAULT_GROUPKEY, defaultgroup = None, evaluateoptauto = True,
                 sortlevel = 0, comparecolformat = DEFAULT_COMPARECOLFORMAT, index = DEFAULT_INDEX, indexsplit=DEFAULT_INDEXSPLIT):
        """
        constructs an Ipet-Evaluation

        Parameters
        ----------
        groupkey : the key by which groups should be built, eg, 'Settings'
        defaultgroupvalues : the values of the default group to be compared with. usually corresponds to specified columns
        evaluateoptauto : should optimal auto settings be calculated?
        sortlevel : level on which to base column sorting, '0' for group level, '1' for column level
        comparecolformat : format string for comparison columns
        index : (string or list or None) single or multiple column names that serve as (row) and column index levels
        indexsplit : (int) position to split index into row and column levels, negative to count from the end.
        """

        # construct super class first, Evaluation is currently always active
        super(IPETEvaluation, self).__init__(True)

        self.filtergroups = []
        self.groupkey = groupkey
        self.comparecolformat = comparecolformat[:]
        self.columns = []
        self.set_evaluateoptauto(evaluateoptauto)
        self.sortlevel = int(sortlevel)
        self.evaluated = False

        self.defaultgroup = defaultgroup
        self.set_indexsplit(indexsplit)
        self.set_index(index)
        
    def getName(self):
        return self.nodetag

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

    def set_evaluateoptauto(self, evaluateoptauto):
        self.evaluateoptauto = True if evaluateoptauto in [True, "True"] else False

    def set_sortlevel(self, sortlevel):
        self.sortlevel = int(sortlevel)

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

#    def setGroupKey(self, gk):
#        self.groupkey = gk

    def set_index(self, index : list):
        """Set index identifier list, optionally with level specification (0 for row index, 1 for column index)
        """
        self.autoIndex = False
        self.index = StrTuple(index)
        logging.debug("Set index to '{}'".format(index))
        if index == "auto":
            self.autoIndex = True
            self.defaultgroup = ""
            self.defaultgrouptuple = None
            return
        self.set_indexsplit(self.indexsplit)
        self.set_defaultgroup(self.defaultgroup)
        
    def getRowIndex(self) -> list:
        """Return (list of) keys to create row index 
        """
        return list(self.index.getTuple())[:self.indexsplit]
    
    def getColIndex(self) -> list:
        """Return (list of) keys to create column index
        """
        return list(self.index.getTuple())[self.indexsplit:]

    def getDefaultgroup(self):
        """Return tuple representation of defaultgroup
        """
        return self.defaultgrouptuple

    def set_defaultgroup(self, dg : str):
        """Set defaultgroup
        
        Parameters
        ----------
        dg
            the string representing the defaultgroup in format "val1:val2:val3"
        """
        self.defaultgroup = dg
        dg = StrTuple.splitStringList(dg, ":")
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

        self.defaultgrouptuple = None
        if x is not None: 
            if len(x) > len(self.getColIndex()):
                x = x[:len(self.getColIndex())]
            if len(x) == 1:
                self.defaultgrouptuple = x[0]
            else:
                self.defaultgrouptuple = tuple(x)
        self.setEvaluated(False)
        logging.debug("Set defaultgrouptuple to {} from defaultgroup {}".format(self.defaultgrouptuple, self.defaultgroup))

    def set_indexsplit(self, indexsplit):
        self.indexsplit = int(indexsplit)
        # make sure that we have at least one col as rowindex
        indexsplitmod = self.indexsplit
        try:
            if self.index is not None:
                indexsplitmod = self.indexsplit % len(self.index)
        except:
            pass
        if indexsplitmod == 0:
            logging.warn("Indexsplit 0 is not allowed, setting it to 1.")
            self.indexsplit = 1;
    
    def addColumn(self, col):
        self.columns.append(col)
        self.setEvaluated(False)

    def removeColumn(self, col):
        self.columns.remove(col)
        self.setEvaluated(False)

    def setEvaluateOptAuto(self, evaloptauto):
        """ Should the evaluation calculate optimal auto settings?
        """
        self.set_evaluateoptauto(evaloptauto)

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

        for col in self.toposortColumns(self.getActiveColumns()):
            # look if a comparison with the default group should be made
            if col.getTransLevel() == 0 and col.getCompareMethod() is not None:

                grouped = df.groupby(self.getColIndex())[col.getName()]
                compcol = dict(list(grouped))[self.getDefaultgroup()]

                comparecolname = col.getCompareColName()

                # apply the correct comparison method to the original and the temporary column
                compmethod = col.getCompareMethod()
                method = lambda x:compmethod(*x)

                df[comparecolname] = 0
                for name, group in grouped:
                    tmpgroup = DataFrame(group.reset_index(drop = True))
                    tmpgroup["_tmpcol_"] = compcol.reset_index(drop = True)
                    tmpgroup[comparecolname] = tmpgroup[[col.getName(), "_tmpcol_"]].apply(method, axis = 1)#.set_index(group.index)
                    df[comparecolname].update((tmpgroup.set_index(group.index))[comparecolname])

#                print(df[comparecolname])
                usercolumns.append(comparecolname)

        # TODO Sort usercolumns?
        self.usercolumns = self.usercolumns + usercolumns
        return df

    def reduceToColumns(self, df_long : DataFrame) -> DataFrame:
        """ Reduce the huge number of columns
        
        Select from the raw data: the columns specified in evaluation xmlfile.
        (concatenate usercolumns, neededcolumns and additionalfiltercolumns from df_long)

        Parameters
        ----------
        df_long
            Dataframe to evaluate, mostly joined data from an experiment,
            that contains the necessary columns required by this evaluation.
            For example: A dataframe containing the parsed data from one or
            multiple .trn files created by ipet-parse.

        Returns
        -------
        DataFrame
            A DataFrame in the same format as df_long with only the relevant columns.
        """
        #
        # Attention: this will be deleted soon because it is not flexible enough
        # --> will be replaced by reduction function in IPETEvaluationColumn
        #
        lvlonecols = [col for col in self.getActiveColumns() if col.getTransLevel() == 1]
        if len(lvlonecols) > 0:
            self.levelonedf = pd.concat([col.getColumnData(df_long) for col in lvlonecols], axis=1)
            self.levelonedf.columns = [col.getName() for col in lvlonecols]
        else:
            self.levelonedf = None
        # treat columns differently for level=0 and level=1
        # We are only interested in the columns that are activated in the eval file
        usercolumns = [c.getName() for c in self.getActiveColumns()]
        for col in self.toposortColumns(self.getActiveColumns()):
            if col.getTransLevel() == 0:
                try:
                    df_long[col.getName()] = col.getColumnData(df_long)
                except Exception as e:
                    print("An error occurred for the column '{}':\n{}".format(col.getName(), col.attributesToStringDict()))
                    raise e

        # concatenate level one columns into a new data frame and treat them as the altogether setting
        newcols = [Key.ProblemStatus, Key.SolvingTime, Key.TimeLimit, Key.ProblemName]

        for x in self.index.getTuple():
            if x not in newcols:
                newcols.append(x)
        neededcolumns = [col for col in newcols if col not in usercolumns]

        additionalfiltercolumns = []
        for fg in self.getActiveFilterGroups():
            additionalfiltercolumns += fg.getNeededColumns(df_long)

        additionalfiltercolumns = list(set(additionalfiltercolumns))
        additionalfiltercolumns = [afc for afc in additionalfiltercolumns if afc not in set(usercolumns + neededcolumns)]

        result = df_long.loc[:, usercolumns + neededcolumns + additionalfiltercolumns + ['_count_', '_solved_', '_time_', '_limit_', '_fail_', '_abort_', '_unkn_']]
        self.usercolumns = usercolumns
        return result

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
        logging.debug("TOPOSORT:\nDependency List: {},\nTopological Ordering: {}".format(adj, toposorted))
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
        df['_limit_'] = ((df['_time_']) | df[Key.ProblemStatus].isin([Key.ProblemStatusCodes.NodeLimit,
                                                                      Key.ProblemStatusCodes.MemoryLimit,
                                                                      Key.ProblemStatusCodes.Interrupted
                                                                      ]))
        df['_fail_'] = df[Key.ProblemStatus].isin([Key.ProblemStatusCodes.FailDualBound,
                                                    Key.ProblemStatusCodes.FailObjectiveValue,
                                                    Key.ProblemStatusCodes.FailSolInfeasible,
                                                    Key.ProblemStatusCodes.FailSolOnInfeasibleInstance,
                                                    Key.ProblemStatusCodes.Fail
                                        ])
        df['_abort_'] = (df[Key.ProblemStatus] == Key.ProblemStatusCodes.FailAbort)

        df['_solved_'] = (~df['_limit_']) & (~df['_fail_']) & (~df['_abort_'])

        df['_count_'] = 1
        df['_unkn_'] = (df[Key.ProblemStatus] == Key.ProblemStatusCodes.Unknown)
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
            logging.debug("Construct IPET Evaluation with attributes : \n{}".format(elem.attrib))
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
        tmpcols = list(set(self.usercolumns + list(self.index.getTuple()) + ['_time_', '_limit_', '_fail_', '_abort_', '_solved_', '_unkn_', '_count_']))
        horidf = df[tmpcols]
        grouped = horidf.groupby(by = self.index.getTuple())
        newcols = []

        reductionMap = {'_solved_' : numpy.all, '_count_' : numpy.max}
        for col in ['_time_', '_limit_', '_fail_', '_abort_', '_solved_', '_unkn_', '_count_']:
            newcols.append(grouped[col].apply(reductionMap.get(col, numpy.any)))

        for col in self.getActiveColumns():
            newcols.append(grouped[col.getName()].apply(col.getReductionFunction()))

        horidf = pd.concat(newcols, axis = 1)
        ind = self.index.getTuple()
        index_uniq = [i for i in ind if i not in horidf.columns]
        index_dupl = [i for i in ind if i in horidf.columns]
        horidf = horidf.reset_index(index_uniq)
        horidf = horidf.reset_index(index_dupl, drop = True)
#        horidf = horidf.reset_index(self.index.getTuple())
        return horidf

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
        df = df.set_index(list(self.index.getTuple())).sort_index(level = 0)
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
        formatters = {}
        thelevel = 0

        # temporary hack to test which level is the maximum level
        try:
            df.columns.get_level_values(1)
            thelevel = 1
        except IndexError:
            pass

        comptuples = []
        # loop over columns
        for col in self.getActiveColumns():

            # determine all possible comparison columns and append them to the list
            if col.getCompareMethod() is not None:
                try:
                    if thelevel == 1:
                        comptuples += df.xs(col.getName() + col.getCompareSuffix(), axis=1, level=thelevel, drop_level=False).columns.values.tolist()
                    else:
                        comptuples += [dfcol for dfcol in df.columns if dfcol.startswith(col.getName()) and dfcol.endswith("Q")]
                except:
                    pass

            # if the column has no formatstr attribute, continue
            if not col.getFormatString():
                continue

            # retrieve all columns as tuples that contain the column name, ie. for column 'Time' and
            # settings 'default' and 'heuroff', the result should be [('default', 'Time'),('heuroff', 'Time')]
            try:
                if thelevel == 1:
                    tuples = df.xs(col.getName(), axis=1, level=thelevel, drop_level=False).columns.values.tolist()

                else:
                    tuples = [dfcol for dfcol in df.columns if dfcol.startswith(col.getName()) and not dfcol.endswith("Q") and not dfcol.endswith("p")]
            except KeyError:
                # the column name is not contained in the final df
                continue

            # add new formatting function to the map of formatting functions
            for thetuple in tuples:
                formatters.update({thetuple:FormatFunc(col.getFormatString()).beautify})

        for comptuple in comptuples:
            formatters.update({comptuple:FormatFunc(self.comparecolformat).beautify})

        return formatters

    def streamDataFrame(self, df, filebasename, streamtype):
        if not self.checkStreamType(streamtype):
            raise ValueError("Stream error: Unknown stream type %s" % streamtype)
        streammethod = getattr(self, "streamDataFrame_%s" % streamtype)

        formatters = self.getColumnFormatters(df)

        streammethod(df, filebasename, formatters)

    def streamDataFrame_stdout(self, df, filebasename, formatters={}):
        """
        print to console
        """
        print("%s:" % filebasename)
        print(df.to_string(formatters=formatters))

    def streamDataFrame_tex(self, df, filebasename, formatters={}):
        """
        write tex output
        """
        with open("%s.tex" % filebasename, "w") as texfile:
            texfile.write(df.to_latex(formatters=formatters))

    def streamDataFrame_csv(self, df, filebasename, formatters={}):
        with open("%s.csv" % filebasename, "w") as csvfile:
            df.to_csv(csvfile, formatters=formatters)

    def streamDataFrame_txt(self, df, filebasename, formatters={}):
        """
        write txt output
        """
        with open("%s.txt" % filebasename, "w") as txtfile:
            df.to_string(txtfile, formatters=formatters, index_names=False)

    def findStatus(self, statuscol):
        uniques = set(statuscol.unique())
        for status in ["ok", "timelimit", "nodelimit", "memlimit", "unknown", "fail", "abort"]:
            if status in uniques:
                return status
        else:
            return statuscol.unique()[0]

    def calculateOptimalAutoSettings(self, df):
        """
        calculate optimal auto settings instancewise
        """
        grouped = df.groupby(level=0)

        #
        # every apply operation on the group element returns a pandas series
        #
        optstatus = grouped["Status"].apply(self.findStatus)
        opttime = grouped["SolvingTime"].apply(numpy.min)
        opttimelim = grouped["TimeLimit"].apply(numpy.mean)

        optdf = pd.concat([optstatus, opttime, opttimelim], axis=1)
        optdf[self.groupkey] = "OPT. AUTO"

        aggfuncs = {'_solved_':numpy.max}
        useroptdf = pd.concat([grouped[col].apply(aggfuncs.get(col, numpy.min)) for col in self.usercolumns if col not in ["Status", "SolvingTime", "TimeLimit"]], axis=1)
        optdf = pd.concat([optdf, useroptdf], axis=1)

        return optdf

    def checkMembers(self):
        """
        checks the evaluation members for inconsistencies
        """
        if self.columns == []:
            raise AttributeError("Please specify at least one column.")
        if self.filtergroups == []:
            raise AttributeError("Please specify at least one filtergroup.")
        for col in self.columns:
            try:
                col.checkAttributes()
            except Exception as e:
                raise AttributeError("Error in column definition of column %s:\n   %s" % (col.getName(), e))

    def getAggregatedGroupData(self, filtergroup):
        if not filtergroup in self.filtergroups:
            raise ValueError("Filter group %s (name:%s) is not contained in evaluation filter groups" % (filtergroup, filtergroup.getName()))
        if  not filtergroup.isActive():
            raise ValueError("Filter group %s is currently not active" % filtergroup.getName())

        return self.filtered_agg[filtergroup.getName()]

    def getInstanceGroupData(self, filtergroup):
        if not filtergroup in self.filtergroups:
            raise ValueError("Filter group %s (name:%s) is not contained in evaluation filter groups" % filtergroup, filtergroup.getName())
        if  not filtergroup.isActive():
            raise ValueError("Filter group %s is currently not active", filtergroup.getName())
        return self.filtered_instancewise[filtergroup.getName()]

    def getAggregatedData(self):
        return self.retagg

    def getInstanceData(self):
        return self.rettab

    def generateDefaultGroup(self, data, colindex):
        '''
        Generate a defaultgroup based on the colindexkeys and data.
        
        Based on the total number of occurences 
        the tuple with the most occurences is chosen to be the defaultgroup.

        Parameters
        ----------
        data
            raw DataFrame
        colindex
            keys of columnindex
        '''
        # only generate a defaultgroup if the user did not specify one themself
        if self.defaultgrouptuple is not None and self.defaultgroup != "":
            return

        # count values of (tuples of) column index
        tuples = [tuple(x) for x in data[colindex].values]
        counts = pd.Series(tuples).value_counts()
        max_key = counts.idxmax()

        # take the tuple with the highest occurrence
        self.defaultgroup = ":".join(max_key)
        logging.info("Using {} as default group.".format(self.defaultgroup))

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
            if self.defaultgroup == "":
                self.generateDefaultGroup(data, list(self.getColIndex()))
                self.set_defaultgroup(self.defaultgroup)
            return

        lowerbound = 1 # 1 or bigger
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
        self.generateDefaultGroup(data, [i[0] for i in second])
        self.set_index(" ".join([i[0] for i in [first] + second]))
        logging.info("Automatically set index to ({}, {})".format(self.getRowIndex(), self.getColIndex()))
        
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

        # data is concatenated along the rows and eventually extended by external data
        data = exp.getJoinedData()
        logging.debug("Result of getJoinedData:\n{}\n".format(data))

        self.tryGenerateIndexAndDefaultgroup(data)

        if not self.groupkey in data.columns:
            raise KeyError(" Group key is missing in data:", self.groupkey)
#        elif self.getDefaultgroup() is not None and self.getDefaultgroup() not in data[self.getColIndex()[0]].values:
#            possiblebasegroups = sorted(data[self.getColIndex()[0]].unique())
#            logging.info(" Default group <%s> not contained, have only: %s" % (self.getDefaultgroup(), ", ".join(possiblebasegroups)))
#            self.defaultgrouptuple = possiblebasegroups[0]
#            logging.info(" Using value <%s> as base group" % (self.getDefaultgroup()))

        data = self.calculateNeededData(data)
        logging.debug("Result of calculateNeededData:\n{}\n".format(data))

        columndata = self.reduceToColumns(data)
        logging.debug("Result of reduceToColumns:\n{}\n".format(columndata))

        if self.evaluateoptauto:
            logging.warning("Optimal auto settings are currently not available, use reductions instead")
            #opt = self.calculateOptimalAutoSettings(columndata)
            #columndata = pd.concat([columndata, opt])
            #logging.debug("Result of calculateOptimalAutoSettings:\n{}\n".format(columndata))

        columndata = self.reduceByIndex(columndata)
        columndata = self.addComparisonColumns(columndata)

        # show less info in long table
        columns = columndata.columns
        diff = lambda l1, l2: [x for x in l1 if x not in l2]
        lcolumns = diff(columns, ['_count_', '_solved_', '_time_', '_limit_', '_fail_', '_abort_', '_unkn_'])
        # show more info in table
#        lcolumns = columndata.columns

        # compile a results table containing all instances
        ret = self.convertToHorizontalFormat(columndata[lcolumns])
        logging.debug("Result of convertToHorizontalFormat:\n{}\n".format(ret))

        # TODO self.levelonedf is always None because it will be deprecated
        if self.levelonedf is not None:
            self.levelonedf.columns = pd.MultiIndex.from_product([[IPETEvaluation.ALLTOGETHER], self.levelonedf.columns])
            self.rettab = pd.concat([ret, self.levelonedf], axis=1)
        else:
            self.rettab = ret
        
        # TODO Where do we need these following three lines?
        self.instance_wise = ret
        self.agg = self.aggregateToPivotTable(columndata)
        logging.debug("Result of aggregateToPivotTable:\n{}\n".format(self.agg))
            
        self.filtered_agg = {}
        self.filtered_instancewise = {}
        # filter column data and group by group key
        activefiltergroups = self.getActiveFilterGroups()
        for fg in activefiltergroups:
            # iterate through filter groups, thereby aggregating results for every group
            reduceddata = self.applyFilterGroup(columndata, fg, self.getRowIndex())
            if (len(reduceddata) == 0):
                fg.set_active(False)
                logging.warn("Filtergroup {} is empty and has been deactived.".format(fg.getName()))
                continue
            logging.debug("Reduced data for filtergroup {} is:\n{}".format(fg.getName(), reduceddata))
            self.filtered_instancewise[fg.name] = self.convertToHorizontalFormat(reduceddata[lcolumns])
            self.filtered_agg[fg.name] = self.aggregateToPivotTable(reduceddata)

        activefiltergroups = self.getActiveFilterGroups()
        if len(activefiltergroups) > 0:
            nonemptyfiltergroups = [fg for fg in activefiltergroups if not self.filtered_agg[fg.name].empty]
            if self.getColIndex() == []:
                for fg in nonemptyfiltergroups:
                    self.filtered_agg[fg.name].index = [fg.name]
            dfs = [self.filtered_agg[fg.name] for fg in nonemptyfiltergroups]
            names = [fg.name for fg in nonemptyfiltergroups]
            if self.getColIndex() == []:
                self.retagg = pd.concat(dfs)
                self.retagg.index.name = 'Group'
            else:
                self.retagg = pd.concat(dfs, keys=names, names=['Group'])
        else:
            self.retagg = pd.DataFrame()

        self.setEvaluated(True)
        return self.rettab, self.retagg

    def applyFilterGroup(self, df, fg, index):
        return fg.filterDataFrame(df, index)

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
        indices = ['_count_', '_solved_', '_time_', '_limit_', '_fail_', '_abort_', '_unkn_'] + self.getColIndex()
        if self.getColIndex() == []:
            generalpart = df[indices].apply(sum)
        else:
            generalpart = df[indices].pivot_table(index = self.getColIndex(), aggfunc = sum)

        # test if there is any aggregation to be calculated
        activecolumns = self.getActiveColumns()
        colsandaggregations = [(col, agg) for col in activecolumns for agg in col.aggregations]
        logging.debug("Cols and aggregations:\n".format([(c.getName(), a.getName()) for (c, a) in colsandaggregations]))

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
            tabs = (df[[col.getName()] + self.getColIndex()].pivot_table(index = self.getColIndex(), aggfunc = agg.aggregate) for col, agg in colsandaggregations)
            colaggpart = pd.concat(tabs, axis = 1)
        # rename the column aggregations
        newnames = ['_'.join((col.getName(), agg.getName())) for col, agg in colsandaggregations]

        # set newnames
        colaggpart.columns = newnames

        if self.getColIndex() == []:
            ret = pd.DataFrame(generalpart.append(colaggpart.iloc[0])).T
            return ret
        else:
            # determine the row in the aggregated table corresponding to the default group
            logging.debug("Index of colaggpart:\n{}".format(colaggpart.index))

            if (self.getDefaultgroup() is not None) and (self.getDefaultgroup() in colaggpart.index):
                defaultrow = colaggpart.loc[self.getDefaultgroup(), :]
            else:
                # if there is no default setting, take the first group as default group
                try:
                    self.defaultgrouptuple = colaggpart.index[0]
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

            logging.debug("Statspart : \n{}".format(statspart))
            if statspart is not None:
                parts.append(statspart)

            return pd.concat(parts, axis = 1)

    def applyStatsTests(self, df):
        """
        apply statistical tests defined by each column
        """
        # TODO What if indexkeys[1] is empty?
        if self.getColIndex() == []:
            return None
        # group the data by the groupkey
        groupeddata = dict(list(df.groupby(self.getColIndex())))
        stats = []
        names = []
        for col in self.getActiveColumns():
            if len(col.getStatsTests()) == 0:
                continue
            defaultvalues = None
            try:
                defaultvalues = groupeddata[self.getDefaultgroup()][col.getName()].reset_index(drop = True)
            except KeyError:
                logging.info("Sorry, cannot retrieve default values for column %s, key %s for applying statistical test)" % (col.getName(), self.getDefaultgroup()))
                continue

            # iterate through the stats tests associated with each column
            for statstest in col.getStatsTests():
                stats.append(df[self.getColIndex() + [col.getName()]].pivot_table(index = self.getColIndex(), aggfunc = lambda x:statstest(x.reset_index(drop = True), defaultvalues)))
                names.append('_'.join((col.getName(), statstest.__name__)))

        if len(stats) > 0:
            stats = pd.concat(stats, axis=1)
            stats.columns = names

            return stats
        else:
            return None
        
    def aggregateTable(self, df):
        results = {}
        columnorder = []
        for col in self.getActiveColumns():
            origcolname = col.getName()
            partialdf = df.xs(origcolname, level=1, axis=1, drop_level=False)

            for partialcol in partialdf.columns:
                columnorder.append(partialcol)
                results[partialcol] = {}
                for agg in col.aggregations:
                    results[partialcol][agg.getName()] = agg.aggregate(df[partialcol])

        return pd.DataFrame(results)[columnorder]

if __name__ == '__main__':
    pass
