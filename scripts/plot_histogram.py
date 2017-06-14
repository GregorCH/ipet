"""
The MIT License (MIT)

Copyright (c) 2016 Zuse Institute Berlin, www.zib.de

Permissions are granted as stated in the license file you have obtained
with this software. If you find the library useful for your purpose,
please refer to README.md for how to cite IPET.

@author: Gregor Hendel
"""

import argparse
import sys
import pandas as pd
from ipet.IPETPlotWindow import IPETPlotFrame
from tkinter import Tk
from numpy import log, log2, log10
import re

# possible arguments in the form name,default,short,description #
clarguments = [('--filename', None,'-f', "A csv file with the data"),
               ('--leftbin', -10,'-l', "Leftmost boundary of bins, only used when 'boundsfromdata' is set to False"),
               ('--rightbin', 10,'-r', "Rightmost boundary of bins, only used when 'boundsfromdata' is set to False"),
               ('--boundsfromdata',True, '-b', "True if left and right bin border should be inferred from the data, False if leftbin and rightbin should be used"),
               ('--binwidth',1, '-w', "the width of every bin. Only used when 'nbins' is smaller than 0"),
               ('--nbins',10, '-n', "the total number of bins. Use a negative value for calculating the bins from bin width instead"),
               ('--columnname',None, '-c', "column name, e.g. 'SolvingTime', from which all suitable columns are inferred"),
               ('--logarithmic', None, '-L', "basis for logarithmic data transformation (use 2, e, or 10)"),
               ('--title', None, '-T', "A custom title for this plot")
               ]
argparser = argparse.ArgumentParser(prog="Ipet Histogram Plot Script", \
                                 description="plots a histogram of the specified data from a csv file")
for name, default, short, description in clarguments:
    argparser.add_argument(short, name, default=default,help=description)

argparser.add_argument("-D", "--legend", action = "store_true", default = False, help = "should a legend be shown?")
argparser.add_argument("-e", "--epsilon", type = float, default = 1e-6, help = "epsilon threshold for data point absolute value")



if __name__ == '__main__':
    try:
        arguments = argparser.parse_args()
    except:
        if not re.search(" -+h", ' '.join(sys.argv)) :
            print("Wrong Usage, use --help for more information.")
        exit()
    #if globals().get("help") is not None:

    #initialize a comparator
    if arguments.filename is None or not arguments.filename.endswith(".csv"):
        print("please provide a csv file as filename!")
        sys.exit(0)

    if arguments.columnname is None:
        print("please provide a column name!")
        sys.exit(0)

    df = pd.DataFrame.from_csv(arguments.filename, sep = ",", header = [0, 1])

    leftbin = float(arguments.leftbin)
    rightbin = float(arguments.rightbin)
    if arguments.boundsfromdata in ["True", True]:
        boundsfromdata = True
    else:
        boundsfromdata = False
    if arguments.logarithmic:
        logarithmic = arguments.logarithmic
        if logarithmic == "2":
            logfunction = log2
        elif logarithmic == "e":
            logfunction = log
        elif logarithmic == "10":
            logfunction = log10
        else:
            print("Wrong logarithm basis %s, must be in [2, e, 10]" % logarithmic)
            sys.exit(0)
    else:
        logarithmic = False
    binwidth = float(arguments.binwidth)
    nbins = int(arguments.nbins)

    # query the data frame for the desired column on first level
    data = df.xs(arguments.columnname, level = 1, axis = 1).dropna()

    # apply a logarithmic transformation
    if logarithmic:
        data = data.apply(logfunction)

    # filter absolute values smaller than epsilon / too close to zero
    if arguments.epsilon >= 0.0:
        data = data[data.abs() >= arguments.epsilon]

    # determine labels and values for the histogram. Note that columns may be dropped if they became empty after filtering
    datalabels, datavals = list(zip(*[(col, data[col].dropna().values) for col in data if len(data[col].dropna()) > 0]))

    removedcolumns = [col for col in data.columns if not col in datalabels]
    if removedcolumns:
        print("Columns <%s> filtered out" % ", ".join(removedcolumns))



    root = Tk()

    # give the window a nice title
    if arguments.title:
        root.wm_title(arguments.title)
    else:
        root.wm_title("Histogram for %s %s" % (str(arguments.columnname), logarithmic and " on logarithmic scale base %s" % logarithmic or ""))

    pw = IPETPlotFrame(master=root)
    pw.plothistogram(datavals, boundsfromdata, binwidth, leftbin, rightbin, nbins, datalabels)

    # plot the legend
    if arguments.legend:
        pw.showLegend()

    pw.pack()
    root.mainloop()
