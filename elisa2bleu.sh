#!/usr/bin/env bash

# get a bleu score from an elisa file. Assume reference and source are in it.

set -e

tmpdir=${TMPDIR:-/tmp}
# TODO: gmktemp option?
MTMP=$(gmktemp -d --tmpdir=$tmpdir XXXXXX)
function cleanup() {
    rm -rf $MTMP;
}
trap cleanup EXIT

SCRIPTDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

INFILE=$1;

x=$MTMP/xtract

$SCRIPTDIR/elisa2flat.py -f ORIG_RAW_SOURCE TEXT ORIG_RAW_TARGET -i $INFILE -o $x

reflen=$(head -1 $x | awk -F'\t' '{print NF}')
cut -f1 $x > $MTMP/src
cut -f2 $x > $MTMP/tst
for i in $(seq 3 $reflen); do
    cut -f$i $x > $MTMP/ref.$i;
done


for i in src ref tst; do 
    $SCRIPTDIR/flat2nist.py -i $(find $MTMP -name "$i*") -t $i -o $MTMP/$i.xml
done

$SCRIPTDIR/mteval-v14c.pl -b -c -r $MTMP/ref.xml -s $MTMP/src.xml -t $MTMP/tst.xml | grep "^BLEU" | cut -d' ' -f4
#$SCRIPTDIR/mteval-v14c.pl -b -c -r $MTMP/ref.xml -s $MTMP/src.xml -t $MTMP/tst.xml -d 3

