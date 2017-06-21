#!/usr/bin/env bash

# get a bleu score from an elisa file. Assume reference and source are in it.

set -e

tmpdir=${TMPDIR:-/tmp}
MTMP=$(mktemp -d --tmpdir=$tmpdir XXXXXX)
function cleanup() {
    rm -rf $MTMP;
}
trap cleanup EXIT

SCRIPTDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

INFILE=$1;

x=$MTMP/xtract

$SCRIPTDIR/elisa2flat.py -f ORIG_RAW_SOURCE ORIG_RAW_TARGET TEXT -i $INFILE -o $x

cut -f1 $x > $MTMP/src
cut -f2 $x > $MTMP/ref
cut -f3 $x > $MTMP/tst

for i in src ref tst; do 
    $SCRIPTDIR/flat2nist.py -i $MTMP/$i -t $i -o $MTMP/$i.xml
done

$SCRIPTDIR/mteval-v14.pl -b -c -r $MTMP/ref.xml -s $MTMP/src.xml -t $MTMP/tst.xml | grep "^BLEU" | cut -d' ' -f4

