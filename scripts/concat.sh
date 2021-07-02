#!/bin/bash

function usage {
    echo "Usage: $0 -f|--files <FILES>"
    echo "<FILES>: path to the folder containing input files in .out format (output files of SCIP)"
    exit 1
}

# exactly one param with required argument
if [ "$#" -ne 2 ]; then usage ; fi

# read the options
OPTS=$(getopt --options "f:" --long "files:" --name "$0" -- "$@")
if [ $? != 0 ] ; then usage ; fi
eval set -- "$OPTS"

# extract options and their arguments into variables.
while true ; do
  case "$1" in
    -f | --files )
      FILES="$2"
      shift 2
      ;;
    -- )
      shift
      break
      ;;
    *)
      echo "Internal error!"
      exit 1
      ;;
  esac
done

LOGFILENAME="$FILES"/concatenated

if test -f $LOGFILENAME
then
    echo $LOGFILENAME.out already exists. Exiting.
    exit 1
else
    rm -f $LOGFILENAME.out
fi

for i in "$FILES"/*
do
    echo "@01 $i" >> $LOGFILENAME.out
    cat $i >> $LOGFILENAME.out
    echo "=ready=" >> $LOGFILENAME.out
done

echo "Concatenated logs from folder '$FILES' into '$LOGFILENAME.out'."
