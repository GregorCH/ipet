'''
Created on 24.02.2015

@author: bzfhende
'''

from ipet.Experiment import Experiment
from ipet.parsing.ReaderManager import ReaderManager
from ipet.TestRun import TestRun
import argparse
import sys
import os
import re
import logging

# possible arguments in the form name,default,short,description #
clarguments = []

argparser = argparse.ArgumentParser(prog="Ipet Startup Script", \
                                 description="starts the IPET graphical user interface")
for name, default, short, description in clarguments:
    argparser.add_argument(short, name, default=default,help=description)

argparser.add_argument('outfiles', nargs='*', help="list of outfiles that should be parsed")
argparser.add_argument('-r','--readers', nargs='*', default=[], help="list of additional readers in xml format that should be used for parsing")
argparser.add_argument('-s','--solufiles', nargs='*', default=[], help="list of solu files that should be taken into account")
argparser.add_argument("-D", "--debug", action = "store_true", default = False, help = "Enable debug output to console during parsing")


if __name__ == '__main__':
    try:
        n = vars(argparser.parse_args())
        globals().update(n)
    except:
        if not re.search(" -+h", ' '.join(sys.argv)) :
            print "Wrong Usage, use --help for more information."
        exit()
    #if globals().get("help") is not None:
    print globals()
    if outfiles is None:
        print "We need out files"
        sys.exit(0)


    # initialize an experiment
    experiment = Experiment()

    if debug:
        logger = logging.getLogger()
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        logger.setLevel(logging.DEBUG)
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        logger.addHandler(ch)

    for additionalfile in readers:
        rm = ReaderManager.fromXMLFile(additionalfile)
        for reader in rm.getManageables(False):
            experiment.readermanager.registerReader(reader)

    for outfile in outfiles:
        experiment.addOutputFile(outfile)

    for solufile in solufiles:
        experiment.addSoluFile(solufile)

    experiment.collectData()

    for tr in experiment.testrunmanager.getManageables():
        try:
            filename = tr.filenames[0]
            newfilename = "%s%s"%(os.path.splitext(filename)[0], TestRun.FILE_EXTENSION)
            tr.saveToFile(newfilename)
            print "converted %s --> %s"%(filename, newfilename)
        except:
            print "skipped testrun %s"%tr.getIdentification()

