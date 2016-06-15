Installation and prerequisites
------------------------------

This section covers the installation of IPET. We assume that you have a working
Python 2.7 installation. On top of that, we require
 - matplotlib version 1.3.1 or higher
 - Tkinter with Tcl/Tk version 8.5 or higher
 - pandas version 0.15.0 or higher
 - for some distributions, the Pillow library as a replacement for the PIL library.

In order to install the IPET-module and its contents to the python path and
thus make it importable from every working directory you are in,
run the command:

 python setup.py install [--user]

This will install IPET to your Python distribution, and make
it importable from every working directory in the file system. If
you do not have administrator rights on your system, append '--user'
in order to install the package to your local Python libraries.
If you now start an interactive python interpreter from any working directory,
you can import IPET as a module into your Python scripts and use its methods.

The user interface uses the Python Image Library (PIL) to display button images
via PNG files. In case you have an error that says PIL could not be found, install
Pillow via

 pip install Pillow [--user]

or

 python easy_install Pillow [--user]

