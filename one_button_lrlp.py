#! /usr/bin/env python
import argparse
import sys
import codecs
from itertools import izip
from collections import defaultdict as dd
import re
import os.path
import glob
from subprocess import check_output, check_call, CalledProcessError
scriptdir = os.path.dirname(os.path.abspath(__file__))

class Step:
  def __init__(self, prog, progpath=scriptdir, argstring="", stdin=None, stdout=None, stderr=None, help=None, call=check_call, abortOnFail=True):
    self.prog = prog
    self.help = help
    self.progpath = progpath
    self.argstring = argstring
    self.stdin = stdin
    self.stdout = stdout
    self.stderr = stderr
    self.call = call
    self.abortOnFail = abortOnFail
  def run(self):
    kwargs = {}
    kwargs["shell"]=True
    if self.stdin is not None:
      kwargs["stdin"]=open(self.stdin)
    if self.stdout is not None:
      kwargs["stdout"]=open(self.stdout, 'w')
    if self.stderr is not None:
      kwargs["stderr"]=open(self.stderr, 'w')
    prog = os.path.join(self.progpath, self.prog)
    # TODO: could check that prog exists and is executable
    # TODO: fail or succeed based on return code and specified behavior
    try:
      localstderr =  kwargs["stderr"] if self.stderr is not None else sys.stderr
      localstderr.write("Calling %s %s\n" % (prog, self.argstring))
      retval = self.call("%s %s" % (prog, self.argstring), **kwargs)
      sys.stderr.write("%s: Done\n" % prog)
    except CalledProcessError as exc:
      sys.stderr.write("%s: FAIL: %d %s\n" % (prog, exc.returncode, exc.output))
      if self.abortOnFail:
        sys.exit(1)
    return retval

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

  # put additional steps in here. Arguments, stdin/stdout, etc. get set below
  steps.append(Step('unpack_lrlp.sh', call=check_output, help="untars lrlp into position for further processing"))
  steps.append(Step('get_tweet_by_id.rb', help="download tweets. must have twitter gem installed and full internet"))
  steps.append(Step('ltf2rsd.perl', help="get flat form of tweet translations", abortOnFail=False))
  steps.append(Step('extract_lexicon.py', help="get flat form of bilingual lexicon"))
  steps.append(Step('extract_psm_annotation.py', help="get annotations from psm files into psm.ann", abortOnFail=False))
  steps.append(Step('extract_entity_annotation.py', help="get entity and other annotations into entity.ann", abortOnFail=False))
  steps.append(Step('extract_parallel.py', help="get flat form parallel data"))
  steps.append(Step('extract_mono.py', help="get flat form mono data"))
  steps.append(Step('make_mono_release.py', help="package mono flat data"))
  steps.append(Step('make_parallel_release.py', help="package parallel flat data"))

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
  parser.add_argument("--stop", "-p", type=int, default=len(steps)-1, help='step to stop at (inclusive)')
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

  rootdir = args.root
  language = args.language
  start = args.start
  stop = args.stop+1
  # patchups for step 0
  stepsbyname["unpack_lrlp.sh"].argstring="-l %s -r %s %s" % (language, rootdir, args.tarball)

  if start == 0:
    expdir = steps[0].run().strip()
    start+=1
  else:
    expdir = args.expdir

  # patchups for the rest
  if stop > 0:
    stepsbyname["get_tweet_by_id.rb"].progpath=os.path.join(expdir, 'tools', 'twitter-processing')
    stepsbyname["get_tweet_by_id.rb"].argstring=os.path.join(rootdir, language, 'tweet')
    stepsbyname["get_tweet_by_id.rb"].stdin= os.path.join(expdir, 'docs', 'twitter_info.tab')
    stepsbyname["get_tweet_by_id.rb"].stderr=os.path.join(rootdir, language, 'extract_tweet.err')

    stepsbyname["ltf2rsd.perl"].argstring=os.path.join(expdir, 'data', 'translation', 'from_'+language, 'eng')
    stepsbyname["ltf2rsd.perl"].progpath=os.path.join(expdir, 'tools', 'ltf2rsd')
    stepsbyname["ltf2rsd.perl"].stderr=os.path.join(rootdir, language, 'ltf2rsd.err')

    stepsbyname["extract_lexicon.py"].argstring="-i %s -o %s" % (os.path.join(expdir, 'data', 'lexicon', '*.xml'), os.path.join(rootdir, language, 'lexicon'))
    stepsbyname["extract_lexicon.py"].stderr=os.path.join(rootdir, language, 'extract_lexicon.err')
    psmpath = os.path.join(rootdir, language, 'psm.ann')
    stepsbyname["extract_psm_annotation.py"].argstring="-i %s -o %s" % (os.path.join(expdir, 'data', 'monolingual_text', 'zipped', '*.psm.zip'), psmpath)
    entitypath = os.path.join(rootdir, language, 'entity.ann')
    stepsbyname["extract_entity_annotation.py"].argstring="-r %s -o %s -et %s" % (expdir, entitypath, os.path.join(rootdir, language, 'tweet'))

    paralleldir = os.path.join(rootdir, language, 'parallel', 'extracted')
    stepsbyname["extract_parallel.py"].argstring="-r %s -o %s -s %s -et %s" % (expdir, paralleldir, language, os.path.join(rootdir, language, 'tweet'))
    stepsbyname["extract_parallel.py"].stderr=os.path.join(rootdir, language, 'extract_parallel.err')

    monodir = os.path.join(rootdir, language, 'mono','extracted')
    stepsbyname["extract_mono.py"].argstring="-i %s -o %s" % (os.path.join(expdir, 'data','monolingual_text','zipped','*.ltf.zip'), monodir)
    stepsbyname["extract_mono.py"].stderr=os.path.join(rootdir, language, 'extract_mono.err')

    stepsbyname["make_mono_release.py"].argstring="-r %s -o %s -l %s -c %s -a %s -p %s" % (monodir, os.path.join(rootdir, language, 'elisa.%s.y1r1.v1.xml' % language), language, ' '.join([re.sub('.manifest', '', f) for f in os.listdir(monodir) if re.match('(.+)\.manifest', f)]), entitypath, psmpath)
    stepsbyname["make_mono_release.py"].stderr=os.path.join(rootdir, language, 'make_mono_release.err')

    stepsbyname["make_parallel_release.py"].argstring="-r %s -o %s -l %s -c %s -a %s -p %s -e %s" % (paralleldir, os.path.join(rootdir, language, 'elisa.%s-eng.y1r1.v1.xml' % language), language, ' '.join([re.sub('.eng.manifest', '', f) for f in os.listdir(paralleldir) if re.match('(.+)\.eng.manifest', f)]), entitypath, psmpath, 'True')
    stepsbyname["make_parallel_release.py"].stderr=os.path.join(rootdir, language, 'make_parallel_release.err')

    for step in steps[start:stop]:
      step.run()
  print "Done. Expdir is "+expdir

if __name__ == '__main__':
  main()
