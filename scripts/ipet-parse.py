'''
The MIT License (MIT)

Copyright (c) 2016 Zuse Institute Berlin, www.zib.de

Permissions are granted as stated in the license file you have obtained
with this software. If you find the library useful for your purpose,
please refer to README.md for how to cite IPET.

@author: Gregor Hendel
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
    argparser.add_argument(short, name, default = default, help = description)

argparser.add_argument('-l', '--logfiles', nargs = '*', help = "list of outfiles that should be parsed")
argparser.add_argument('-r', '--readers', nargs = '*', default = [], help = "list of additional readers in xml format that should be used for parsing")
argparser.add_argument('-s', '--solufiles', nargs = '*', default = [], help = "list of solu files that should be taken into account")
argparser.add_argument("-D", "--debug", action = "store_true", default = False, help = "Enable debug output to console during parsing")


if __name__ == '__main__':
    try:
        arguments = argparser.parse_args()
    except:
        if not re.search(" -+h", ' '.join(sys.argv)) :
            print("Wrong Usage, use --help for more information.")
        exit()
    # if globals().get("help") is not None:
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

    if arguments.readers == []:
        readers = []
        for _file in os.listdir('./'):
            if _file.endswith(".xml") or _file.endswith(".ipr"):
                try:
                    rm = ReaderManager.fromXMLFile(_file)
                    readers.append(_file)
                except:
                    pass
        logging.info("No additional readers specified. Found following %d reader files (.ipr, .xml) in directory: [%s]", len(readers), ", ".join(readers))
    else:
        readers = arguments.readers

    for additionalfile in readers:
        rm = ReaderManager.fromXMLFile(additionalfile)
        for reader in rm.getManageables():
            experiment.readermanager.registerReader(reader)
            logging.info("Registered reader with name %s" % reader.getName())

    for logfile in arguments.logfiles:
        experiment.addOutputFile(logfile)
        
    # search for solu files in current directory
    if arguments.solufiles == []:
        solufiles = [_file for _file in os.listdir("./") if _file.endswith(".solu")]
        logging.info("No '.solu'-files specified. Found %d .solu files in directory: %s", len(solufiles), ", ".join(solufiles))
    else:
        solufiles = arguments.solufiles

    for solufile in solufiles:
        experiment.addSoluFile(solufile)

    logging.info("Start parsing process")
    experiment.collectData()

    for tr in experiment.getTestRuns():
        try:
            filename = tr.filenames[0]
            newfilename = "%s%s" % (os.path.splitext(filename)[0], TestRun.FILE_EXTENSION)
            tr.saveToFile(newfilename)
            logging.info("converted %s --> %s" % (filename, newfilename))
        except:
            logging.info("skipped testrun %s" % tr.getIdentification())

