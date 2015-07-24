#!/usr/bin/env bash

yell() { echo "$0: $*" >&2; }
die() { yell "$*"; exit 111; }
try() { "$@" || die "cannot $*"; }

#Set Script Name variable
SCRIPT=`basename ${BASH_SOURCE[0]}`
SCRIPTDIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

# tarball lang outroot

TARBALL=${1:-lrlp.tar.gz}
LANG=${2:-uzb}
ROOT=${3:-/home/nlg-02/LORELEI/ELISA/data}


EXPDIR=`try $SCRIPTDIR/unpack_lrlp.sh -l $LANG -r $ROOT $TARBALL`;
try $SCRIPTDIR/extract_lexicon.py -i $EXPDIR/data/lexicon/lexicon.llf.xml -o $ROOT/$LANG/lexicon 2> $ROOT/$LANG/extract_lexicon.err
try $SCRIPTDIR/extract_parallel.py -r $EXPDIR -o $ROOT/$LANG/parallel/extracted -s $LANG 2> $ROOT/$LANG/extract_parallel.err;
try $SCRIPTDIR/extract_mono.py -i $EXPDIR/data/monolingual_text/zipped/*.ltf.zip -o $ROOT/$LANG/mono/extracted 2> $ROOT/$LANG/extract_mono.err;
# tweets! requires gem and twitter module