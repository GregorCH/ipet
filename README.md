IPET (Interactive Performance Evaluation Tools) is a toolbox that
allows to easily create customized benchmark tables from
raw solver log files, written in Python 3. 

It is aimed to develop evaluations through a
grapical interface that can later be loaded and reused on other
data. Additional readers and evaluations are stored in
xml-format which can be plugged into the evaluation method.

Here are some usage examples


How to get IPET
---------------

The most recent source code can be obtained by cloning from the following url

    https://git.zib.de/integer/ipet/repository/archive.tar.gz
    
In the future, we will support the download of older versions of IPET.




Installation and prerequisites
------------------------------

IPET was originally written in Python2.7 and recently converted into Python3.
It consists of two modules, *ipet* together with several submodules, and *ipetgui*.
The use of the graphical user interface requires that the PyQt4 bindings for
Python3 are available on your system. Assuming that the PyQt4 bindings are available,
all you have to do is

    
    cd ipet; sudo python setup.py install





Getting Started on the command line
-----------------------------------




The concept of IPET
-------------------



