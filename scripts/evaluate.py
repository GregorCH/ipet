'''
Created on 24.02.2015

@author: bzfhende
'''

from ipet.IpetApplication import IpetApplication
from ipet.Comparator import Comparator
import argparse
import sys
from ipet.IPETEvalTable import IPETEvaluation
import pandas as pd

# possible arguments in the form name,default,short,description #
clarguments = [('--comparatorfile', None,'-c', "A comparator file name (must have .cmp file extension) in cmp-format to read"),
               ('--evalfile', None,'-e', "An evaluation file name (must have .xml file extension) in xml-format to read"),
               ('--recollect', False,'-r', "Should the loaded comparator recollect data before proceeding?"),
               ('--savecomparator', False,'-s', "Should the comparator data be overwritten? Makes only sense if combined with '--recollect True'")]

argparser = argparse.ArgumentParser(prog="Ipet Startup Script", \
                                 description="starts the IPET graphical user interface")
for name, default, short, description in clarguments:
    argparser.add_argument(short, name, default=default,help=description)

argparser.add_argument('-t', '--testrunfiles', nargs='*', default=[], help="list of .trn files that should used for the evaluation")


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


    rettab, retagg = theeval.evaluate(comp)

    print pd.concat([rettab, theeval.levelonedf], axis=1)

    print rettab.to_string()
    print
    print retagg.to_string()
