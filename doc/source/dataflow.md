Dataflow
========

Long table
----------

1. Start with data from \*.trn-files and external data.

2. Add generalinfo: \_count\_, \_solved\_, \_time\_, \_limit\_, \_fail\_, \_abort\_, \_unkn\_.

3. Substitute `alternative` values applying (or-concatenated) (`Column`)`Filter`s and generate userdefined `Column`s in topological order (respecting dependencies).

4. Select relevant columns: userdefined `Column`s and their dependencies.

5. `Reduce` columns such that the specified `index` becomes unique. 
    - \_solved\_: all
    - \_count\_: max
    - \_\*\*\*\_: any
    - default reduce for other columns: ??? mean/strConcat?

6. Add columns containing `comp`arison with `defaultgroup`.

Aggregated table
----------------

For each `Filtergroup`, do the following with the data from long table:

1. Select data by applying all (and-concatenated) `Filter`s.

2. Generate aggregated table:
    - `Aggregate` columns (generalinfo and columns) of long table to rows in aggregated table.
    - Generate columns containing `comp`arison to `defaultgroup`.
    - Add columns containing statistical tests of aggregated columns.
