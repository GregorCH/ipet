'''
Created on 24.02.2015

@author: bzfhende
'''

from ipet.Comparator import Comparator
import argparse
import sys
from ipet.IPETEvalTable import IPETEvaluation
import pandas as pd
import re

# possible arguments in the form name,default,short,description #
clarguments = [('--comparatorfile', None,'-c', "A comparator file name (must have .cmp file extension) in cmp-format to read"),
               ('--evalfile', None,'-e', "An evaluation file name (must have .xml file extension) in xml-format to read"),
               ('--recollect', False,'-r', "Should the loaded comparator recollect data before proceeding?"),
               ('--savecomparator', False,'-s', "Should the comparator data be overwritten? Makes only sense if combined with '--recollect True'"),
               ('--externaldata', None,'-E', "Should external data such as additional instance information be used?"),
               ('--defaultgroup', None,'-d', "overwrites the default group specified in the evaluation"),
               ('--fileextension', None,'-f', "file extension for writing evaluated data, e.g., csv, tex, stdout, txt"),
               ('--compformatstring', None,'-C', "a format string like %%.5f for compare columns (those ending with ...'Q')"),
               ('--groupkey', None,'-g', "overwrites the group key as, e.g., 'Settings' specified in the evaluation by something else"),
               ('--prefix', None,'-p', "a prefix string for every file written, only useful combined with --filextension"),
               ('--keysearch', None,'-k', "a string containing a regular expression to search all columns that match this expression")]

argparser = argparse.ArgumentParser(prog="Ipet Startup Script", \
                                 description="evaluates experimental data according to an evaluation XML-file")
for name, default, short, description in clarguments:
    argparser.add_argument(short, name, default=default,help=description)

argparser.add_argument('-t', '--testrunfiles', nargs='*', default=[], help="list of .trn files that should used for the evaluation")
argparser.add_argument("-n", "--nooptauto", action="store_true", default=False, help="Disable calculation of optimal auto settings")

if __name__ == '__main__':
    try:
        n = vars(argparser.parse_args())
        globals().update(n)
    except:
        print "Wrong Usage"
    #if globals().get("help") is not None:

    #initialize a comparator
    comparator = None
    print n
    if evalfile is None:
        print "please provide an eval file!"
        sys.exit(0)


    if comparatorfile is None and testrunfiles == []:
        print "please provide either a comparatorfile or (multiple, if needed) .trn testrun files"
        sys.exit(0)
    theeval = IPETEvaluation.fromXMLFile(evalfile)

    if nooptauto:
        theeval.setEvaluateOptAuto(False)
    else:
        theeval.setEvaluateOptAuto(True)
    if comparatorfile is not None:
        comp = Comparator.loadFromFile(comparatorfile)
    else:
        comp = Comparator()

    for trfile in testrunfiles:
        comp.addLogFile(trfile)

    if recollect is not False:
        print "Recollecting data"
        comp.collectData()

    if savecomparator is not False:
        comp.saveToFile(comparatorfile)

    if defaultgroup is not None:
        theeval.setDefaultGroup(defaultgroup)

    if groupkey is not None:
        theeval.setGroupKey(groupkey)

    if externaldata is not None:
        comp.addExternalDataFile(externaldata)
    else:
        comp.externaldata = None

    if compformatstring is not None:
        theeval.setCompareColFormat(compformatstring)
        
    if keysearch is not None:
        print "Starting key enumeration"
        for key in comp.getDatakeys():
            if re.search(keysearch, key):
                print "    " + key
        print "End key enumeration"
        exit(0)
        
    rettab, retagg = theeval.evaluate(comp)


    theeval.streamDataFrame(rettab, "Instancewise Results", "stdout")
    print
    theeval.streamDataFrame(retagg, "Aggregated Results", "stdout")

    #for tr in comp.testrunmanager.getManageables():
        #for col in tr.data.columns:
            #print col


    if fileextension is not None:
        path = "."
        extension = fileextension
        prefixstr = prefix and prefix or ""
        for fg in theeval.filtergroups:
            instancewisename = "%s/%s%s"%(path, prefixstr, fg.name)
            theeval.streamDataFrame(theeval.filtered_instancewise[fg.name], instancewisename, extension)
            print "Instance-wise data written to %s.%s"%(instancewisename,extension)
            aggname = instancewisename + "_agg"
            theeval.streamDataFrame(theeval.filtered_agg[fg.name], aggname, extension)
            print "aggregated data written to %s.%s"%(aggname,extension)

        filename = "%s/%s"%(path, "_".join(prefixstr, "inst_combined") if prefixstr != "" else "inst_combined")
        theeval.streamDataFrame(rettab, filename, extension)
        print "combined instance data written to %s.%s"%(filename,extension)
        # print the combined aggregated data if there are multiple filter groups present
        filename = "%s/%s"%(path, "_".join(prefixstr, "agg_combined") if prefixstr != "" else "agg_combined")
        theeval.streamDataFrame(retagg, filename, extension)
        print "combined aggregated data written to %s.%s"%(filename,extension)

    #print pd.concat([rettab, theeval.levelonedf], axis=1)

