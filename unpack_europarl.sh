#!/usr/bin/env bash
#PBS -l walltime=24:00:00
#PBS -T allcores        
#PBS -N unpack_europarl
#PBS -q isi

export LANG=en_US.UTF-8

yell() { echo "$0: $*" >&2; }
die() { yell "$*"; exit 111; }
try() { "$@" || die "cannot $*"; }

# untar and properly simlink new europarl corpus

#Set Script Name variable
SCRIPT=`basename ${BASH_SOURCE[0]}`
SCRIPTDIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

CDECTOK=$SCRIPTDIR/cdectok.sh
ISITOK=$SCRIPTDIR/ulftok.py

#Initialize variables to default values.
WORKROOT=/home/nlg-02/LORELEI/ELISA/mockups

#Set fonts for Help.
NORM=`tput sgr0`
BOLD=`tput bold`
REV=`tput smso`

TMPDIR=${TMPDIR:-/tmp}
TOKTMP=$(mktemp -d --tmpdir=$TMPDIR XXXXXX)
function cleanup() {
    rm -rf $TOKDIR;
}
trap cleanup EXIT


#Help function
function HELP {
  echo -e \\n"Help documentation for ${BOLD}${SCRIPT}.${NORM}"\\n
  echo -e "${REV}Basic usage:${NORM} ${BOLD}$SCRIPT xx-en.gz ...${NORM} (file form is important!)"\\n
  echo "${REV}-r${NORM}  --Sets the data root. Default is ${BOLD}$WORKROOT${NORM}."
  echo -e "${REV}-h${NORM}  --Displays this help message. No further functions are performed."\\n
  echo -e "Example: ${BOLD}$SCRIPT bg-en.tgz${NORM}"\\n
  exit 1
}

#Check the number of arguments. If none are passed, print help and exit.
NUMARGS=$#

if [ $NUMARGS -eq 0 ]; then
    echo -e \\n"Number of arguments: $NUMARGS"
    HELP
fi

### Start getopts code ###

#Parse command line flags
#If an option should be followed by an argument, it should be followed by a ":".
#Notice there is no ":" after "h". The leading ":" suppresses error messages from
#getopts. This is required to get my unrecognized option code to work.

COMMANDLINE=$@;

while getopts :r:h FLAG; do
  case $FLAG in
    r)  #set option "r"
      WORKROOT=$OPTARG
      ;;
    h)  #show help
      HELP
      ;;
    \?) #unrecognized option - show help
      echo -e \\n"Option -${BOLD}$OPTARG${NORM} not allowed."
      HELP
      #If you just want to display a simple error message instead of the full
      #help, remove the 2 lines above and uncomment the 2 lines below.
      #echo -e "Use ${BOLD}$SCRIPT -h${NORM} to see the help documentation."\\n
      #exit 2
      ;;
  esac
done

shift $((OPTIND-1))  #This tells getopts to move on to the next argument.

### End getopts code ###

### Main loop to process files ###

DATAPREFIX="europarl"
FILEPREFIX="europarl-v7"

#This is where your main file processing will take place. This example is just
#printing the files and extensions to the terminal. You should place any other
#file processing tasks within the while-do loop.

while [ $# -ne 0 ]; do
  FILE=$1
  BASE=$(basename $FILE)
  SHORTCODE=$(echo "$BASE" | cut -d'-' -f1)
  TARGETSHORTCODE=$(echo "$BASE" | cut -d'-' -f2 | cut -d'.' -f1)
  LRL_LANG=$((echo "import pycountry as pl" ; echo "print pl.languages.get(iso639_1_code='$SHORTCODE').iso639_3_code") | python)
  TARGET_LRL_LANG=$((echo "import pycountry as pl" ; echo "print pl.languages.get(iso639_1_code='$TARGETSHORTCODE').iso639_3_code") | python)
  echo "$SHORTCODE ($LRL_LANG) -> $TARGETSHORTCODE ($TARGET_LRL_LANG)"

  DATALOC=$WORKROOT/$LRL_LANG/parallel/extracted/;
  ORIGLOC=$DATALOC/original;
  ISILOC=$DATALOC/tok.isi;
  CDECLOC=$DATALOC/tok.cdec;

  TARLOC=$WORKROOT/$LRL_LANG/tars;
  EXPLOC=$WORKROOT/$LRL_LANG/expanded;



  TARBALL=$PWD/$1;
  if [ ! -e $TARBALL ]; then
      echo "Couldn't find $TARBALL"
      exit 1;
  fi
  mkdir -p $TARLOC;
  LRLPNAMEPREFIX=$TARLOC/$LRL_LANG
  LRLPNAME=$LRLPNAMEPREFIX.tar.gz;
  COUNTER=0
  NEWBASENAME="tar"
  EXPLOC=$WORKROOT/$LRL_LANG/expanded;
  while [ -e $LRLPNAME ] || [ -h $LRLPNAME ]; do
      COUNTER=$((COUNTER+1));
      LRLPNAMEPREFIX=$TARLOC/$LRL_LANG.$COUNTER;
      LRLPNAME=$LRLPNAMEPREFIX.tar.gz;
      NEWBASENAME="tar.$COUNTER"
  done
  ln -s $TARBALL $LRLPNAME
  cat >>$TARLOC/source <<EOF
Linked $TARBALL to $LRLPNAME on $(date).
Will extract to $EXPLOC;
Using [ $SCRIPT $COMMANDLINE ] from $PWD 
EOF
  mkdir -p $EXPLOC;
  cat >>$EXPLOC/source <<EOF
Extracted $LRLPNAME here on $(date).
Using [ $SCRIPT $COMMANDLINE ] from $PWD 
$NEWBASENAME comes from $LRLPNAME
EOF
  tar -C $EXPLOC -zxf $LRLPNAME
  # assume the tarball contains untokenized parallel data
  mkdir -p $ORIGLOC
  ln -s $EXPLOC/$FILEPREFIX.$SHORTCODE-$TARGETSHORTCODE.$SHORTCODE $ORIGLOC/$DATAPREFIX.$LRL_LANG;
  ln -s $EXPLOC/$FILEPREFIX.$SHORTCODE-$TARGETSHORTCODE.$TARGETSHORTCODE $ORIGLOC/$DATAPREFIX.$TARGET_LRL_LANG;
  cat >>$ORIGLOC/source <<EOF
Linked files from $LRLPNAME here on $(date).
Using [ $SCRIPT $COMMANDLINE ] from $PWD
EOF
  # tokenization: cdec style and isi style (latter for eng only)
  for lang in $LRL_LANG $TARGET_LRL_LANG; do
      mkdir -p $CDECLOC/lc;
      cmd="$CDECTOK -i $ORIGLOC/$DATAPREFIX.$lang -o $CDECLOC/lc/$DATAPREFIX.tok.lc.$lang -t $CDECLOC/$DATAPREFIX.tok.$lang"
      echo $cmd >> $DATALOC/source
      `$cmd` 2>&1 >> $DATALOC/cdectok.errors
      if [ $lang == "eng" ]; then
	  mkdir -p $ISILOC/lc;
	  cmd="$ISITOK -i $ORIGLOC/$DATAPREFIX.$lang -o $ISILOC/lc/$DATAPREFIX.tok.lc.$lang -t $ISILOC/$DATAPREFIX.tok.$lang";
	  echo $cmd >> $DATALOC/source
	  `$cmd` 2>&1 >> $DATALOC/isitok.errors 
      fi
  done
  shift
done

exit 0