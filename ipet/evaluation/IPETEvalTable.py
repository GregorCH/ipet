'''
Created on 24.02.2015

@author: Gregor Hendel
'''
import pandas as pd
from ipet.evaluation import Aggregation
import xml.etree.ElementTree as ElementTree
from .IPETFilter import IPETFilterGroup
import numpy
from ipet.concepts.Editable import Editable
from ipet.concepts.IPETNode import IpetNode
from ipet.misc import misc
import logging

class IPETEvaluationColumn(Editable, IpetNode):

    nodetag = "Column"

    editableAttributes = ["name", "origcolname", "formatstr","transformfunc", "constant",
                 "nanrep", "minval", "maxval", "comp", "translevel", "regex"]

    possibletransformations = {None:(0,0), 
                               "abs":(1,1),
                               "getGap":(2, 2),
                               "getCplexGap":(2, 2),
                               "getVariabilityScore":(1, -1),
                               "prod":(1,-1),
                               "sum":(1,-1),
                               "subtract":(2,2), 
                               "divide":(2, 2),
                               "log10":(1, 1),
                               "log":(1, 1),
                               "mean":(1, -1),
                               "median":(1, -1),
                               "std":(1, -1),
                               "min":(1, -1),
                               "max":(1, -1)}
    possiblecomparisons = [None, "quot", "difference"] + ["quot shift. by %d" % shift for shift in (1, 5, 10, 100, 1000)]
    
    requiredOptions = {"comp":possiblecomparisons,
                       "origcolname":"datakey",
                       "translevel":[0,1],
                       "transformfunc":list(possibletransformations.keys())}

    def __init__(self, origcolname=None, name=None, formatstr=None, transformfunc=None, constant=None,
                 nanrep=None, minval=None, maxval=None, comp=None, regex=None, translevel=None):
        '''
        constructor of a column for the IPET evaluation

        Parameters
        ----------
        origcolname : column name in the original data frame
        name : column name that will be displayed for this column
        formatstr : a format string to define how the column gets printed, if no format

        transformfunc : a transformation function, that should be applied to all children
                        columns of this column recursively. See also the 'translevel' attribute

        constant : should this column represent a constant value?

        nanrep : replacement of nan-values for this column

        minval : a minimum value for all elements in this column

        maxval : a maximum value for all elements in this column

        comp : should a comparison for this column with the default group be made? This will append one column per group with this column
               name and an appropriate suffix. Any nonexistent comp will raise a ValueError

        regex : use for selecting a set of columns at once by including regular expression wildcards such as '*+?' etc.

        translevel : Specifies the level on which to apply the defined transformation for this column. Use translevel=0 to handle every instance
                     and group separately, and translevel=1 for an instance-wise transformation over all groups, e.g., the mean solving time
                     if five permutations were tested. Columns with translevel=1 are appended at the end of the instance-wise table
        '''

        self.origcolname = origcolname
        self.name = name

        self.formatstr = formatstr
        self.transformfunc = transformfunc
        self.constant = constant

        self.nanrep = nanrep
        self.minval = minval
        self.maxval = maxval
        self.translevel = translevel
        self.set_comp(comp)
        self.regex = regex


        self.aggregations = []
        self.children = []

    def checkAttributes(self):
        if self.origcolname is None and self.regex is None and self.transformfunc is None and self.constant is None:
            raise AttributeError("Error constructing this column: No origcolname, regex, constant, or transformfunction specified")
        if self.transformfunc is not None:
            if self.transformfunc not in self.possibletransformations:
                raise AttributeError("Error: Column <%s> specified unknown transformation <%s>" % (self.getName(), self.transformfunc))
            minval, maxval = self.possibletransformations[self.transformfunc]
            if len(self.children) < minval or maxval != -1 and len(self.children) > maxval:
                raise AttributeError("Error: Column <%s> specifies wrong number of children for transformation <%s>" % (self.getName(), self.transformfunc))

    def addChild(self, child):
        if not self.acceptsAsChild(child):
            raise ValueError("Cannot accept child %s as child of a column node"%child)
        if child.__class__ is IPETEvaluationColumn:
            self.children.append(child)
        elif child.__class__ is Aggregation:
            self.aggregations.append(child)

    def getChildren(self):
        return self.children + self.aggregations

    def acceptsAsChild(self, child):
        return child.__class__ in (IPETEvaluationColumn, Aggregation)

    def removeChild(self, child):
        if child.__class__ is IPETEvaluationColumn:
            self.children.remove(child)
        elif child.__class__ is Aggregation:
            self.aggregations.remove(child)

    @staticmethod
    def getNodeTag():
        return IPETEvaluationColumn.nodetag

    def getEditableAttributes(self):
        return self.editableAttributes

    def getRequiredOptionsByAttribute(self, attr):
        return self.requiredOptions.get(attr, None)

    def getName(self):
        '''
        infer the name for this column

        if this column was constructed with a column name, the name is used
        else if this column represents an original column of the data frame,
        the original column name is used, otherwise, we construct an
        artificial name that represents how this column is constructed
        '''
        if self.name is not None:
            return self.name
        elif self.origcolname is not None:
            return self.origcolname
        elif self.regex is not None:
            return self.regex
        elif self.constant is not None:
            return "Const_%s"%self.constant
        else:
            return self.transformfunc + ','.join((child.getName() for child in self.children))

    def parseValue(self, val, df = None):
        '''
        parse a value into an integer (prioritized) or float
        '''
        for conversion in [int, float]:
            try:
                return conversion(val)
            except:
                pass
        if df is not None and val in df.columns:
            return df[val]
        return None

    def parseConstant(self):
        '''
        parse the constant attribute, which is a string, into an integer (prioritized) or float
        '''
        return self.parseValue(self.constant)

    def addAggregation(self, agg):
        self.aggregations.append(agg)

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
                raise ValueError("Trying to set an unknown comparison method '%s' for column '%s', should be in\n %s"%(newvalue, self.getName(), ", ".join((repr(c) for c in self.possiblecomparisons))))

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
                    return lambda x,y:numpy.true_divide(x + shift, y + shift)
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

    def toXMLElem(self):
        '''
        convert this Column into an XML node
        '''

        # keep only non NAN elements
        myelements = {k:self.__dict__[k] for k in self.getEditableAttributes() if self.__dict__.get(k) is not None}


        me = ElementTree.Element(IPETEvaluationColumn.getNodeTag(), myelements)

        # iterate through children and aggregations and convert them to xml nodes
        for child in self.children:
            me.append(child.toXMLElem())

        for agg in self.aggregations:
            me.append(agg.toXMLElem())

        return me

    @staticmethod
    def processXMLElem(elem):

        if elem.tag == IPETEvaluationColumn.getNodeTag():
            column = IPETEvaluationColumn(**elem.attrib)
            for child in elem:
                if child.tag == 'Aggregation':
                    column.addAggregation(Aggregation.processXMLElem(child))
                elif child.tag == IPETEvaluationColumn.getNodeTag():
                    column.addChild(IPETEvaluationColumn.processXMLElem(child))
            return column

    def getColumnData(self, df):
        '''
        Retrieve the data associated with this column
        '''

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
                    print("Could not retrieve data %s"%self.origcolname)
                    result = pd.Series(numpy.nan, index=df.index)


            elif self.regex is not None:
                result = df.filter(regex = self.regex)
            elif self.constant is not None:
                df[self.getName()] = self.parseConstant()
                result = df[self.getName()]
        else:
            # try to apply an element-wise transformation function to the children of this column
            # gettattr is equivalent to numpy.__dict__[self.transformfunc]
            try:
                transformfunc = getattr(numpy, self.transformfunc)
            except AttributeError:
                transformfunc = getattr(misc, self.transformfunc)

            # concatenate the children data into a new data frame object
            argdf = pd.concat([child.getColumnData(df) for child in self.children], axis=1)

            if self.getTransLevel() == 1:

                # group the whole table per instance #

                argdf = argdf.groupby(level=0)

                #determine the axis along which to apply the transformation later on
                applydict={}
            else:
                applydict=dict(axis=1)

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

        if self.nanrep is not None:
            nanrep = self.parseValue(self.nanrep, df)
            if nanrep is not None:
                result = result.fillna(nanrep)
        if self.minval is not None:
            minval = self.parseValue(self.minval, df)
            if minval is not None:
                result = numpy.maximum(result, minval)
        if self.maxval is not None:
            maxval = self.parseValue(self.maxval, df)
            if maxval is not None:
                result = numpy.minimum(result, maxval)

        return result


    def getStatsTests(self):
        return [agg.getStatsTest() for agg in self.aggregations if agg.getStatsTest() is not None]


