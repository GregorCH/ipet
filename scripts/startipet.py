'''
Created on 02.08.2014

@author: Gregor Hendel
'''
from ipet.gui import IpetApplication
from ipet import Experiment
import argparse
import sys
import re

# possible arguments in the form name,default,short,description #
clarguments = [('--experimentfile', None, '-e', "An experiment file name (must have .cmp file extension) in cmp-format to read")]

argparser = argparse.ArgumentParser(prog="Ipet Startup Script", \
                                 description="starts the IPET graphical user interface")
for name, default, short, description in clarguments:
    argparser.add_argument(short, name, default=default,help=description)




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
    if experimentfile is not None:
        try:
            experiment = Experiment.loadFromFile(experimentfile)
        except NameError:
            pass

    gui = IpetApplication(experiment)
    gui.mainloop()
