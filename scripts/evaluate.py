'''
Created on 24.02.2015

@author: bzfhende
'''

from ipet.Experiment import Experiment
import argparse
import sys
from ipet.evaluation.IPETEvalTable import IPETEvaluation

import re
import textwrap
from PyQt4.Qt import QApplication
from qipet.IpetEvaluationEditorApp import IpetEvaluationEditorApp

description = \
'''
    produces an table evaluation of test runs according to an evaluation XML-file

    An evaluation file is an xml file that specifies a number of columns of the original log file data and a number of interesting groups of instances for which aggregated results of the data should be produced.

    The script produces two tables: the first, instancewise table has all specified columns for every passed log file and one row per instance. The second, aggregated table shows aggregated statistics for all specified filter groups for this evaluation.
'''

epilog = \
    '''
    =================
    Examples of Usage
    =================

    The simplest way to invoke the script is to specify the name of a parsed log file and the name of a valid evaluation file, e.g.,

       python evaluate.py -t sometestrun.trn -e evaluation.xml

    A sample evaluation script to start with is '[IPET-ROOT]/scripts/evaluation.xml' which uses only readily available data like the number of solving nodes and the solving time in seconds.


    Key Search
    ==========




    '''


# possible arguments in the form name,default,short,description #
clarguments = [('--experimentfile', None, '-x', "An experiment file name (must have .ipx file extension) in cmp-format to read"),
               ('--evalfile', None,'-e', "An evaluation file name (must have .xml file extension) in xml-format to read"),
               ('--recollect', False, '-r', "Should the loaded experiment recollect data before proceeding?"),
               ('--saveexperiment', False, '-s', "Should the experiment data be overwritten? Makes only sense if combined with '--recollect True'"),
               ('--externaldata', None,'-E', "Should external data such as additional instance information be used?"),
               ('--defaultgroup', None,'-d', "overwrites the default group specified in the evaluation"),
               ('--fileextension', None,'-f', "file extension for writing evaluated data, e.g., csv, tex, stdout, txt"),
               ('--compformatstring', None,'-C', "a format string like %%.5f for compare columns (those ending with ...'Q')"),
               ('--groupkey', None,'-g', "overwrites the group key as, e.g., 'Settings' specified in the evaluation by something else"),
               ('--prefix', None,'-p', "a prefix string for every file written, only useful combined with --filextension"),
               ('--keysearch', None,'-k', "a string containing a regular expression to search all columns that match this expression")]

argparser = argparse.ArgumentParser(prog="IPET command line evaluation", \
                                 description=description,
                                 epilog = textwrap.dedent(epilog),
                                 formatter_class = argparse.RawDescriptionHelpFormatter)
for name, default, short, description in clarguments:
    argparser.add_argument(short, name, default=default,help=description)

argparser.add_argument('-t', '--testrunfiles', nargs='*', default=[], help="list of .trn files that should used for the evaluation")
argparser.add_argument("-n", "--nooptauto", action="store_true", default=False, help="Disable calculation of optimal auto settings")

argparser.add_argument("-A", "--showapp", action = "store_true", default = False, help = "Display the Evaluation Editor app to modify the evaluation")
if __name__ == '__main__':
    try:
        n = vars(argparser.parse_args())
        globals().update(n)
    except:
        if not re.search(" -+h", ' '.join(sys.argv)) :
            print "Wrong Usage, use --help for more information."
        exit()
    #if globals().get("help") is not None:

    # initialize a experiment
    experiment = None
    print n
    if evalfile is None:
        print "please provide an eval file!"
        sys.exit(0)


    if experimentfile is None and testrunfiles == []:
        print "please provide either a experimentfile or (multiple, if needed) .trn testrun files"
        sys.exit(0)
    theeval = IPETEvaluation.fromXMLFile(evalfile)

    if nooptauto:
        theeval.setEvaluateOptAuto(False)
    else:
        theeval.setEvaluateOptAuto(True)
    if experimentfile is not None:
        experiment = Experiment.loadFromFile(experimentfile)
    else:
        experiment = Experiment()

    for trfile in testrunfiles:
        experiment.addOutputFile(trfile)

    if recollect is not False:
        print "Recollecting data"
        experiment.collectData()

    if saveexperiment is not False:
        experiment.saveToFile(experimentfile)

    if defaultgroup is not None:
        theeval.setDefaultGroup(defaultgroup)

    if groupkey is not None:
        theeval.setGroupKey(groupkey)

    if externaldata is not None:
        experiment.addExternalDataFile(externaldata)
    else:
        experiment.externaldata = None

    if compformatstring is not None:
        theeval.setCompareColFormat(compformatstring)

    if keysearch is not None:
        print "Starting key enumeration"
        for key in experiment.getDatakeys():
            if re.search(keysearch, key):
                print "    " + key
        print "End key enumeration"
        exit(0)

    if showapp:
        application = QApplication(sys.argv)
        application.setApplicationName("Evaluation editor")
        mainwindow = IpetEvaluationEditorApp()
        try:
            mainwindow.setEvaluation(theeval)
        except:
            pass
        mainwindow.setExperiment(experiment)
        mainwindow.show()

        sys.exit(application.exec_())

    rettab, retagg = theeval.evaluate(experiment)


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

        filename = "%s/%s"%(path, "_".join((prefixstr, "inst_combined")) if prefixstr != "" else "inst_combined")
        theeval.streamDataFrame(rettab, filename, extension)
        print "combined instance data written to %s.%s"%(filename,extension)
        # print the combined aggregated data if there are multiple filter groups present
        filename = "%s/%s"%(path, "_".join((prefixstr, "agg_combined")) if prefixstr != "" else "agg_combined")
        theeval.streamDataFrame(retagg, filename, extension)
        print "combined aggregated data written to %s.%s"%(filename,extension)

    #print pd.concat([rettab, theeval.levelonedf], axis=1)

