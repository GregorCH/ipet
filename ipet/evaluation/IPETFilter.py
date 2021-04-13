"""
The MIT License (MIT)

Copyright (c) 2018 Zuse Institute Berlin, www.zib.de

Permissions are granted as stated in the license file you have obtained
with this software. If you find the library useful for your purpose,
please refer to README.md for how to cite IPET.

@author: Gregor Hendel
"""
import xml.etree.ElementTree as ElementTree
import numpy as np
from ipet.concepts import IpetNode, IpetNodeAttributeError
import logging
import pandas as pd
from ipet.evaluation import TestSets

logger = logging.getLogger(__name__)


class IPETValue(IpetNode):
    nodetag = "Value"

    def __init__(self, name = None, active = True):
        """
        constructs an Ipet Instance

        Parameters
        ----------

        name : The name of this problem
        active : True or "True" if this element should be active, False otherwise
        """
        super(IPETValue, self).__init__(active)
        self.name = name

    def checkAttributes(self):
        if self.name is None:
            raise IpetNodeAttributeError("name", "No name specified")
        return True

    def getEditableAttributes(self):
        return ["name"] + super(IPETValue, self).getEditableAttributes()

    @staticmethod
    def getNodeTag():
        return IPETValue.nodetag

    def getName(self):
        return self.name

    def getValue(self, dtype = None):
        if dtype is None:
            for mytype in [int, float, str]:
                try:
                    return mytype(self.name)
                except ValueError:
                    continue
        elif dtype != object:
            return dtype.type(self.name)

        return self.name

    def toXMLElem(self):
        me = ElementTree.Element(IPETValue.getNodeTag(), self.attributesToStringDict())
        return me


class IPETComparison:
    """
    comparison operators for filters. All standard binary comparisons + float comparisons (with tolerance)
    + percentage based inequality
    """
    comparisondict = {
                      "le":"le",
                      "lt":"lt",
                      "gt":"gt",
                      "ge":"ge",
                      "eq":"eq",
                      "neq":"neq"
                      }

    def __init__(self, operator):
        """
        constructs a comparison object by passing an appropriate operator as string
        """
        if str(operator) in IPETComparison.comparisondict:
            self.operator = str(operator)
        else:
            raise KeyError("Unknown key value %s" % (operator))

    def compare(self, x, y):
        method = getattr(self, "method_" + IPETComparison.comparisondict[self.operator])
        try:
            return method(x, y)
        except TypeError as t:
            logger.error("Got type error %s comparing elements x:%s and y:%s" % (t, x, y))
            return 0

    def method_le(self, x, y):
        return x <= y

    def method_lt(self, x, y):
        return x < y

    def method_ge(self, x, y):
        return x >= y

    def method_gt(self, x, y):
        return x > y

    def method_eq(self, x, y):
        return x == y

    def method_neq(self, x, y):
        return x != y


