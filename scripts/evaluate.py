'''
Created on 24.02.2015

@author: bzfhende
'''

from ipet.IpetApplication import IpetApplication
from ipet.Comparator import Comparator
import argparse
import sys
from ipet.IPETEvalTable import IPETEvaluation

# possible arguments in the form name,default,short,description #
clarguments = [('--comparatorfile', None,'-c', "A comparator file name (must have .cmp file extension) in cmp-format to read"),
               ('--evalfile', None,'-e', "An evaluation file name (must have .xml file extension) in xml-format to read"),
               ('--recollect', False,'-r', "Should the loaded comparator recollect data before proceeding?")]

argparser = argparse.ArgumentParser(prog="Ipet Startup Script", \
                                 description="starts the IPET graphical user interface")
for name, default, short, description in clarguments:
    argparser.add_argument(short, name, default=default,help=description)




if __name__ == '__main__':
    try:
        n = vars(argparser.parse_args())
        globals().update(n)
    except:
        print "Wrong Usage"
    #if globals().get("help") is not None:

    #initialize a comparator
    comparator = None
    if evalfile is None or comparatorfile is None:
        print "please provide an eval and a comparator file!"
        sys.exit(0)


    eval = IPETEvaluation.fromXMLFile(evalfile)
    comp = Comparator.loadFromFile(comparatorfile)

    if recollect is not False:
        print "Recollecting data"
        comp.collectData()

    rettab, retagg = eval.evaluate(comp)

    print rettab.to_string()
    print
    print retagg.to_string()