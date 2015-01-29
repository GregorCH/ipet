'''
Created on 02.08.2014

@author: Gregor Hendel
'''
from ipet.IpetApplication import IpetApplication
from ipet.Comparator import Comparator
import argparse
import sys

# possible arguments in the form name,default,short,description #
clarguments = [('--comparatorfile', None,'-c', "A comparator file name (must have .cmp file extension) in cmp-format to read")]

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
    if comparatorfile is not None:
        try:
            comparator = Comparator.loadFromFile(comparatorfile)
        except NameError:
            pass

    gui = IpetApplication(comparator)
    gui.mainloop()
