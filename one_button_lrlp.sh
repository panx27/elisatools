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
LANGUAGE=${2:-uzb}
ROOT=${3:-/home/nlg-02/LORELEI/ELISA/data}

EXPDIR=`try $SCRIPTDIR/unpack_lrlp.sh -l $LANGUAGE -r $ROOT $TARBALL`;
try $EXPDIR/tools/twitter-processing/get_tweet_by_id.rb $ROOT/$LANGUAGE/tweet < $EXPDIR/docs/twitter_info.tab 2>$ROOT/$LANGUAGE/extract_tweet.err
echo "get_tweet_by_id.rb Done."
$EXPDIR/tools/ltf2rsd/ltf2rsd.perl $EXPDIR/data/translation/from_"$LANGUAGE"/eng
echo "ltf2rsd.perl Done."
try $SCRIPTDIR/extract_lexicon.py -i $EXPDIR/data/lexicon/*.xml -o $ROOT/$LANGUAGE/lexicon 2> $ROOT/$LANGUAGE/extract_lexicon.err
echo "extract_lexicon.py Done."
$SCRIPTDIR/extract_psm_annotation.py -i $EXPDIR/data/monolingual_text/zipped/*.psm.zip -o $ROOT/$LANGUAGE/psm.ann
echo "extract_psm_annotation.py Done."
$SCRIPTDIR/extract_entity_annotation.py -r $EXPDIR -o $ROOT/$LANGUAGE/entity.ann -et $ROOT/$LANGUAGE/tweet
echo "extract_entity_annotation.py Done."
try $SCRIPTDIR/extract_parallel.py -r $EXPDIR -o $ROOT/$LANGUAGE/parallel/extracted -s $LANGUAGE -et $ROOT/$LANGUAGE/tweet 2> $ROOT/$LANGUAGE/extract_parallel.err;
echo "extract_parallel.py Done."
try $SCRIPTDIR/extract_mono.py -i $EXPDIR/data/monolingual_text/zipped/*.ltf.zip -o $ROOT/$LANGUAGE/mono/extracted 2> $ROOT/$LANGUAGE/extract_mono.err;
echo "extract_mono.py Done."