class IPETFilter(IpetNode):
    """
    Filters are used for selecting subsets of problems to analyze.
    """
    valueoperators = ["keep", "drop"]
    listoperators = ["diff", "equal"]
    attribute2Options = {
                         "anytestrun":["one", "all"],
                         "operator":list(IPETComparison.comparisondict.keys())
                         +valueoperators
                         +listoperators}
    nodetag = "Filter"
    DEFAULT_ANYTESTRUN = 'all'
    _storedcol_ = None
    _storeddf_ = None

    def __init__(self, expression1 = None, expression2 = None, operator = "ge", anytestrun = DEFAULT_ANYTESTRUN, active = True, datakey = None):
        """
        filter constructor

        Parameters
        ----------

        expression1 : integer, float, string, or column name
        expression2 : integer, float, string, or column name
        datakey : available data key for drop and keep filters
        operator : operator such that evaluation expression1 op expression2 yields True or False
        anytestrun : either 'one' or 'all'
        active : True or "True" if this filter should be active, False otherwise
        """

        super(IPETFilter, self).__init__(active)
        self.expression1 = expression1
        self.expression2 = expression2

        self.anytestrun = anytestrun
        self.values = []
        self._updatevalueset = False

        self.set_operator(operator)
        self.datakey = datakey

    def checkAttributes(self):
        if self.operator in self.valueoperators and self.values == []:
            raise IpetNodeAttributeError("operator", "Trying to use a filter with operator {0} and empty value set".format(self.operator))
        if self.operator in self.valueoperators and self.datakey is None or self.datakey == "":
            raise IpetNodeAttributeError("datakey", "Trying to use a filter with operator '{}' and unspecified data key '{}'".format(self.operator, self.datakey))

        if self.anytestrun not in self.attribute2Options["anytestrun"]:
            raise IpetNodeAttributeError("anytestrun", "Wrong attribute {} passed as 'anytestrun' property. Should be in {}".format(self.anytestrun, self.attribute2Options["anytestrun"]))
        return True

    @staticmethod
    def fromDict(attrdict):
        expression1 = attrdict.get('expression1')
        expression2 = attrdict.get('expression2')

        anytestrun = attrdict.get('anytestrun', IPETFilter.DEFAULT_ANYTESTRUN)
        operator = attrdict.get('operator')
        datakey = attrdict.get('datakey')
        active = attrdict.get('active', True)

        return IPETFilter(expression1, expression2, operator, anytestrun, active, datakey)


    @staticmethod
    def processXMLElem(elem):
        """
        inspect and process an xml element
        """

        elemdict = dict(elem.attrib)

        # filter_ must be written with a trailing underscore "_" not to conflict with the filter method of Python
        filter_ = IPETFilter.fromDict(elemdict)

        # add values one by one
        for child in elem:

            # catch wrong children
            if not child.tag == IPETValue.getNodeTag():
                raise AttributeError("Cannot add a child of type {} to a Filter".format(child.tag))

            instancename = child.attrib.get("name")
            if instancename:
                filter_.addChild(IPETValue(instancename))
        # check the filter attributes
        filter_.checkAttributes()
        return filter_

    def getName(self):
        prefix = self.anytestrun
        if self.operator in self.valueoperators:
            return "{} value filter (key: {})".format(self.operator, self.datakey)
        elif self.operator in self.listoperators:
            return "{}-{} list filter (key: {})".format(self.anytestrun, self.operator, self.datakey)
        else:
            return " ".join(map(str, (prefix, self.expression1, self.operator, self.expression2)))

    def set_operator(self, operator):
        self.operator = operator
        if self.operator in list(IPETComparison.comparisondict.keys()):
            self.comparison = IPETComparison(self.operator)

    def getEditableAttributes(self):
        """
        returns editable attributes depending on the selected operator

        if a binary operator is selected, two expressions as left and right hand side of operator must be chosen
        For problem operators, no expressions are selectable.
        """
        parenteditables = super(IPETFilter, self).getEditableAttributes()

        if self.operator in list(IPETComparison.comparisondict.keys()):
            return parenteditables + ['operator', 'anytestrun', 'expression1', 'expression2']
        else:
            return parenteditables + ['operator', 'anytestrun', 'datakey']

    @staticmethod
    def getNodeTag():
        return IPETFilter.nodetag

    def getChildren(self):
        return self.values

    def acceptsAsChild(self, child):
        return child.__class__ is IPETValue

    def addChild(self, child):
        self.values.append(child)
        self._updatevalueset = True

    def removeChild(self, child):
        self.values.remove(child)
        self._updatevalueset = True

    def getActiveValues(self):
        return [x for x in self.values if x.isActive()]

    def getRequiredOptionsByAttribute(self, attr):
        return self.attribute2Options.get(attr, super(IPETFilter, self).getRequiredOptionsByAttribute(attr))

    def checkAndUpdateValueSet(self, dtype = None):
        """Update the value set of this filter if necessary
        """
        if not self._updatevalueset:
            return

        self.valueset = set([x.getValue(dtype) for x in self.getActiveValues()])
        updateset = set()

        #
        # check for test set names among the values
        #
        for i in self.valueset:

            if i in TestSets.getTestSets():
                logger.debug("Adding test set {} to value set".format(i))
                updateset = updateset.union(set(TestSets.getTestSetByName(i)))
        self.valueset = self.valueset.union(updateset)
        logger.debug("Complete value set of filter {}:\n{}".format(self.getName(), self.valueset))

        self._updatevalueset = False

    def applyValueOperator(self, df):

        dtype = df.dtypes[0]

        self.checkAndUpdateValueSet(dtype)
        contained = df.isin(self.valueset)
        logger.debug("Contained: {}\nData: {}".format(contained, df))
        if self.operator == "keep":
            return contained
        else:
            return ~contained

    def isAllDiff(self, x):
        valueset = set()
        for x_i in x:
            if x_i in valueset:
                return False
            valueset.add(x_i)
        return True

    def isOneEqual(self, x):
        return not self.isAllDiff(x)

    def isAllEqual(self, x):
        first_x = x.iloc[0]
        for x_i in x:
            if first_x != x_i:
                return False
        return True

    def isOneDiff(self, x):
        return not self.isAllEqual(x)

    def applyListOperator(self, df, groupindex):
        """
        Apply list operators 'diff' and 'equal' to the datakey.

        In combination with the 'anytestrun' attribute, there are
        four possibilities in total:

        | anytestrun | operator | result |
        |------------|----------|--------|
        | one        |diff      |True, if there are at least 2 different values in a group |
        | all        |diff      |True, if all values are different in this group |
        | one        |equal     |True, if at least one value occurs twice in a group |
        | all        |equal     |True, if there is only a single value for this group |
        """

        #
        # 1. chose the right list function
        #
        if self.operator == "diff":
            if self.anytestrun == "one":
                fun = self.isOneDiff
            else:
                fun = self.isAllDiff
        if self.operator == "equal":
            if self.anytestrun == "one":
                fun = self.isOneEqual
            else:
                fun = self.isAllEqual
        #
        # 2. store the original index
        #
        dfindex = df.set_index(groupindex).index
        #
        # 3. group by the index and apply the list function
        #
        f_by_group = df.groupby(groupindex)[self.datakey].apply(fun)
        #
        # 4. reindex the result to match the original data frame row count
        #
        f_by_group_as_frame = pd.DataFrame(f_by_group.reindex(index = dfindex, axis = 0))

        #
        # 5. set the index of the frame to match the original frame's index
        #
        f_by_group_as_frame.set_index(df.index, inplace = True)

        return f_by_group_as_frame

    def filterProblem(self, probname, testruns = []):
        """
        return True or False depending on the evaluation of the filter operator comparison
        """

        # apply an problem operator directly
        if self.operator in self.valueoperators:
            return self.applyValueOperator(probname)

        # evaluate the two expressions and filter according to the anytestrun attribute if one or all match the requirement
        for testrun in testruns:
            x = self.evaluate(self.expression1, probname, testrun)
            y = self.evaluate(self.expression2, probname, testrun)
            if self.anytestrun == 'one' and self.comparison.compare(x, y):
                return True
            elif self.anytestrun == 'all' and not self.comparison.compare(x, y):
                return False

        if self.anytestrun == 'one':
            return False
        return True

    def storeResult(self, df : pd.DataFrame, filtercol : pd.Series):
        """store a filter result for future reuse
        """
        self._storeddf_ = df
        self._storedcol_ = filtercol

    def getStoredResult(self, df : pd.DataFrame):
        """return the already stored result for this data frame
        """
        if self._storeddf_ is df:
            return self._storedcol_
        else:
            return None

    def applyFilter(self, df, groupindex = None):
        """Apply the filter to a data frame rowwise

        Parameters
        ----------

        df : DataFrame
            data frame object containing columns 'expression1' and 'expression2' or 'datakey'
            depending on the selected operator

        groupindex : list or None
            either a list of columns that should be used for groupby operations
            (only needed for list operators 'equal' and 'diff')


           Returns
           -------
           booleanseries :
        """
        if self.operator in self.listoperators:
            filtercol = self.applyListOperator(df, groupindex)
        elif self.operator in self.valueoperators:
            filtercol = self.applyValueOperator(df[[self.datakey]])

        else:
            x = self.evaluateValueDataFrame(df, self.expression1)
            y = self.evaluateValueDataFrame(df, self.expression2)
            try:
                x.columns = ["comp"]
            except:
                pass
            try:
                y.columns = ["comp"]
            except:
                pass
            filtercol = self.comparison.compare(x, y)

        if groupindex is None:
            return filtercol

        dfindex = df.set_index(groupindex).index

        renaming = {i:"{}_filter".format(i) for i in groupindex}

        filtercol = filtercol.rename(renaming, axis = 1)

        filtercol.index = dfindex
        # group the filter by the specified data frame index columns.
        if self.anytestrun == "one":
            func = np.any
        elif self.anytestrun == "all":
            func = np.all

        fcol_index = filtercol.groupby(filtercol.index).apply(func)
        #
        # reshape the column to match the original data frame rows
        #
        fcol = fcol_index.reindex(index = dfindex, axis = 0)

        return fcol

    def getNeededColumns(self, df):
        return [exp for exp in [self.expression1, self.expression2, self.datakey] if exp in df.columns]

    def evaluateValueDataFrame(self, df, value):
        if value in df.columns:
            return df[[value]]
        else:
            for conversion in [int, float, str]:
                try:
                    return conversion(value)
                except ValueError:
                    pass
        return value

    def evaluate(self, value, probname, testrun):
        if value in testrun.getKeySet():
            return testrun.getProblemDataById(probname, value)
        else:
            for conversion in [int, float, str]:
                try:
                    return conversion(value)
                except ValueError:
                    pass
        return value

    def filterProblems(self, probnames, testruns = []):
        return [self.filterProblem(probname, testruns) for probname in probnames]

    def getFilteredList(self, probnames, testruns = []):
        return [probname for probname in probnames if self.filterProblem(probname, testruns)]

    def toXMLElem(self):
        me = ElementTree.Element(IPETFilter.getNodeTag(), self.attributesToStringDict())
        for value in self.values:
            me.append(value.toXMLElem())
        return me

    def getDependency(self, i):
        if i == 1:
            value = self.expression1
        else:
            value = self.expression2
        try:
            float(value)
        except:
            return value
        return None

    def equals(self, other):
        """Compare this and another filter for equality
        """
        if not IpetNode.equals(self, other):
            return False

        if self.operator == other.operator:
            if self.operator not in IPETFilter.valueoperators:
                return True
            if len(self.values) != len(other.values):
                return False
            for v1, v2 in zip(self.values, other.values):
                if not v1.equals(v2):
                    return False

        return True


