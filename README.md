IPET (Interactive Performance Evaluation Tools) is a toolbox that
allows to easily create customized benchmark tables from
raw solver log files, written in Python 3. 

It is aimed to develop evaluations through a
grapical interface that can later be loaded and reused on other
data. Additional readers and evaluations are stored in
xml-format which can be plugged into the evaluation method.

# How to get IPET

In the following installation instructions, we will assume that you clone the IPET repository by

    git clone https://github.com/GregorCH/ipet.git

or download and unzip one of the available zipped archieves into a local directory called "ipet".

It is planned to make ipet available via the Python package indexer PyPi.

# Installation and prerequisites

IPET was originally written in Python2.7 and recently converted into Python3.
It consists of two modules, *ipet* together with several submodules, and *ipetgui*.
The use of the graphical user interface requires that the PyQt4 bindings for
Python3 are available on your system.
We give installation instructions for the Linux operating system. Since the code is
written in python only, it should also work on other platforms. We assume that you either
have sudo-privileges on your target architecture, or are able to create a python3
virtual environment. You can test if virtual environments are available by running the command

    virtualenv --python python3 myvenv
    rm -r myvenv # remove the created directory

If your target system does not provide virtual environments, please contact your system administrator
before you continue.

Running the graphical user interface of IPET requires PyQt4 for python3. In order to test if
your system has PyQt4, execute

    python3 -c "from PyQt4 import QtCore,QtGui; print(\"PyQt4 is ready\")"

We provide a script called "install-pyqt4-in-virtual-environment.sh" to install PyQt4-bindings inside a virtual environment.

## Linux installation inside a virtual environment

Using a virtual environment, you can safely install the required packages together without 
messing with your globally installed system libraries. This is certainly the recommended way
to install IPET. In the following, we assume you create the root directory of your virtual 
environment directly in the IPET root directory and call it "venv". You may choose
to use a differently named virtual environment somewhere else, of course.

1. Create and activate the virtual environment (a new directory called "venv" gets created):

        cd ipet
        virtualenv --python python3 venv
        source venv/bin/activate
   Note that you may deactivate the virtual environment at any time by calling 
        
        deactivate
    
2. Install PyQt4 bindings inside your virtual environment by calling the provided script, 
which assumes that you are running inside the virtual environment "venv" or the one specified by the optional path. 
The script will ask you to carefully read and accept the license agreement for using PyQt4 bindings.

        ./install-pyqt4-in-virtual-environment.sh [optional path to virtual environment root]

3. Execute the command (note that it does no longer require to mention python3 because we are running inside the virtual environment)

        pip install -r requirements.txt
        python setup.py install

4. As a developer, it might be useful to call the following command instead:

        python setup.py develop
   This creates symlinks to the IPET source files in the site-packages of the virtual environment library,
   and allows for more rapid testing and development.



## Linux installation into your *global* environment

If you would like to install *IPET* systemwide, all you need to do is

    cd ipet
    python3 setup.py install --user
    
or

    cd ipet
    sudo python3 setup.py install
    
This step makes imports available systemwide such as 

    python3 -c "from ipet import *"

The installation process will recognize if you have PyQt4 bindings available on your system, which are necessary to
use the graphical user interface.




## Testing your installation

Run the command 
    
    python -m unittest test
 if the output says OK, all tests were passed.






# Getting Started on the command line

IPET has a subdirectory called "scripts" with scripts to invoke log file parsing, test run evaluating, and starting 
the graphical user interface.

**under construction**






# The concept of IPET

**under construction**




