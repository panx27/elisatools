#!/usr/bin/env bash

# untar and properly simlink new lrlp

#Set Script Name variable
SCRIPT=`basename ${BASH_SOURCE[0]}`

#Initialize variables to default values.
LRL_LANG=uzb
WORKROOT=/home/nlg-02/LORELEI/ELISA/data
ENC_KEY=""
ENC_SET=""

#Set fonts for Help.
NORM="";#`tput sgr0`
BOLD="";#`tput bold`
REV="";#`tput smso`

#Help function
function HELP {
  echo -e \\n"Help documentation for ${BOLD}${SCRIPT}.${NORM}"\\n
  echo -e "${REV}Basic usage:${NORM} ${BOLD}$SCRIPT tarball.gz${NORM}"\\n
  echo "Command line switches are optional. The following switches are recognized."
  echo "${REV}-l${NORM}  --Sets the language of the lrlp. Default is ${BOLD}$LRL_LANG${NORM}."
  echo "${REV}-r${NORM}  --Sets the data root. Default is ${BOLD}$WORKROOT${NORM}."
  echo "${REV}-k${NORM}  --Sets the key to decrypt with. Default is unset."
  echo "${REV}-s${NORM}  --Sets the set to decrypt. Default is unset."
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

while getopts :l:r:k:s:h FLAG; do
  case $FLAG in
    l)  #set option "l"
      LRL_LANG=$OPTARG
      ;;
    r)  #set option "r"
      WORKROOT=$OPTARG
      ;;
    k)  #set option "k"
      ENC_KEY=$OPTARG
      ;;
    s)  #set option "s"
      ENC_SET=$OPTARG
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


LRLPLOC=$WORKROOT/$LRL_LANG/lrlps;
EXPLOC=$WORKROOT/$LRL_LANG/expanded;

mkdir -p $LRLPLOC;
LRLPNAMEPREFIX=$LRLPLOC/$LRL_LANG
NEWBASENAME="lrlp"
EXPLOC=$WORKROOT/$LRL_LANG/expanded;
mkdir -p $EXPLOC/$NEWBASENAME;

PART=0
for TARBALL in $@; do
    TARBALL=$(greadlink -f $TARBALL);
    #echo $TARBALL
    if [ ! -e $TARBALL ]; then
        echo "Couldn't find $TARBALL"
        exit 1;
    fi
    LRLPNAME=$LRLPNAMEPREFIX.part.$PART.tar.gz;
    ln -s $TARBALL $LRLPNAME
    cat >>$LRLPLOC/source <<EOF
Linked $TARBALL to $LRLPNAME on $(date).
Will extract to $EXPLOC;
Using [ $SCRIPT $COMMANDLINE ] from $PWD
EOF

    cat >>$EXPLOC/source <<EOF
Extracted $LRLPNAME here on $(date).
Using [ $SCRIPT $COMMANDLINE ] from $PWD
$NEWBASENAME comes from $LRLPNAME
EOF
    #echo "about to run tar -C $EXPLOC -zxf $LRLPNAME "
    # WARNING: very brittle way to find the directory name
    ORIGBASENAME=`(tar -ztf $LRLPNAME | python -c "import os,sys; print ''.join([os.path.normpath(x) for x in sys.stdin])" | grep -v "^\." | grep "/" | head -1) 2>/dev/null`
    tar -C $EXPLOC -zxf $LRLPNAME
    cp -R $EXPLOC/$ORIGBASENAME/* $EXPLOC/$NEWBASENAME/
    rm -rf $EXPLOC/$ORIGBASENAME
    PART=$((PART+1))
done


# get rid of dot files; nothing but trouble
find $EXPLOC/$NEWBASENAME -name "\.*" | xargs rm
echo "$EXPLOC/$NEWBASENAME"
if [ -n "$ENC_KEY" ]; then
    cd $EXPLOC/$NEWBASENAME;
    cat $ENC_SET.tar.bz2.openssl | openssl enc -d -aes-256-cbc -salt -k $ENC_KEY | tar jxf -
fi

exit 0
