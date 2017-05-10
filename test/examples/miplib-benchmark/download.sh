#!/bin/bash
#
# download benchmark results for different solvers and store them in a subdirectory logfiles
#
outfiles=("http://plato.asu.edu/ftp/milpc_log1/benchmark.cbc.out" \
       "http://plato.asu.edu/ftp/milpc_log1/benchmark.cplex.out" \
       "http://plato.asu.edu/ftp/milpc_log1/benchmark.gurobi.out" \
       "http://plato.asu.edu/ftp/milpc_log1/benchmark.mipcl.out" \
       "http://plato.asu.edu/ftp/milpc_log1/benchmark.scipc.out" \
       "http://plato.asu.edu/ftp/milpc_log1/benchmark.scips.out" \
       "http://plato.asu.edu/ftp/milpc_log1/benchmark.xpress.out")

resfiles=("http://plato.asu.edu/ftp/milpc_res1/benchmark.cbc.res" \
       "http://plato.asu.edu/ftp/milpc_res1/benchmark.cplex.res" \
       "http://plato.asu.edu/ftp/milpc_res1/benchmark.gurobi.res" \
       "http://plato.asu.edu/ftp/milpc_res1/benchmark.mipcl.res" \
       "http://plato.asu.edu/ftp/milpc_res1/benchmark.scipc.res" \
       "http://plato.asu.edu/ftp/milpc_res1/benchmark.scips.res" \
       "http://plato.asu.edu/ftp/milpc_res1/benchmark.xpress.res")

mkdir -p logfiles
for f in ${outfiles[@]} ${resfiles[@]}
do
    wget $f -O logfiles/`basename $f`
done