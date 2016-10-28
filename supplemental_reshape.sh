#!/usr/bin/env bash

# reshaping script so we can work with the supplemental exercise directory structure

INDIR=$1;
OUTDIR=$2;
LANG=$3;

base=`basename $INDIR`;
for l in $LANG eng; do
    id=$INDIR/$l;
    if [ -e $id ]; then
        od=$OUTDIR/$base/data/translation/from_"$LANG"/$l/ltf;
        mkdir -p $od;
        cp $id/*.xml $od;
    else
        echo "$id not found"
    fi
done
