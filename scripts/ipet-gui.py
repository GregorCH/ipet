'''
The MIT License (MIT)

Copyright (c) 2016 Zuse Institute Berlin, www.zib.de

Permissions are granted as stated in the license file you have obtained
with this software. If you find the library useful for your purpose,
please refer to README.md for how to cite IPET.

@author: Gregor Hendel
'''
from ipetgui import QIPETApplication
from PyQt4.Qt import QApplication
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
            print("Wrong Usage, use --help for more information.")
        exit()
    #if globals().get("help") is not None:

    # initialize a experiment
    experiment = None
    if experimentfile is not None:
        try:
            experiment = Experiment.loadFromFile(experimentfile)
        except NameError:
            pass

    app = QApplication(sys.argv)
    qipetapplication = QIPETApplication()
    qipetapplication.setWindowTitle("IPET 2.0")

    app.setApplicationName("IPET 2.0")

    qipetapplication.show()

    sys.exit(app.exec_())
