#!/usr/bin/env bash

# TODO: there are some logical flaws here involving what happens when trying to
#       re-extract .1, .2, etc. should be part of the language prefix perhaps?
#       language specified on input could be auto-detected

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
try $SCRIPTDIR/twitter-processing/get_tweet_by_id.rb $ROOT/$LANG/tweet < $EXPDIR/docs/twitter_info.tab 2>$ROOT/$LANG/extract_tweet.err
echo "get_tweet_by_id.rb Done."
$SCRIPTDIR/ltf2rsd.perl $EXPDIR/data
echo "ltf2rsd.perl Done."
try $SCRIPTDIR/extract_lexicon.py -i $EXPDIR/data/lexicon/*.xml -o $ROOT/$LANG/lexicon 2> $ROOT/$LANG/extract_lexicon.err
echo "extract_lexicon.py Done."
$SCRIPTDIR/extract_psm_annotation.py -i $EXPDIR/data/monolingual_text/zipped/*.psm.zip -o $ROOT/$LANG/psm.ann
echo "extract_psm_annotation.py Done."
$SCRIPTDIR/extract_entity_annotation.py -r $EXPDIR -o $ROOT/$LANG/entity.ann -et $ROOT/$LANG/tweet
echo "extract_entity_annotation.py Done."
try $SCRIPTDIR/extract_parallel.py -r $EXPDIR -o $ROOT/$LANG/parallel/extracted -s $LANG -et $ROOT/$LANG/tweet 2> $ROOT/$LANG/extract_parallel.err;
echo "extract_parallel.py Done."
try $SCRIPTDIR/extract_mono.py -i $EXPDIR/data/monolingual_text/zipped/*.ltf.zip -o $ROOT/$LANG/mono/extracted 2> $ROOT/$LANG/extract_mono.err;
echo "extract_mono.py Done."