class IPETFilterGroup(IpetNode):
    """
    represents a list of filters, has a name attribute for quick tabular representation

    a filter group collects
    """
    nodetag = "FilterGroup"
    attribute2options = {"filtertype":["union", "intersection"]}

    editableAttributes = ["name", "filtertype"]

    # global data frame and index that are reused for several filter groups
    _glbdf_ = None
    _glbindex_ = None

    # intersection row index which can be shared across all filter groups of type "intersection"
    _glbinterrows_ = None

    def __init__(self, name = None, filtertype = "intersection", active = True):
        """
        constructor for a filter group

        Parameters:
        ----------
        name : a suitable name for the filter group
        filtertype : either 'union' or 'intersection'
        active : True or "True" if this filter group should be active, False otherwise
        """
        super(IPETFilterGroup, self).__init__(active)

        self.name = name
        self.filters = []
        if filtertype not in ["intersection", "union"]:
            raise ValueError("Error: filtertype <%s> must be either 'intersection' or 'union'" % filtertype)

        self.filtertype = filtertype

    def getEditableAttributes(self):
        return super(IPETFilterGroup, self).getEditableAttributes() + self.editableAttributes

    def getChildren(self):
        return self.filters

    def addChild(self, child):
        self.addFilter(child)

    def acceptsAsChild(self, child):
        return child.__class__ is IPETFilter

    def removeChild(self, child):
        self.filters.remove(child)

    @staticmethod
    def getNodeTag():
        return IPETFilterGroup.nodetag

    def getRequiredOptionsByAttribute(self, attr):
        return self.attribute2options.get(attr, super(IPETFilterGroup, self).getRequiredOptionsByAttribute(attr))

    def addFilter(self, filter_):
        """
        add a filter to the list of filters.

        Parameters
        ----------
        filter_ : an problem of IPETFilter
        """
        self.filters.append(filter_)

    def getName(self):
        return self.name

    def getActiveFilters(self):
        return [f for f in self.filters if f.isActive()]

    @staticmethod
    def setGlobalDataFrameAndIndex(df : pd.DataFrame, index):
        """Set global data frame and index for filtering, that will be reused by each filter group
        """

        IPETFilterGroup._glbdf_ = df
        IPETFilterGroup._glbindex_ = index

        IPETFilterGroup._glbinterrows_ = IPETFilterGroup.computeIntersectionRows(df, index)

    @staticmethod
    def computeIntersectionRows(df : pd.DataFrame, index):
        """Compute intersection rows of a given data frame and index

        Intersection rows denote a boolean index to define the subset of rows of the input frame
        considered as "intersection" for filter groups that have the "intersection" type (which is the default).
        The intersection row computation is slow and is reused across all
        filter groups with the intersection type.
        """

        logger.info("Computing rows for intersection groups")

        dfindex = df.set_index(index).index

        groups = df.groupby(index)
        instancecount = groups.apply(len).max()
        interrows = groups.apply(lambda x:len(x) == instancecount)

        return interrows.reindex(dfindex)

    def filterDataFrame(self, df, index):
        """
        filters a data frame object as the intersection of all values that match the criteria defined by the filters
        """

        activefilters = self.getActiveFilters()

        # treat the special case to keep everything quickly
        if len(activefilters) == 0 and self.filtertype == "union":
            return df

        # first, get the highest number of index occurrences. This number must be matched to keep the problem
        if self.filtertype == "intersection":
            if df is IPETFilterGroup._glbdf_:
                intersection_index = IPETFilterGroup._glbinterrows_
            else:
                intersection_index = IPETFilterGroup.computeIntersectionRows(df, index)

        elif self.filtertype == "union":
            intersection_index = None

        for f_ in activefilters:

            # check first if the column has already been stored
            storedcol = f_.getStoredResult(df)
            if storedcol is not None:
                fcol = storedcol
            else:
                # apply the filter to the data frame rowwise and store the result in a temporary boolean column
                fcol = f_.applyFilter(df, index)

            if intersection_index is not None:
                intersection_index = intersection_index & fcol
            else:
                intersection_index = fcol

        #
        # aggregate the single, elementwise filters into a single intersection
        # series with one row per index element
        #
        # intersection_index = pd.concat(index_series, axis = 1).apply(np.all, axis = 1)

        lvalues = intersection_index.values

        return lvalues

    def filterProblem(self, probname, testruns = []):
        for filter_ in self.getActiveFilters():
            if not filter_.filterProblem(probname, testruns):
                return False

        return True

    def getNeededColumns(self, df):
        needed = []
        for filter_ in self.filters:
            needed += filter_.getNeededColumns(df)

        return needed

    def toXMLElem(self):
        me = ElementTree.Element('FilterGroup', self.attributesToStringDict())

        for filter_ in self.filters:
            me.append(filter_.toXMLElem())

        return me

    @staticmethod
    def processXMLElem(elem):
        """
        inspect and process an xml element
        """
        if elem.tag == IPETFilterGroup.getNodeTag():
            filtergroup = IPETFilterGroup(**elem.attrib)
            for child in elem:
                filtergroup.addFilter(IPETFilterGroup.processXMLElem(child))
            return filtergroup
        elif elem.tag == IPETFilter.getNodeTag():
            return IPETFilter.processXMLElem(elem)

    @staticmethod
    def fromXML(xmlstring):
        """
        parse an xml string matching the filter group XML syntax
        """
        tree = ElementTree.fromstring(xmlstring)
        return IPETFilterGroup.processXMLElem(tree)

    @staticmethod
    def fromXMLFile(xmlfilename):
        """
        parse a file containing an xml string matching the filter group XML representation syntax
        """
        tree = ElementTree.parse(xmlfilename)
        return IPETFilterGroup.processXMLElem(tree.getroot())
