#!/usr/bin/env bash
SCRIPT=`basename ${BASH_SOURCE[0]}`
SCRIPTDIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

TARBALL=$1
OLDTRAIN=$2
OUTDIR=$3
PREFIX=$4
MIDFIX=$5

# extract tarball
mkdir -p $OUTDIR
tar -zxf $TARBALL -C $OUTDIR

dstdir=`basename $TARBALL | cut -d'.' -f1`;

# reshape for scripts
for i in train tune test; do
    $SCRIPTDIR/supplemental_reshape.sh $OUTDIR/$dstdir/data/$i $OUTDIR il3;
done

# extract flat data
for i in train tune; do
    $SCRIPTDIR/extract_parallel.py -r $OUTDIR/$i -o $OUTDIR/$i/extracted -s il3
done
$SCRIPTDIR/extract_mono_nozip.py -r $OUTDIR/test --datadirs data translation from_il3 il3 ltf -s il3 -t eng -o $OUTDIR/test/extracted --nogarbage

# build train and join it with 
$SCRIPTDIR/make_parallel_release.py -r $OUTDIR/train/extracted -l il3 -c fromsource.generic -s $OUTDIR/train/train.stats -o $OUTDIR/train/train.xml 
$SCRIPTDIR/mergexml.py -i $OLDTRAIN $OUTDIR/train/train.xml -o $OUTDIR/$PREFIX.train.$MIDFIX

# divide tune into dev and syscomb
$SCRIPTDIR/subselect_for_exercise.py -i $OUTDIR/tune -l il3 -s 2 -c syscomb -r dev
for i in dev syscomb; do
    $SCRIPTDIR/make_parallel_release.py -r $OUTDIR/tune/splits/$i -l il3 -c fromsource.generic -o $OUTDIR/$PREFIX.$i.$MIDFIX -s $OUTDIR/$PREFIX.$i.$MIDFIX.stats;
done

# make mono release
$SCRIPTDIR/make_mono_release.py -r $OUTDIR/test/extracted -l il3 -c mono -s $OUTDIR/$PREFIX.test.$MIDFIX.stats -o $OUTDIR/$PREFIX.test.$MIDFIX
