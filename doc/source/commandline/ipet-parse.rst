Format String Examples
----------------------

With the -f option, a format string can be specified to control the
parsing output. Normal Python format syntax with curly braces '{}' is
used for this. The default value for the format string is '{idx} {d}',
which will output the index of every instance together with its complete
data series. 'd' stands for 'data'. By accessing the elements of 'd'
with the format string, only relevant information is displayed on the
console.

::

    >>> cat test/data/scip-*.out | ipet-parse -f "{idx} {d.ProblemName} {d.SolvingTime}"

should yield

::

    0 enlight16 0.02
    1 janos-us-DDM 6807.85
    2 misc03 0.79
    3 aflow40b 600.0

To make the information more readible, the syntax has further options
for formatting:

::

    >>> cat test/data/scip-*.out | ipet-parse -f "{idx:3} {d.ProblemName:40} {d.SolvingTime:12}"

    0 enlight16                                        0.02
    1 janos-us-DDM                                  6807.85
    2 misc03                                           0.79
    3 aflow40b                                        600.0

