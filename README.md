# IPET (Interactive Performance Evaluation Tools) 

IPET is a toolbox that allows to easily create customized benchmark tables from
raw solver log files, written in Python 3.

It is aimed to develop evaluations through a
grapical interface that can later be loaded and reused on other
data. Additional readers and evaluations are stored in
xml-format which can be plugged into the evaluation method.

If you find IPET useful for your work, it would be nice if you
cite it using the following bibtex item:

```
@Misc{ipet,
  Title                    = {{IPET} Interactive Performance Evaluation Tools},
  Author                   = {Gregor Hendel},
  HowPublished             = {\url{https://github.com/GregorCH/ipet}}
}
```

# Table of contents

- [How to get IPET](#how-to-get-ipet)
- [Installation and prerequisites](#installation-and-prerequisites)
  * [Linux installation inside a virtual environment](#linux-installation-inside-a-virtual-environment)
  * [Linux installation into your global environment](#linux-installation-into-your-global-environment)
  * [Testing your installation](#testing-your-installation)
- [Usage and concept](#usage-and-concept)
  * [Overview](#overview)
  * [Basic usage on the command line](#basic-usage-on-the-command-line)
  * [Tutorial for parsing results obtained with SCIP](#tutorial-for-parsing-results-obtained-with-scip)
  * [Configuration](#configuration)
  * [Starting the graphical user interface](#starting-the-graphical-user-interface)
- [Building the documentation](#building-the-documentation)

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

*This is the recommended kind of installation.*

Using a virtual environment, you can safely install the required packages together without
messing with your globally installed system libraries. This is certainly the recommended way
to install *IPET*. In the following, we assume you create the root directory of your virtual
environment directly in the IPET root directory and call it "venv". You may choose
to use a differently named virtual environment somewhere else, of course.

1. Create and activate the virtual environment (a new directory called "venv" gets created):

        cd ipet
        virtualenv --python python3 venv
        source venv/bin/activate
        
   Note that you may deactivate the virtual environment at any time by calling

        deactivate

2. (*optional* step to install the graphical user interface, for command line only skip to next step) 
Install PyQt4 bindings inside your virtual environment by calling the provided script,
which assumes that you are running inside the virtual environment "venv" or the one specified by the optional path.
The script will ask you to carefully read and accept the license agreement for using PyQt4 bindings.

        ./install-pyqt4-in-virtual-environment.sh [optional path to virtual environment root]

3. Execute the command (note that it does no longer require to mention python3 because we are running inside the virtual environment)

        pip install .

4. As a developer, it might be useful to call the following command instead:

        pip install -e .
        
   This creates symlinks to the IPET source files in the site-packages of the virtual environment library,
   and allows for more rapid testing and development.

## Linux installation into your global environment

[We highly recommend to install IPET into a virtual environment.](#linux-installation-inside-a-virtual-environment)

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

# Usage and concept

**under construction**

## Overview 
 
IPET takes a logfile and some optional additional files like an error-, set- and metafile, extracts information and aggregates this data in a compact table.
The Logfiles need to have an `.out` extension, errorfiles need to have `.err`, setfiles are `.set` and metafiles are `.meta`

The process is divided in two stages:

1) `ipet-parse`, which performs the parsing, where the standard data is extracted and stored in a .trn file.
2) `ipet-evaluate`, where the data is aggregated and displayed in two tables by user-defined rules. The *aggregated table* displays the information that was condensed from the *long table*.

For more information, please refer to the [Basic usage](#basic-usage-on-the-command-line) section and the help pages, that can be displayed with `ipet-parse --help` and `ipet-evaluate --help`.
It is possible to configure ipet for your own solver and testset, please check the [Configuration](#configuration) section.

## Basic usage on the command line

IPET is easily used on the command line. Assume you have a logfile `testrun.out` that contains the output of running the solver on a list of instances. 
The output of each run is preceded by a line indicating the instance and preceded by a line indicating correct shutdown of the solver. 
In other words your format is the following:

        @01 /path/to/my/first_instance.clp
        <Output of solver for aforementioned instance>
        =ready=
        @01 /path/to/my/second_instance.mpz
        <Output of solver for aforementioned instance>
        =ready=
        ...
        =ready=
        @01 /path/to/my/last_instance.clp
        <Output of solver for aforementioned instance>
        =ready=
        
Now you call the parsing command with the logfile, which will create a `testrun.trn` file storing the parsed data.

        ipet-parse -l testrun.out
        
In the second step you call the evaluation command with this `testrun.trn` file and an evaluation file that encodes the datakey and aggregation functions for your table. 
There is an example in `scripts/evaluation.xml`.
Calling `ipet-evaluate` will display the aggregated table only:

        ipet-evaluate -e scripts/evaluation.xml -t testrun.trn

If you are interesting in the considered values that result in this table you can have a look at the long table with the `--long` or `-l` option:

        ipet-evaluate -e scripts/evaluation.xml -t testrun.trn --long

## Tutorial for parsing results obtained with SCIP

Say that you used SCIP to solve a number of instances and would like to get the solving time, number of nodes used and the status of the solver for each instance. This short tutorial will show you how to do that with ipet. As an input, it is assumed that you have the output of scip in a separate file for each instance in the folder `SCIP_OUT_FILES`.

### Step 1
A helper script scripts/concat.sh is available that can preprocess single output files and create a concatenated logfile in the format that is needed by ipet. As input it takes the folder containing your logfiles:
```
$ cd scripts
$ ./concat.sh -f SCIP_OUT_FILES
Concatenated logs from folder '../SCIP_OUT_FILES' into '../SCIP_OUT_FILES/concatenated.out'.
```

### Step 2
We can now parse the results by calling the ipet-parse command with the concatenated logfile:
```
$ ipet-parse -l SCIP_OUT_FILES/concatenated.out
2021-07-01 14:49:50,530 -    INFO - root - Start parsing process using 8 threads
  0%|                                                                                    | 0/1 [00:00<?, ?it/s]2021-07-01 14:49:50,532 -    INFO - root - Start parsing process of outfile(s) SCIP_OUT_FILES/concatenated.out
2021-07-01 14:49:50,983 -    INFO - root - converted /home/boro/repo/ipet/SCIP_OUT_FILES/concatenated.out --> /home/boro/repo/ipet/SCIP_OUT_FILES/concatenated.trn
100%|████████████████████████████████████████████████████████████████████████████| 1/1 [00:00<00:00,  2.21it/s]
```

### Step 3
Calling ipet-evaluate now with the resulting .trn file and the example evaluation file scipts/evaluation.xml will display our data in a table:
```
$ ipet-evaluate -t SCIP_OUT_FILES/concatenated.trn -e scripts/evaluation.xml --long
2021-07-01 14:52:32,903 -    INFO - root - No external data file
2021-07-01 14:52:32,949 -    INFO - ipet.evaluation.IPETEvalTable - Automatically set index to (['ProblemName'], [])
2021-07-01 14:52:32,949 -    INFO - ipet.evaluation.IPETEvalTable - No validation information specified
2021-07-01 14:52:32,949 -    INFO - ipet.validation.Validation - Validating with a (gap) tolerance of 0.0001 and a feasibility tolerance of 1e-06.
2021-07-01 14:52:32,982 -    INFO - ipet.evaluation.IPETEvalTable - Validation resulted in the following status codes: [ fail_inconsistent: 59 | ok: 2 ]
2021-07-01 14:52:33,149 -    INFO - ipet.evaluation.IPETFilter - Computing rows for intersection groups
2021-07-01 14:52:33,213 - WARNING - ipet.evaluation.IPETEvalTable - Filtergroup diff-timeouts is empty and has been deactived.
Instancewise Results:
                 Time  Nodes             Status
ProblemName                                    
31966239     36004.22      1  fail_inconsistent
31966240     36007.75      1  fail_inconsistent
31966241     36012.76      1  fail_inconsistent
31966242     36001.43      1  fail_inconsistent
31966243     36008.84      1  fail_inconsistent
31966244     36029.03      1  fail_inconsistent
31966245     36002.47      1  fail_inconsistent
31966246     36015.92      1  fail_inconsistent
31966247     36005.92      1  fail_inconsistent
31966248     36013.47      1  fail_inconsistent
31966249     36004.72      1  fail_inconsistent
31966250     36010.12      1  fail_inconsistent
31966251     36016.95      1  fail_inconsistent
31966252     36000.58      1  fail_inconsistent
31966253     36021.44      1  fail_inconsistent
31966254     36010.16      1  fail_inconsistent
31966255     36015.02      1  fail_inconsistent
31966256     36000.52      1  fail_inconsistent
31966257     36025.40      1  fail_inconsistent
31966258     36012.98      1  fail_inconsistent
31966259     36002.78      1  fail_inconsistent
31966260     36007.17      1  fail_inconsistent
31966261     36000.00      1  fail_inconsistent
31966262     36000.67      1  fail_inconsistent
31966263     36002.23      1  fail_inconsistent
31966264     36011.77      1  fail_inconsistent
31966265     36001.57      1  fail_inconsistent
31966266     36002.57      1  fail_inconsistent
31966267     36000.01      1  fail_inconsistent
31966268     36000.20      1  fail_inconsistent
31966269     36000.01      1  fail_inconsistent
31966270     36000.01      1  fail_inconsistent
31966271     36000.01      1  fail_inconsistent
31966272     36000.00      1  fail_inconsistent
31966273     36000.01      1  fail_inconsistent
31966274     36000.27      1  fail_inconsistent
31966275     36000.01      1  fail_inconsistent
31966276     36000.01      1  fail_inconsistent
31966277     36000.01      1  fail_inconsistent
31966278     36000.01      1  fail_inconsistent
31966279     36000.04      1  fail_inconsistent
31966280     36000.01      1  fail_inconsistent
31966281     36000.01      1  fail_inconsistent
31966282     36017.63      1  fail_inconsistent
31966283     36000.01      1  fail_inconsistent
31966284     36011.14      1  fail_inconsistent
31966285     36000.01      1  fail_inconsistent
31966286     36005.53      1  fail_inconsistent
31966287     36000.01      1  fail_inconsistent
31966288     36012.31      1  fail_inconsistent
31966289     36008.58      1  fail_inconsistent
31966290     36013.95      1  fail_inconsistent
31966291     36009.99      1  fail_inconsistent
31966292     36001.28      1  fail_inconsistent
31966293     36000.01      1  fail_inconsistent
31966294     36013.66      1  fail_inconsistent
31966295     36000.02      1  fail_inconsistent
31966296     36010.50      1  fail_inconsistent
31966297     36000.02      1  fail_inconsistent
31966298         2.53      1                 ok
31966299         2.54      1                 ok
Aggregated Results:
              _time_ _limit_ _primfail_ _dualfail_ _fail_ _abort_ _solved_ _unkn_ _count_ _miss_  Time_shmean(1.0)  Nodes_shmean(100.0)
Group                                                                                                                                  
all                0       0          0          0     59       0        2      0      61      0      26604.848145                  1.0
alloptimal         0       0          0          0      0       0        2      0       2      0          2.534996                  1.0
easyinstances      0       0          0          0      0       0        2      0       2      0          2.534996                  1.0
```

## Configuration

User-defined configuration files are stored in the `~/.ipet` folder, that is considered in the parsing process.
This includes

- `~/.ipet/solvers`, where the user can define their own solver model. For an example check the `SCIPSolver` class in `ipet/parsing/Solver.py`
Additionally you need to place a `__init__.py` file in the `~/.ipet/solvers/` folder that loads the python modules (for example you have to classes `MySolver` and `OtherSolver` in files `~/.ipet/solvers/MySolver.py` and `~/.ipet/solvers/OtherSolver.py`):

        __all__ = []
        from .MySolver import MySolver
        from .OtherSolver import OtherySolver

- `~/.ipet/readers`, where the user can define their own rules for extracting data by giving a line, position and format of the number or string they want to parse from the logfile(s). For an example check `scripts/readers-example.xml`.
- `~/.ipet/solufiles`, that contains solution files with information about the correct solution of instance files or their (inf)feasibility status. For an example check `test/data/short.solu`
- 
## Starting the graphical user interface

IPET has a subdirectory called "scripts" with scripts to invoke log file parsing, test run evaluating, and starting
the graphical user interface.

# Building the documentation

In your virtual environment type:

    pip install sphinx
    cd doc
    make html

your documentation will then be located in doc/build/html/index.html.
