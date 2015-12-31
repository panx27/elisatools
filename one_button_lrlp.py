#! /usr/bin/env python
import argparse
import sys
import codecs
from itertools import izip
from collections import defaultdict as dd
import re
import os.path
from lputil import Step, make_action
from subprocess import check_output, check_call, CalledProcessError
scriptdir = os.path.dirname(os.path.abspath(__file__))


def main():
  steps = []
  # Put additional steps in here. Arguments, stdin/stdout, etc. get set below

  # unpack_lrlp.sh
  steps.append(Step('unpack_lrlp.sh', call=check_output,
                    help="untars lrlp into position for further processing"))

  # gather_ephemera.py
  steps.append(Step('gather_ephemera.py',
                    help="relocates assorted bits from lrlp"))

  # extract_lexicon.py
  steps.append(Step('extract_lexicon.py',
                    help="get flat form of bilingual lexicon"))
  # normalize_lexicon.py
  steps.append(Step('normalize_lexicon.py',
                    help="heuristically convert lexicon into something more machine readable"))

  # relocate lexicon
  steps.append(Step('cp', progpath='/bin',
                    help="move the lexicon stuff into ephemera"))

  # get_tweet_by_id.rb
  steps.append(Step('get_tweet_by_id.rb',
                    help="download tweets. must have twitter gem installed " \
                    "and full internet"))
  # ltf2rsd.perl
  steps.append(Step('ltf2rsd.perl',
                    help="get flat form of tweet translations",
                    abortOnFail=False))

  # extract_psm_annotation.py
  steps.append(Step('extract_psm_annotation.py',
                    help="get annotations from psm files into psm.ann",
                    abortOnFail=False))
  # extract_entity_annotation.py
  steps.append(Step('extract_entity_annotation.py',
                    help="get entity and other annotations into entity.ann",
                    abortOnFail=False))
  # extract_parallel.py
  steps.append(Step('extract_parallel.py',
                    help="get flat form parallel data"))
  # extract_mono.py
  steps.append(Step('extract_mono.py',
                    help="get flat form mono data"))

  stepsbyname = {}
  for step in steps:
    stepsbyname[step.prog] = step

  parser = argparse.ArgumentParser(description="Process a LRLP into flat format",
                                   formatter_class= \
                                   argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--tarball", "-t", default='lrlp.tar.gz',
                      help='path to gzipped tar for processing')
  parser.add_argument("--language", "-l", default='uzb',
                      help='three letter code of language')
  parser.add_argument("--root", "-r", default='/home/nlg-02/LORELEI/ELISA/data',
                      help='path to where the extraction will take place')
  parser.add_argument("--expdir", "-e",
                      help='path to where the extraction is. If starting at ' \
                      'step 0 this is ignored')
  parser.add_argument("--start", "-s", type=int, default=0,
                      help='step to start at')
  parser.add_argument("--stop", "-p", type=int, default=len(steps)-1,
                      help='step to stop at (inclusive)')
  parser.add_argument("--liststeps", "-x", nargs=0, action=make_action(steps),
                      help='print step list and exit')
  parser.add_argument("--ruby", default="/opt/local/bin/ruby2.2", help='path to ruby (2.1 or higher)')

  try:
    args = parser.parse_args()
  except IOError, msg:
    parser.error(str(msg))

  if args.expdir is not None and args.start <= 0:
    sys.stderr.write \
      ("Warning: expdir is set but will be ignored and determined dynamically")
  if args.expdir is None and args.start > 0:
    sys.stderr.write \
      ("Error: must explicitly set expdir if not starting at step 0")
    sys.exit(1)

  rootdir = args.root
  language = args.language
  start = args.start
  stop = args.stop + 1
  # Patchups for step 0
  stepsbyname["unpack_lrlp.sh"].argstring="-l %s -r %s %s" % \
    (language, rootdir, args.tarball)

  if start == 0:
    expdir = steps[0].run().strip()
    start += 1
  else:
    expdir = args.expdir

  # Patchups for the rest
  if stop > 0:
    # TWEET
    tweetprogpath = os.path.join(expdir, 'tools', 'twitter-processing')
    stepsbyname["get_tweet_by_id.rb"].progpath = tweetprogpath
    tweetdir = os.path.join(rootdir, language, 'tweet')
    stepsbyname["get_tweet_by_id.rb"].argstring = tweetdir+" -l "+language
    tweetintab = os.path.join(expdir, 'docs', 'twitter_info.tab')
    stepsbyname["get_tweet_by_id.rb"].stdin = tweetintab
    tweeterr = os.path.join(rootdir, language, 'extract_tweet.err')
    stepsbyname["get_tweet_by_id.rb"].stderr = tweeterr
    stepsbyname["get_tweet_by_id.rb"].scriptbin = args.ruby
    
    
    # EPHEMERA
    ephemdir = os.path.join(rootdir, language, 'ephemera')
    stepsbyname['gather_ephemera.py'].argstring = "-s %s -t %s" %\
                                                  (expdir, ephemdir)
    ephemerr = os.path.join(rootdir, language, 'gather_ephemera.err')
    stepsbyname['gather_ephemera.py'].stderr = ephemerr


    # LTF2RSD
    l2rindir = os.path.join(expdir, 'data', 'translation', 'from_'+language,
                            'eng') # Only converts from_SRC_tweet subdir
    stepsbyname["ltf2rsd.perl"].argstring = l2rindir
    # l2rprogpath = os.path.join(expdir, 'tools', 'ltf2txt')
    # stepsbyname["ltf2rsd.perl"].progpath = l2rprogpath
    l2rerr = os.path.join(rootdir, language, 'ltf2rsd.err')
    stepsbyname["ltf2rsd.perl"].stderr = l2rerr

    # LEXICON
    lexiconinfile = os.path.join(expdir, 'data', 'lexicon', '*.xml')
    lexiconoutdir = os.path.join(rootdir, language, 'lexicon')
    lexiconoutfile = os.path.join(lexiconoutdir, 'lexicon')
    lexiconnormoutfile = os.path.join(lexiconoutdir, 'lexicon.norm')

    lexiconerr = os.path.join(rootdir, language, 'extract_lexicon.err')
    lexiconnormerr = os.path.join(rootdir, language, 'normalize_lexicon.err')
    stepsbyname["extract_lexicon.py"].argstring = "-i %s -o %s" % \
                                                  (lexiconinfile, lexiconoutfile)
    stepsbyname["extract_lexicon.py"].stderr = lexiconerr

    stepsbyname["normalize_lexicon.py"].argstring = "-i %s -o %s" % \
                                                  (lexiconoutfile, lexiconnormoutfile)
    stepsbyname["normalize_lexicon.py"].stderr = lexiconnormerr


    stepsbyname["cp"].argstring = "-r %s %s" % (lexiconoutdir, ephemdir)

    # PSM
    psmindir = os.path.join(expdir, 'data', 'monolingual_text',
                            'zipped', '*.psm.zip')
    psmoutpath = os.path.join(rootdir, language, 'psm.ann')
    psmerr = os.path.join(rootdir, language, 'extract_psm_annotation.err')
    stepsbyname["extract_psm_annotation.py"].argstring = "-i %s -o %s" % \
                                                         (psmindir, psmoutpath)
    stepsbyname["extract_psm_annotation.py"].stderr = psmerr

    # ENTITY
    entityoutpath = os.path.join(rootdir, language, 'entity.ann')
    entityerr = os.path.join(rootdir, language, 'extract_entity_annotation.err')
    stepsbyname["extract_entity_annotation.py"].argstring="-r %s -o %s -et %s" \
      % (expdir, entityoutpath, tweetdir)
    stepsbyname["extract_entity_annotation.py"].stderr = entityerr

    # PARALLEL
    paralleloutdir = os.path.join(rootdir, language, 'parallel', 'extracted')
    parallelerr = os.path.join(rootdir, language, 'extract_parallel.err')
    stepsbyname["extract_parallel.py"].argstring="-r %s -o %s -s %s -et %s" % \
      (expdir, paralleloutdir, language, tweetdir)
    stepsbyname["extract_parallel.py"].stderr = parallelerr

    # MONO
    monoindir = os.path.join(expdir, 'data', 'monolingual_text',
                             'zipped', '*.ltf.zip')
    monooutdir = os.path.join(rootdir, language, 'mono', 'extracted')
    monoerr = os.path.join(rootdir, language, 'extract_mono.err')
    stepsbyname["extract_mono.py"].argstring = "-i %s -o %s" % \
      (monoindir, monooutdir)
    stepsbyname["extract_mono.py"].stderr = monoerr

    for step in steps[start:stop]:
      step.run()


  print "Done.\nExpdir is %s" % expdir

if __name__ == '__main__':
  main()
