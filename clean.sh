#!/usr/bin/env bash
set -e
SCRIPTDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
wilde=$SCRIPTDIR/wildeclean-v1.0.pl
nfkc=$SCRIPTDIR/nfkc.py


IN=${1:-/dev/stdin}
OUT=${2:-/dev/stdout}
$wilde < $IN | $nfkc > $OUT