class FormatFunc:

    def __init__(self, formatstr):
        self.formatstr = formatstr[:]

    def beautify(self, x):
        return (self.formatstr%x)



class IPETEvaluation(Editable, IpetNode):
    '''
    evaluates a comparator with given group keys, columns, and filter groups
    
    An evaluation transfers raw, collected data from a collection of testruns
    into tables based on selected columns, filter groups, and aggregations.
    An evaluation and its friends come with an easy-to-modify  
    By defining multiple evaluations, 
    it is therefore possible to view the same raw data through multiple angles
    
    '''
    nodetag = "Evaluation"
    #todo put tex, csv etc. here as other possible streams for filter group output
    possiblestreams=['stdout', 'tex', 'txt', 'csv']
    DEFAULT_GROUPKEY="Settings"
    DEFAULT_DEFAULTGROUP="default"
    DEFAULT_COMPARECOLFORMAT="%.3f"
    ALLTOGETHER="_alltogether_"

    editableAttributes = ["groupkey", "defaultgroup", "evaluateoptauto", "sortlevel", "comparecolformat"]
    attributes2Options = {"evaluateoptauto":[True, False], "sortlevel":[0,1]}
    def __init__(self, groupkey=DEFAULT_GROUPKEY, defaultgroup=DEFAULT_DEFAULTGROUP, evaluateoptauto=True,
                 sortlevel=0, comparecolformat=DEFAULT_COMPARECOLFORMAT):
        '''
        constructs an Ipet-Evaluation

        Parameters
        ----------
        groupkey : the key by which groups should be built, eg, 'Settings'
        defaultgroup : the name of the default group
        evaluateoptauto : should optimal auto settings be calculated?
        sortlevel : level on which to base column sorting, '0' for group level, '1' for column level
        '''
        self.filtergroups = []
        self.groupkey = groupkey
        self.defaultgroup = defaultgroup
        self.comparecolformat = comparecolformat[:]
        self.columns = []
        self.set_evaluateoptauto(evaluateoptauto)
        self.sortlevel = int(sortlevel)
        self.evaluated = False

    def getName(self):
        return self.nodetag
    
    def isEvaluated(self):
        '''
        returns whether this evaluation has been evaluated since its columns or filter groups have been modified
        '''
        return self.evaluated
    
    def setEvaluated(self, evaluated):
        '''
        change the flag if this evaluation has been evaluated since its last modification
        '''
        self.evaluated = evaluated

    def set_evaluateoptauto(self, evaluateoptauto):
        self.evaluateoptauto = True if evaluateoptauto in [True, "True"] else False

    def set_sortlevel(self, sortlevel):
        self.sortlevel = int(sortlevel)

    def setCompareColFormat(self, comparecolformat):
        self.comparecolformat = comparecolformat[:]

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
            raise ValueError("Cannot accept child %s as child of an evaluation node"%child)
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
        return self.attributes2Options.get(attr)

    def addFilterGroup(self, fg):
        # check if a filter group of the same name already exists
        if fg.getName() in (fgroup.getName() for fgroup in self.filtergroups):
            raise ValueError("Error: Filter group of name <%s> already existing in current evaluation!" % fg.getName())

        self.filtergroups.append(fg)
        self.setEvaluated(False)

    def removeFilterGroup(self, fg):
        self.filtergroups.remove(fg)
        self.setEvaluated(False)

    def setGroupKey(self, gk):
        self.groupkey = gk


    def setDefaultGroup(self, dg):
        self.defaultgroup = dg
        self.setEvaluated(False)

    def addColumn(self, col):
        self.columns.append(col)
        self.setEvaluated(False)

    def removeColumn(self, col):
        self.columns.remove(col)
        self.setEvaluated(False)

    def setEvaluateOptAuto(self, evaloptauto):
        '''
        should the evaluation calculate optimal auto settings?
        '''
        self.set_evaluateoptauto(evaloptauto)

    def reduceToColumns(self, df_long):
        usercolumns = []

        lvlonecols = [col for col in self.columns if col.getTransLevel() == 1]
        if len(lvlonecols) > 0:
            self.levelonedf = pd.concat([col.getColumnData(df_long) for col in lvlonecols], axis=1)
            self.levelonedf.columns = [col.getName() for col in lvlonecols]
        else:
            self.levelonedf = None
        #treat columns differently for level=0 and level=1
        for col in self.columns:
            if col.getTransLevel() == 0:
                df_long[col.getName()] = col.getColumnData(df_long)
                usercolumns.append(col.getName())

                # look if a comparison with the default group should be made
                if col.getCompareMethod() is not None:
                    compcol = dict(list(df_long.groupby(self.groupkey)[col.getName()]))[self.defaultgroup]
                    
                    # save as temporary column. This will expand the smaller compcol index to the larger data frame
                    df_long["_tmpcol_"] = compcol
                    
                    # append the right suffix to the column name
                    comparecolname = col.getName() + col.getCompareSuffix()
                    
                    # apply the correct comparison method to the original and the temporary column
                    compmethod = col.getCompareMethod()
                    method = lambda x:compmethod(*x) 
                    df_long[comparecolname] = df_long[[col.getName(), "_tmpcol_"]].apply(method, axis=1)
                    usercolumns.append(comparecolname)



        # concatenate level one columns into a new data frame and treat them as the altogether setting

        neededcolumns = [col for col in [self.groupkey, 'Status', 'SolvingTime', 'TimeLimit'] if col not in usercolumns]

        additionalfiltercolumns = []
        for fg in self.filtergroups:
            additionalfiltercolumns += fg.getNeededColumns(df_long)

        additionalfiltercolumns = list(set(additionalfiltercolumns))
        additionalfiltercolumns = [afc for afc in additionalfiltercolumns if afc not in set(usercolumns + neededcolumns)]

        result = df_long.loc[:,usercolumns + neededcolumns + additionalfiltercolumns]
        self.usercolumns = usercolumns
        return result

    def calculateNeededData(self, df):
        df['_time_'] = (df.Status.isin(('better', 'timelimit')))
        df['_limit_'] = ((df['_time_']) | df.Status.isin(['nodelimit', 'memorylimit', 'userinterrupt', 'gaplimit']))
        df['_fail_'] = (df.Status.apply(lambda x: True if x.startswith("fail") else False))
        df['_abort_'] = (df.Status == 'fail (abort)')

        df['_solved_'] = (~df['_limit_']) & (~df['_fail_']) & (~df['_abort_'])

        df['_count_'] = 1
        df['_unkn_'] = (df.Status == 'unknown')
        df['ProblemNames'] = df.index

        return df

    def toXMLElem(self):
        me = ElementTree.Element(IPETEvaluation.getNodeTag(), {'groupkey':self.groupkey, 'defaultgroup':self.defaultgroup})
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
            ev = IPETEvaluation()
            ev.setGroupKey(elem.attrib.get('groupkey', IPETEvaluation.DEFAULT_GROUPKEY))
            ev.setDefaultGroup(elem.attrib.get('defaultgroup', IPETEvaluation.DEFAULT_DEFAULTGROUP))

        for child in elem:
            if child.tag == IPETFilterGroup.getNodeTag():
                # add the filter group to the list of filter groups
                fg = IPETFilterGroup.processXMLElem(child)
                ev.addFilterGroup(fg)

            elif child.tag == IPETEvaluationColumn.getNodeTag():
                ev.addColumn(IPETEvaluationColumn.processXMLElem(child))
        return ev

    def convertToHorizontalFormat(self, df):
        horidf = df[self.usercolumns + ['ProblemNames', self.groupkey]].pivot('ProblemNames', self.groupkey).swaplevel(0, 1, axis=1)
        horidf.sortlevel(axis=1, level=self.sortlevel)
        return horidf

    def checkStreamType(self, streamtype):
        if streamtype not in self.possiblestreams:
            return False
        else:
            return True

    def getColumnFormatters(self, df):
        '''
        returns a formatter dictionary for all columns of this data frame

        expects a Multiindex column data frame df
        '''
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
        for col in self.columns:

            #determine all possible comparison columns and append them to the list
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
            raise ValueError("Stream error: Unknown stream type %s"%streamtype)
        streammethod = getattr(self, "streamDataFrame_%s"%streamtype)

        formatters = self.getColumnFormatters(df)

        streammethod(df, filebasename, formatters)

    def streamDataFrame_stdout(self, df, filebasename, formatters = {}):
        '''
        print to console
        '''
        print("%s:"%filebasename)
        print(df.to_string(formatters=formatters))

    def streamDataFrame_tex(self, df, filebasename, formatters = {}):
        '''
        write tex output
        '''
        with open("%s.tex"%filebasename, "w") as texfile:
            texfile.write(df.to_latex(formatters = formatters))

    def streamDataFrame_csv(self, df, filebasename, formatters = {}):
        with open("%s.csv"%filebasename, "w") as csvfile:
            df.to_csv(csvfile, formatters = formatters)

    def streamDataFrame_txt(self, df, filebasename, formatters = {}):
        '''
        write txt output
        '''
        with open("%s.txt"%filebasename, "w") as txtfile:
            df.to_string(txtfile, formatters = formatters, index_names = False)


    def findStatus(self, statuscol):
        uniques = set(statuscol.unique())
        for status in ["ok", "timelimit", "nodelimit", "memlimit", "unknown", "fail", "abort"]:
            if status in uniques:
                return status
        else:
            return statuscol.unique()[0]

    def calculateOptimalAutoSettings(self, df):
        '''
        calculate optimal auto settings instancewise
        '''
        grouped = df.groupby(level=0)

        optstatus = grouped["Status"].apply(self.findStatus)
        opttime = grouped["SolvingTime"].apply(numpy.min)
        opttimelim = grouped["TimeLimit"].apply(numpy.mean)

        optdf = pd.concat([optstatus, opttime, opttimelim], axis=1)
        optdf[self.groupkey] = "OPT. AUTO"

        aggfuncs = {'_solved_':numpy.max}
        useroptdf = pd.concat([grouped[col].apply(aggfuncs.get(col, numpy.min)) for col in self.usercolumns if col not in ["Status", "SolvingTime", "TimeLimit"]], axis = 1)
        optdf = pd.concat([optdf, useroptdf], axis=1)


        return optdf

    def checkMembers(self):
        '''
        checks the evaluation members for inconsistencies
        '''
        for col in self.columns:
            try:
                col.checkAttributes()
            except Exception as e:
                raise AttributeError("Error in column definition of column %s:\n   %s" % (col.getName(), e))
            

            
    def getAggregatedGroupData(self, filtergroup):
        if not filtergroup in self.filtergroups:
            raise ValueError("Filter group %s (name:%s) is not contained in evaluation filter groups")
        return self.filtered_agg[filtergroup.getName()]
    
    def getInstanceGroupData(self, filtergroup):
        return self.filtered_instancewise[filtergroup.getName()]
    
    def getAggregatedData(self):
        return self.retagg
    
    def getInstanceData(self):
        return self.rettab

    def evaluate(self, exp):
        '''
        evaluate the data of an Experiment instance exp

        Parameters
        ----------
        exp : an experiment instance for which data has already been collected

        Returns
        -------
        rettab : an instance-wise table of the specified columns
        retagg : aggregated results for every filter group and every entry of the specified
        '''
        self.checkMembers()

        #data is concatenated along the rows and eventually extended by external data
        data = exp.getJoinedData()
        
        if not self.groupkey in data.columns:
            raise KeyError(" Group key is missing in data:", self.groupkey)
        elif self.defaultgroup not in data[self.groupkey].values:
            possiblebasegroups = sorted(data[self.groupkey].unique())
            logging.info(" Default group <%s> not contained, have only: %s" % (self.defaultgroup, ", ".join(possiblebasegroups)))
            self.defaultgroup = possiblebasegroups[0]
            logging.info(" Using value <%s> as base group"%(self.defaultgroup))
            
        columndata = self.reduceToColumns(data)

        if self.evaluateoptauto:
            opt = self.calculateOptimalAutoSettings(columndata)
            columndata = pd.concat([columndata, opt])

        columndata = self.calculateNeededData(columndata)

        # compile a results table containing all instances
        ret = self.convertToHorizontalFormat(columndata)
        if self.levelonedf is not None:
            self.levelonedf.columns = pd.MultiIndex.from_product([[IPETEvaluation.ALLTOGETHER], self.levelonedf.columns])
            self.rettab = pd.concat([ret, self.levelonedf], axis=1)
        else:
            self.rettab = ret


        self.instance_wise = ret
        self.agg = self.aggregateToPivotTable(columndata)

        self.filtered_agg = {}
        self.filtered_instancewise = {}
        # filter column data and group by group key #
        for fg in self.filtergroups:
            # iterate through filter groups, thereby aggregating results for every group
            reduceddata = self.applyFilterGroup(columndata, fg)
            self.filtered_instancewise[fg.name] = self.convertToHorizontalFormat(reduceddata)
            self.filtered_agg[fg.name] = self.aggregateToPivotTable(reduceddata)

        if len(self.filtergroups) > 0:
            dfs = [self.filtered_agg[fg.name] for fg in self.filtergroups if not self.filtered_agg[fg.name].empty]
            names = [fg.name for fg in self.filtergroups if not self.filtered_agg[fg.name].empty]
            self.retagg = pd.concat(dfs, keys=names, names=['Group'])
        else:
            self.retagg = pd.DataFrame()

        self.setEvaluated(True)
        return self.rettab, self.retagg
    '''
        for fg in self.filtergroups:
            self.applyFilterGroup(columndata, fg, comp)
    '''
    def applyFilterGroup(self, df, fg):
        return fg.filterDataFrame(df)

    def aggregateToPivotTable(self, df):
        # the general part sums up the number of instances falling into different categories
        generalpart = df[['_count_', '_solved_', '_time_', '_limit_', '_fail_', '_abort_', '_unkn_'] + [self.groupkey]].pivot_table(index = self.groupkey, aggfunc = sum)

        # test if there is any aggregation to be calculated
        hasaggregation = False
        stop = False
        for col in self.columns:
            for _ in col.aggregations:
                hasaggregation = True
                stop = True
                break
            if stop:
                break
        # if no aggregation was specified, print only the general part
        if not hasaggregation:
            return generalpart

        # column aggregations aggregate every column and every column aggregation
        colaggpart = pd.concat((df[[col.getName(), self.groupkey]].pivot_table(index = self.groupkey, aggfunc = agg.aggregate) for col in self.columns for agg in col.aggregations), axis = 1)

        # print df[["DualInt", "Settings"]].pivot_table(index = "Settings", aggfunc = numpy.min)
        # rename the column aggregations
        # print colaggpart
        newnames = ['_'.join((col.getName(), agg.getName())) for col in self.columns for agg in col.aggregations]
        # print newnames
        colaggpart.columns = newnames

        # determine the row in the aggregated table corresponding to the default group
        if self.defaultgroup in colaggpart.index:
            defaultrow = colaggpart.loc[self.defaultgroup, :]
        else:
            # if there is no default setting, take the first group as default group
            try:
                defaultrow = colaggpart.iloc[0, :]
            except:
                defaultrow = numpy.nan

        # determine quotients
        comppart = colaggpart / defaultrow
        comppart.columns = [col + 'Q' for col in colaggpart.columns]

        #apply statistical tests, whereever possible
        statspart = self.applyStatsTests(df)

        #glue the parts together
        parts = [generalpart, colaggpart, comppart]
        if statspart is not None:
            parts.append(statspart)

        return pd.concat(parts, axis = 1)

    def applyStatsTests(self, df):
        '''
        apply statistical tests defined by each column
        '''

        # group the data by the groupkey
        groupeddata = dict(list(df.groupby(self.groupkey)))
        stats = []
        names = []
        for col in self.columns:
            if len(col.getStatsTests()) == 0:
                continue
            defaultvalues = None
            try:
                defaultvalues = groupeddata[self.defaultgroup][col.getName()]
            except KeyError:
                logging.info("Sorry, cannot retrieve default values for column %s, key %s for applying statistical test)"%(col.getName(), self.defaultgroup))
                continue

            # iterate through the stats tests associated with each column
            for statstest in col.getStatsTests():
                stats.append(df[[self.groupkey, col.getName()]].pivot_table(index=self.groupkey, aggfunc=lambda x:statstest(x, defaultvalues)))
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
        for col in self.columns:
            origcolname = col.getName()
            partialdf = df.xs(origcolname, level=1, axis=1, drop_level=False)

            for partialcol in partialdf.columns:
                columnorder.append(partialcol)
                results[partialcol] = {}
                for agg in col.aggregations:
                    results[partialcol][agg.getName()] = agg.aggregate(df[partialcol])

        return pd.DataFrame(results)[columnorder]

