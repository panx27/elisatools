#!/usr/bin/env bash
#PBS -l walltime=12:00:00
#PBS -N truecase
#PBS -q isi

# qsub safe call to truecase
set -e

#Set Script Name variable
SCRIPT=`basename ${BASH_SOURCE[0]}`
SCRIPTDIR=`dirname $0`

CASER=$SCRIPTDIR/truecase.perl

$CASER --model $1 < $2 > $3;
