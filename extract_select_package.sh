#!/usr/bin/env bash
set -e
SCRIPTDIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
TARBALL=$1;
LANGUAGE=$2;
DST=$3;
VERSION=$4;

mkdir -p $DST/$LANGUAGE
$SCRIPTDIR/one_button_lrlp.py -t $TARBALL -l $LANGUAGE -r $DST &> $DST/$LANGUAGE/one_button_lrlp.err
$SCRIPTDIR/subselect_data.py -i $DST/$LANGUAGE/parallel -e filtered -l $LANGUAGE -s 10000 10000 10000 20000 -c eval syscomb test dev -t $SCRIPTDIR/incidentvocab &> $DST/$LANGUAGE/subselect_data.err
$SCRIPTDIR/one_button_package.py -l $LANGUAGE -v $VERSION -r $DST/$LANGUAGE &> $DST/$LANGUAGE/one_button_package.err
echo "Done with $LANGUAGE version $VERSION in $DST";
ls -l $DST/$LANGUAGE