if __name__ == '__main__':
    ev = IPETEvaluation.fromXMLFile('../test/testevaluate.xml')
#     ev.addColumn(IPETEvaluationColumn('SolvingTime'))
#     ev.addColumn(IPETEvaluationColumn('Nodes'))
#     group = IPETFilterGroup('new')
#     filter1 = IPETFilter('SolvingTime', '0.01', 'ge', True)
#     filter2 = IPETFilter('Nodes', '10', 'le', True)
#     group.addFilter(filter1)
#     group.addFilter(filter2)
    agg = Aggregation('shmean', shiftby=10)
    #ev.columns[0].addAggregation(agg)
    #print ElementTree.tostring(agg.toXMLElem())

    from ipet.Comparator import Comparator
    comp = Comparator.loadFromFile('../test/.testcomp.cmp')
    comp.externaldata = None
    rettab, retagg = ev.evaluate(comp)
    print(rettab.to_string())
    print(retagg.to_string())
    xml = ev.toXMLElem()
    from xml.dom.minidom import parseString
    dom = parseString(ElementTree.tostring(xml))
    with open("myfile.xml", 'w') as myfile:
        myfile.write(dom.toprettyxml())
#     xml = ev.toXMLElem()
#     dom = parseString(ElementTree.tostring(xml))
#     print dom.toprettyxml()
#
