#!/usr/bin/env bash

# untar and properly simlink new lrlp

#Set Script Name variable
SCRIPT=`basename ${BASH_SOURCE[0]}`

#Initialize variables to default values.
LRL_LANG=uzb
WORKROOT=/home/nlg-02/LORELEI/ELISA/data

#Set fonts for Help.
NORM=`tput sgr0`
BOLD=`tput bold`
REV=`tput smso`

#Help function
function HELP {
  echo -e \\n"Help documentation for ${BOLD}${SCRIPT}.${NORM}"\\n
  echo -e "${REV}Basic usage:${NORM} ${BOLD}$SCRIPT tarball.gz${NORM}"\\n
  echo "Command line switches are optional. The following switches are recognized."
  echo "${REV}-l${NORM}  --Sets the language of the lrlp. Default is ${BOLD}$LRL_LANG${NORM}."
  echo "${REV}-r${NORM}  --Sets the data root. Default is ${BOLD}$WORKROOT${NORM}."
  echo -e "${REV}-h${NORM}  --Displays this help message. No further functions are performed."\\n
  echo -e "Example: ${BOLD}$SCRIPT -l tur tarball.gz${NORM}"\\n
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

while getopts :l:r:h FLAG; do
  case $FLAG in
    l)  #set option "l"
      LRL_LANG=$OPTARG
      ;;
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

#This is where your main file processing will take place. This example is just
#printing the files and extensions to the terminal. You should place any other
#file processing tasks within the while-do loop.

LRLPLOC=$WORKROOT/$LRL_LANG/lrlps;
EXPLOC=$WORKROOT/$LRL_LANG/expanded;

  TARBALL=$PWD/$1;
  if [ ! -e $TARBALL ]; then
      echo "Couldn't find $TARBALL"
      exit 1;
  fi
  mkdir -p $LRLPLOC;
  LRLPNAMEPREFIX=$LRLPLOC/$LRL_LANG
  LRLPNAME=$LRLPNAMEPREFIX.tar.gz;
  COUNTER=0
  NEWBASENAME="lrlp"
  EXPLOC=$WORKROOT/$LRL_LANG/expanded;
  while [ -e $LRLPNAME ] || [ -h $LRLPNAME ]; do
      COUNTER=$((COUNTER+1));
      LRLPNAMEPREFIX=$LRLPLOC/$LRL_LANG.$COUNTER;
      LRLPNAME=$LRLPNAMEPREFIX.tar.gz;
      NEWBASENAME="lrlp.$COUNTER"
  done
  ln -s $TARBALL $LRLPNAME
  cat >>$LRLPLOC/source <<EOF
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
  #echo "about to run tar -C $EXPLOC -zxf $LRLPNAME "
  # WARNING: very brittle way to find the directory name
  ORIGBASENAME=`(tar -ztf $LRLPNAME | grep -v "^\." | grep "/" | head -1) 2>/dev/null`
  tar -C $EXPLOC -zxf $LRLPNAME
  mv $EXPLOC/$ORIGBASENAME $EXPLOC/$NEWBASENAME
  # get rid of dot files; nothing but trouble
  find $EXPLOC/$NEWBASENAME -name "\.*" | xargs rm
  echo "$EXPLOC/$NEWBASENAME"


exit 0
