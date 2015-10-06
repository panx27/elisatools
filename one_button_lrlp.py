#! /usr/bin/env python
import argparse
import sys
import codecs
from itertools import izip
from collections import defaultdict as dd
import re
import os.path
from subprocess import check_output, check_call, CalledProcessError
scriptdir = os.path.dirname(os.path.abspath(__file__))

class Step:
  def __init__(self, prog, progpath=scriptdir, argstring="", stdin=None, stdout=None, stderr=None, help=None, call=check_call):
    self.prog = prog
    self.help = help
    self.progpath = progpath
    self.argstring = argstring
    self.stdin = stdin
    self.stdout = stdout
    self.stderr = stderr
    self.call = call
  def run(self):
    kwargs = {}
    kwargs["shell"]=True
    if self.stdin is not None:
      kwargs["stdin"]=self.stdin
    if self.stdout is not None:
      kwargs["stdout"]=self.stdout
    if self.stderr is not None:
      kwargs["stderr"]=self.stderr
    prog = os.path.join(self.progpath, self.prog)
    # TODO: could check that prog exists and is executable
    # TODO: fail or succeed based on return code and specified behavior
    return self.call("%s %s" % (prog, self.argstring), **kwargs) 

class listSteps(argparse.Action):
  def __call__(self, parser, args, values, option_string=None):
    print "This is where I list steps"

def make_action(steps):
  class customAction(argparse.Action):
    def __call__(self, parser, args, values, option_string=None):
      for stepnum, step in enumerate(steps):
        sys.stderr.write("%d: %s" % (stepnum, step.prog))
        if step.help is not None:
          sys.stderr.write(" = "+step.help)
        sys.stderr.write("\n")
      sys.exit(0)
  return customAction


def main():

  steps = []
  # steps that need their script adjusted after step 0 runs
  adjustmentsteps = []
  # put steps in here


  steps.append(Step('unpack_lrlp.sh', call=check_output, help="untars lrlp into position for further processing"))
  steps.append(Step('get_tweet_by_id.rb', help="download tweets. must have twitter gem installed and full internet"))
  adjustmentsteps.append(steps[-1])
  steps.append(Step('ltf2rsd.perl', help="get flat form of tweet translations"))
  adjustmentsteps.append(steps[-1])
  steps.append(Step('extract_lexicon.py', help="get flat form of bilingual lexicon"))
  steps.append(Step('extract_psm_annotation.py', help="get annotations from psm files into psm.ann"))
  steps.append(Step('extract_entity_annotation.py', help="get entity and other annotations into entity.ann"))
  steps.append(Step('extract_parallel.py', help="get flat form parallel data"))
  steps.append(Step('extract_mono.py', help="get flat form mono data"))

  stepsbyname = {}
  for step in steps:
    stepsbyname[step.prog] = step


  parser = argparse.ArgumentParser(description="Process a LRLP into flat format",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--tarball", "-t", default='lrlp.tar.gz', help='path to gzipped tar for processing')
  parser.add_argument("--language", "-l", default='uzb', help='three letter code of language')
  parser.add_argument("--root", "-r", default='/home/nlg-02/LORELEI/ELISA/data', help='path to where the extraction will take place')
  parser.add_argument("--expdir", "-e", help='path to where the extraction is. If starting at step 0 this is ignored')
  parser.add_argument("--start", "-s", type=int, default=0, help='step to start at')
  parser.add_argument("--liststeps", "-x", nargs=0, action=make_action(steps), help='print step list and exit')

  try:
    args = parser.parse_args()
  except IOError, msg:
    parser.error(str(msg))

  if args.expdir is not None and args.start <=0:
    sys.stderr.write("Warning: expdir is set but will be ignored and determined dynamically")
  if args.expdir is None and args.start >0:
    sys.stderr.write("Error: must explicitly set expdir if not starting at step 0")
    sys.exit(1)

  # patchups
  stepsbyname["unpack_lrlp.sh"].argstring="-l %s -r %s %s" % ($LANGUAGE -r $ROOT $TARBALL`;
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



                      
if __name__ == '__main__':
  main()
