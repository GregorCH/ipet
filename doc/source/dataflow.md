Dataflow
========

Long table
----------

1. Start with data from \*.trn-files and external data.

2. Add generalinfo: \_count\_, \_solved\_, \_time\_, \_limit\_, \_fail\_, \_abort\_, \_unkn\_.

3. Substitute ``alternative`` values applying (or-concatenated) (``Column``-) ``Filters`` and generate userdefined ``Columns`` in topological order (respecting dependencies).
    - alternative (conditions and NaN)
    - minval
    - maxval

4. Select relevant columns: userdefined ``Columns`` and their dependencies.

5. ``Reduce`` columns such that the specified ``index`` becomes unique. 
    - \_solved\_: all
    - \_count\_: max
    - \_\*\*\*\_: any
    - default reduce for other columns: mean or string concatenation

6. Add columns containing ``comp`` arison with ``defaultgroup``.

Aggregated table
----------------

For each ``Filtergroup``, do the following with the data from long table:

1. Select data by applying all (and-concatenated) ``Filters``.

2. Generate aggregated table:
    - ``Aggregate`` columns (generalinfo and columns) of long table to rows in aggregated table.
    - Generate columns containing comparison of aggregations to ``defaultgroup``.
    - Add columns containing statistical tests of aggregated columns.

Note
----

This means, that
    - columns **can** refer to each other (in any way) as long as the dependencies are **not** circular.
    - ``alternatives`` are substituted **before** any ``reductions`` and ``transformations`` take place.
    - ``transformations`` are evaluated **before** ``reductions``, i.e. it does not make very much sense to reuse values from columns where you are interested in a (real) reduction
