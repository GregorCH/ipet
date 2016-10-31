'''
Created on 24.02.2015

@author: bzfhende
'''

from ipet import Experiment
from ipet.parsing import ReaderManager
from ipet import TestRun
import argparse
import sys
import os
import re
import logging

# possible arguments in the form name,default,short,description #
clarguments = []

argparser = argparse.ArgumentParser(prog = "Ipet Parsing script", \
                                 description = "parses test run log files and saves parsed data")
for name, default, short, description in clarguments:
    argparser.add_argument(short, name, default=default,help=description)

argparser.add_argument('-l','--logfiles', nargs='*', help="list of outfiles that should be parsed")
argparser.add_argument('-r','--readers', nargs='*', default=[], help="list of additional readers in xml format that should be used for parsing")
argparser.add_argument('-s','--solufiles', nargs='*', default=[], help="list of solu files that should be taken into account")
argparser.add_argument("-D", "--debug", action = "store_true", default = False, help = "Enable debug output to console during parsing")


if __name__ == '__main__':
    try:
        arguments = argparser.parse_args()
    except:
        if not re.search(" -+h", ' '.join(sys.argv)) :
            print "Wrong Usage, use --help for more information."
        exit()
    #if globals().get("help") is not None:
    logger = logging.getLogger()
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    if arguments.debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    if arguments.logfiles is None:
        logging.info("No testruns specified, exiting")
        sys.exit(0)


    # initialize an experiment
    experiment = Experiment()


    for additionalfile in arguments.readers:
        rm = ReaderManager.fromXMLFile(additionalfile)
        for reader in rm.getManageables():
            experiment.readermanager.registerReader(reader)
            logging.info("Registered reader with name %s" % reader.getName())

    for logfile in arguments.logfiles:
        experiment.addOutputFile(logfile)

    for solufile in arguments.solufiles:
        experiment.addSoluFile(solufile)

    logging.info("Start parsing process")
    experiment.collectData()

    for tr in experiment.testrunmanager.getManageables():
        try:
            filename = tr.filenames[0]
            newfilename = "%s%s"%(os.path.splitext(filename)[0], TestRun.FILE_EXTENSION)
            tr.saveToFile(newfilename)
            logging.info("converted %s --> %s" % (filename, newfilename))
        except:
            logging.info("skipped testrun %s" % tr.getIdentification())

