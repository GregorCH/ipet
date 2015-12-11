'''
Created on 24.02.2015

@author: bzfhende
'''

import argparse
import sys
import pandas as pd
from ipet.IPETPlotWindow import IPETPlotFrame
from Tkinter import Tk
from numpy import log
import re

# possible arguments in the form name,default,short,description #
clarguments = [('--filename', None,'-f', "A csv file with the data"),
               ('--leftbin', -10,'-l', "Leftmost boundary of bins, only used when 'boundsfromdata' is set to False"),
               ('--rightbin', 10,'-r', "Rightmost boundary of bins, only used when 'boundsfromdata' is set to False"),
               ('--boundsfromdata',True, '-b', "True if left and right bin border should be inferred from the data, False if leftbin and rightbin should be used"),
               ('--binwidth',1, '-w', "the width of every bin. Only used when 'nbins' is smaller than 0"),
               ('--nbins',10, '-n', "the total number of bins. Use a negative value for calculating the bins from bin width instead"),
               ('--columnname',None, '-c', "column name, e.g. 'SolvingTime', from which all suitable columns are inferred"),
               ('--logarithmic',False, '-L', "should the data be transformed on a logarithmic scale first? ")
               ]
argparser = argparse.ArgumentParser(prog="Ipet Histogram Plot Script", \
                                 description="plots a histogram of the specified data from a csv file")
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

    #initialize a comparator
    if filename is None or not filename.endswith(".csv"):
        print "please provide a csv file as filename!"
        sys.exit(0)

    if columnname is None:
        print "please provide a column name!"
        sys.exit(0)

    df = pd.DataFrame.from_csv(filename, sep=",",header=[0,1])

    leftbin = float(leftbin)
    rightbin = float(rightbin)
    if boundsfromdata in ["True", True]:
        boundsfromdata = True
    else:
        boundsfromdata = False
    if logarithmic in ["True", True]:
        logarithmic = True
    else:
        logarithmic = False
    binwidth = float(binwidth)
    nbins = int(nbins)

    # query the data frame for the desired column on first level
    data = df.xs(columnname, level=1, axis=1).dropna()


    datavals = [data[col].values for col in data]
    if logarithmic:
        datavals = [log(col) for col in datavals]

    datalabels = [col for col in data]

    root = Tk()
    root.wm_title("Histogram for %s %s"%(str(columnname), logarithmic and " on logarithmic scale" or ""))
    pw = IPETPlotFrame(master=root)
    pw.plothistogram(datavals, boundsfromdata, binwidth, leftbin, rightbin, nbins, datalabels)

    pw.pack()
    root.mainloop()