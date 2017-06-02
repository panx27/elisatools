#!/usr/bin/env bash
#PBS -q isi
#PBS -l walltime=24:00:00
#PBS -j oe

set -e
SCRIPTDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"


wilde=$SCRIPTDIR/wildeclean-v1.0.pl
nfkc=$SCRIPTDIR/nfkc.py


IN=${1:-/dev/stdin}
OUT=${2:-/dev/stdout}
$nfkc -i <($wilde -r < $IN) -o $OUT
