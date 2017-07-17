#!/usr/bin/env bash
set -e
SCRIPTDIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
TARBALL=$1;
LANGUAGE=$2;
DST=$3;
VERSION=$4;
KEY=$5;
DEVSET=$6;


mkdir -p $DST/$LANGUAGE
# TODO: if IL needs swap (e.g. il3) add --swap below to one_button_lrlp
if [ -n "$KEY" ]; then
    $SCRIPTDIR/one_button_lrlp.py --lexversion il3 --evalil -t $TARBALL -l $LANGUAGE -r $DST -k $KEY -S set0 --ruby /Users/jonmay/.rvm/rubies/ruby-2.3.0/bin/ruby &> $DST/$LANGUAGE/one_button_lrlp.err
else
    $SCRIPTDIR/one_button_lrlp.py --lexversion il3 --evalil -t $TARBALL -l $LANGUAGE -r $DST --ruby /Users/jonmay/.rvm/rubies/ruby-2.3.0/bin/ruby &> $DST/$LANGUAGE/one_button_lrlp.err
fi
if [[ -n "$DEVSET" ]] && [[ -e $DEVSET ]];  then
    PREFIX="-d $DEVSET";
else
    PREFIX=""
fi
# TODO: use --allperseg in subselect_data if very few documents!
$SCRIPTDIR/subselect_data.py $PREFIX -i $DST/$LANGUAGE/parallel -e filtered -l $LANGUAGE -s 10000 10000 20000 -c syscomb test dev -t $SCRIPTDIR/incidentvocab &> $DST/$LANGUAGE/subselect_data.err
$SCRIPTDIR/one_button_package.py --noeval -l $LANGUAGE -v $VERSION -r $DST/$LANGUAGE &> $DST/$LANGUAGE/one_button_package.err
for i in syscomb test dev train rejected; do
    $SCRIPTDIR/elisa2flat.py -f FULL_ID_SOURCE SOURCE.id ORIG_RAW_SOURCE ORIG_RAW_TARGET -i $DST/$LANGUAGE/elisa.$LANGUAGE-eng.$i.y1r1.v$VERSION.xml.gz -o $DST/$LANGUAGE/$i.tab; echo $i; $SCRIPTDIR/sample.py -i $DST/$LANGUAGE/$i.tab -s 10;
done > $DST/$LANGUAGE/samples;

$SCRIPTDIR/elisa2flat.py -f FULL_ID_SOURCE SOURCE.id ORIG_RAW_SOURCE ORIG_RAW_TARGET -i $DST/$LANGUAGE/elisa.$LANGUAGE.y1r1.v$VERSION.xml.gz -o $DST/$LANGUAGE/$LANGUAGE.tab
echo "Done with $LANGUAGE version $VERSION in $DST";
ls -l $DST/$LANGUAGE
