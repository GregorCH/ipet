Examples
========

- `index=A B C D`
- `indexsplit=2`
- `defaultgroup=d2:e1`

long table
----------

First part of `index` becomes index of long table, second part becomes column-index.
Note: Both may be hierarchical.

|    |    |      |      |    |      |      |    |      |    |       |    |       |    |
|:---|:---| ---: | ---: |---:| ---: | ---: |---:| ---: |---:|  ---: |---:|  ---: |---:|
| E  |    | e1   | e2   | .. | e1   | e2   | .. | e1   | .. | e1    | .. | e1    | .. |
| D  |    | d1   | d1   | .. | d2   | d2   | .. | d1   | .. | d1    | .. | d2    | .. |
|    |    | col1 | col1 | .. | col1 | col1 | .. | col2 | .. | col1Q | .. | col1Q | .. |
| A  | B  |      |      |    |      |      |    |      | .. |       |    |       |    |
| a1 | b1 |    * |    * | .. |    * |    * | .. |    * | .. |     * | .. |     1 | .. |
|    | b2 |    * |    * | .. |    * |    * | .. |    * | .. |     * | .. |     1 | .. |
|    | b3 |    * |    * | .. |    * |    * | .. |    * | .. |     * | .. |     1 | .. |
|    | .. |   .. |   .. | .. |   .. |   .. | .. |   .. | .. |    .. | .. |    .. | .. |
| a2 | b1 |    * |    * | .. |    * |    * | .. |    * | .. |     * | .. |     1 | .. |
|    | b2 |    * |    * | .. |    * |    * | .. |    * | .. |     * | .. |     1 | .. |
|    | b3 |    * |    * | .. |    * |    * | .. |    * | .. |     * | .. |     1 | .. |
|    | .. |   .. |   .. | .. |   .. |   .. | .. |   .. | .. |    .. | .. |    .. | .. |

aggregated table
----------------

The index of the aggregated table is the second part of `index`.
Note: This means that the column-index of the long table becomes the index of the aggregated table.
For each filtergroup the columns are aggregated to a scalar via the `aggregation` function.

|       |    |    |           |           |    |            |            |    |            |    |             |    |             |    |
|:---   |:---|:---|      ---: |      ---: |---:|       ---: |       ---: |---:|       ---: |---:|        ---: |---:|        ---: |---:|
| group | D  | E  | \_abort\_ | \_count\_ | .. | col1\_agg1 | col1\_agg2 | .. | col2\_agg1 | .. | col1\_agg1Q | .. | col1\_agg1p | .. |
| fg1   | d1 | e1 |         * |         * | .. |          * |          * | .. |          * | .. |           * | .. |           * | .. |
|       |    | e2 |         * |         * | .. |          * |          * | .. |          * | .. |           * | .. |           * | .. |
|       |    | .. |         * |         * | .. |          * |          * | .. |          * | .. |           * | .. |           * | .. |
|       | d2 | e1 |         * |         * | .. |          * |          * | .. |          * | .. |           1 | .. |         NaN | .. |
|       |    | e2 |         * |         * | .. |          * |          * | .. |          * | .. |           * | .. |           * | .. |
|       |    | .. |         * |         * | .. |          * |          * | .. |          * | .. |           * | .. |           * | .. |
| fg2   | d1 | e1 |         * |         * | .. |          * |          * | .. |          * | .. |           * | .. |           * | .. |
|       |    | e2 |         * |         * | .. |          * |          * | .. |          * | .. |           * | .. |           * | .. |
|       |    | .. |         * |         * | .. |          * |          * | .. |          * | .. |           * | .. |           * | .. |
|       | d2 | e1 |         * |         * | .. |          * |          * | .. |          * | .. |           1 | .. |         NaN | .. |
|       |    | e2 |         * |         * | .. |          * |          * | .. |          * | .. |           * | .. |           * | .. |
|       |    | .. |         * |         * | .. |          * |          * | .. |          * | .. |           * | .. |           * | .. |

