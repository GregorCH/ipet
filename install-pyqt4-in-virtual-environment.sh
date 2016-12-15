#! /usr/bin/bash

# this script is an attempt to automate the installation
# of PyQt4 into a virtual environment
# 
# The graphical user interface of IPET is based on PyQt4,
# Run without arguments from the IPET root directory
#
# If you have super user permissions on your machine, you may want to 
# use 
#
# sudo apt-get install python3-pyqt4 
#
# to achieve something similar to this script.
# 
# This script will only run under linux

#!/bin/bash
#
# The MIT License (MIT)
# 
# Copyright (c) 2016 Zuse Institute Berlin, www.zib.de
# 
# Permissions are granted as stated in the license file you have obtained
# with this software. If you find the library useful for your purpose,
# please refer to README.md for how to cite IPET.
# 
# @author: Gregor Hendel
#
VIRTUALENV=venv


if test -n "$1"
then
    VIRTUALENV=$1
fi
if ! test -d "$VIRTUALENV"
then
    echo Specified virtual environment \"${VIRTUALENV}\" does not exist. Exiting
    exit 1
fi

DOWNLOADDIR=${VIRTUALENV}/download
SIP=sip-4.18.1
PYQT4_VERSION=4.11.4

function wgetCommand {
    TARGET=$1
    wget $1 -P $DOWNLOADDIR --no-clobber
    
    # exit script if the command failed
    if test "$?" != 0
    then
        echo Could not download the target $TARGET, please download manually
        exit 1
    fi
}

test -d $VIRTUALENV || test -L $VIRTUALENV || \
(echo "Could not find assumed virtual environment '$VIRTUALENV'" && \
echo "Please modify the variable VIRTUALENV in this script to point" && \
echo "to the virtual environment you are using")
test -d $VIRTUALENV || test -L $VIRTUALENV || exit 1


echo "Downloading sip to $DOWNLOADDIR"
wgetCommand https://sourceforge.net/projects/pyqt/files/sip/${SIP}/${SIP}.tar.gz

echo "Downloading pyQt4 to $DOWNLOADDIR"
wgetCommand https://sourceforge.net/projects/pyqt/files/PyQt4/PyQt-${PYQT4_VERSION}/PyQt-x11-gpl-${PYQT4_VERSION}.tar.gz

# untar both libraries
for t in ${SIP}.tar.gz PyQt-x11-gpl-${PYQT4_VERSION}.tar.gz
do
    cd $DOWNLOADDIR; tar xzf $t; cd -
done

# create a local include directory for the sip configuration
mkdir -p ${VIRTUALENV}/local/include

echo configure and install sip
cd $DOWNLOADDIR/${SIP}
# if the virtual environment was not created with --always-copy,
# it symlinks to inclusion headers, e.g. /usr/include/python-x.x
# make install will then break if we do not specify the directory
# where the header 'sip.h' should go
python configure.py -e ${VIRTUALENV}/local/include
make; make install
cd -

echo configure and install PyQt-$PYQT4_VERSION, might take a while
cd $DOWNLOADDIR/PyQt-x11-gpl-${PYQT4_VERSION}
python configure.py
make; make install
cd -

echo test the installation
OUTPUT=`python -c "from PyQt4 import QtCore,QtGui"`
if test "$OUTPUT" = ""
then
    echo PyQt successfully installed
else
    echo PyQt installation was not successful
    echo Running 'python -c "from PyQt4 import QtCore,QtGui"' returned
    echo $OUTPUT
fi



