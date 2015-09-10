#!/usr/bin/env bash

yell() { echo "$0: $*" >&2; }
die() { yell "$*"; exit 111; }
try() { "$@" || die "cannot $*"; }

#Set Script Name variable
SCRIPT=`basename ${BASH_SOURCE[0]}`
SCRIPTDIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

# inroot lang outdir outfile

ROOT=${1:-/home/nlg-02/LORELEI/ELISA/data}
LANG=${2:-uzb}
OUTDIR=${3:-release}
OUTFILE=${4:-release.tar.gz}

# TODO: zip file on creation
# THIS IS MOSTLY UNDONE
# Need to:
#   downselect dev/test/heldout corpora from mt + annotation subset; should match length ratio and source distribution of the rest of the data
#   add in all entity info
#   package up parallel data
#   add identification as needed

mkdir -p $OUTDIR
manifests=`for i in $ROOT/$LANG/mono/extracted/*.manifest; do echo $i | awk -F'/' '{print $NF}' | cut -d'.' -f1; done | sed ':a;N;$!ba;s/\n/ /g'`
try $SCRIPTDIR/make_mono_release.py -r $ROOT/$LANG/mono/extracted -c $manifests -o $OUTDIR/mono.xml -p $ROOT/$LANG/psm.ann -a $ROOT/$LANG/entity.ann &> $OUTDIR/mono_build.err
