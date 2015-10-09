#!/usr/bin/env bash
#PBS -l walltime=12:00:00
#PBS -T allcores
#PBS -N cdectok
#PBS -q isi

# wrap cdec tokenizer/safe LC

#Set Script Name variable
SCRIPT=`basename ${BASH_SOURCE[0]}`
SCRIPTDIR=`dirname $0`

#Set fonts for Help.
NORM=`tput sgr0`
BOLD=`tput bold`
REV=`tput smso`

OUTFILE=/dev/stdout
TOKFILE=/dev/null
INFILE=/dev/stdin

TOKENIZER=$SCRIPTDIR/cdectok/tokenize-anything.sh

#Help function
function HELP {
  echo -e \\n"Help documentation for ${BOLD}${SCRIPT}.${NORM}"\\n
  echo -e "${REV}Basic usage:${NORM} ${BOLD}$SCRIPT -i corpus -o tok.lc -t tok ${NORM}"\\n
  echo "${REV}-t${NORM}  --Destination for tokenized file. Default is ${BOLD}$TOKFILE${NORM}."
  echo "${REV}-o${NORM}  --Destination for tokenized, lowercased file. Default is ${BOLD}$OUTFILE${NORM}."
  echo "${REV}-i${NORM}  --Source for untokenized, truecased file. Default is ${BOLD}$INFILE${NORM}."
  echo -e "${REV}-h${NORM}  --Displays this help message. No further functions are performed."\\n
  exit 1
}


### Start getopts code ###

#Parse command line flags
#If an option should be followed by an argument, it should be followed by a ":".
#Notice there is no ":" after "h". The leading ":" suppresses error messages from
#getopts. This is required to get my unrecognized option code to work.

COMMANDLINE=$@;

while getopts :i:o:t:h FLAG; do
  case $FLAG in
    i)  #set option "r"
      INFILE=$OPTARG
      ;;
    o)  #set option "o"
      OUTFILE=$OPTARG
      ;;
    t)  #set option "t"
      TOKFILE=$OPTARG
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

$TOKENIZER < $INFILE 2> /dev/null | tee $TOKFILE | sed -e 's/\(.*\)/\L\1/' > $OUTFILE;

exit 0
