#!/usr/bin/env python3

import argparse
import sys
import codecs

from collections import defaultdict as dd
import re
import os.path
from lputil import Step, make_action, dirfind, mkdir_p
from subprocess import check_output, check_call, CalledProcessError
scriptdir = os.path.dirname(os.path.abspath(__file__))


def main():
  steps = []

  # extract_mono.py
  steps.append(Step('decrypt_sets.py',
                    help="decode encrypted sets"))

  # extract_mono.py
  steps.append(Step('extract_mono.py',
                    help="get flat form mono data"))

  # get_tweet_by_id.rb
  steps.append(Step('get_tweet_by_id.rb',
                    help="download tweets. must have twitter gem installed " \
                    "and full internet",
                    abortOnFail=False))
  # extract_mono_tweet.py
  steps.append(Step('extract_mono_tweet.py',
                    help="make twitter data look like regular mono data"))

  steps.append(Step('make_mono_release.py',
                    help="package mono flat data"))

  stepsbyname = {}
  for step in steps:
    stepsbyname[step.prog] = step

  parser = argparse.ArgumentParser(description="Build an eval IL monoset from LDC to elisa form",
                                   formatter_class= \
                                   argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--setdir", "-d", default='.',
                      help='name of set directory (i.e. set1, setE, etc.)')
  parser.add_argument("--language", "-l", default='uzb',
                      help='three letter code of IL language')
  parser.add_argument("--key", "-k", default=None,
                      help='decryption key for encrypted il')
  parser.add_argument("--expdir", "-e",
                      help='path to where the extraction is. If starting at ' \
                      'step 0 this is ignored')
  parser.add_argument("--root", "-r", default='/home/nlg-02/LORELEI/ELISA/data',
                      help='path to where the extraction will take place')
  parser.add_argument("--outfile", "-o", help='name of the output file')
  parser.add_argument("--start", "-s", type=int, default=0,
                      help='step to start at')
  parser.add_argument("--stop", "-p", type=int, default=len(steps)-1,
                      help='step to stop at (inclusive)')
  parser.add_argument("--liststeps", "-x", nargs=0, action=make_action(steps),
                      help='print step list and exit')
  parser.add_argument("--ruby", default="/opt/local/bin/ruby2.2", help='path to ruby (2.1 or higher)')

  try:
    args = parser.parse_args()
  except IOError as msg:
    parser.error(str(msg))

  rootdir = args.root
  language = args.language

  setdir = args.setdir
  outdir = os.path.join(rootdir, language, setdir)
  outfile = os.path.join(outdir, args.outfile)
  start = args.start
  stop = args.stop + 1

  if args.expdir is None:
    expdir = os.path.join(rootdir, language, 'expanded', 'lrlp')
  else:
    expdir = args.expdir

  mkdir_p(outdir)

  if args.key is None:
    stepsbyname["decrypt_sets.py"].disable()
  else:
    stepsbyname["decrypt_sets.py"].stderr=os.path.join(outdir, 'decrypt_sets.err')
    stepsbyname["decrypt_sets.py"].argstring="-r %s -k %s -s %s" % (expdir, args.key, setdir)
    stepsbyname["decrypt_sets.py"].run()
    start+=1
  # TWEET
  # LDC changed its mind again
  tweetprogpath = os.path.join(expdir, 'set0', 'tools', 'twitter-processing', 'bin')

  stepsbyname["get_tweet_by_id.rb"].progpath = tweetprogpath
  tweetdir = os.path.join(outdir, 'tweet')
  stepsbyname["get_tweet_by_id.rb"].argstring = tweetdir+" -l "+language
  tweetintab = os.path.join(expdir, setdir, 'docs', 'twitter_info.tab')
  if os.path.exists(tweetintab):
    stepsbyname["get_tweet_by_id.rb"].stdin = tweetintab
  else:
    stepsbyname["get_tweet_by_id.rb"].disable()
  tweeterr = os.path.join(outdir, 'extract_tweet.err')
  stepsbyname["get_tweet_by_id.rb"].stderr = tweeterr
  stepsbyname["get_tweet_by_id.rb"].scriptbin = args.ruby

  # # TODO: log tweets!

  # MONO
  monoindirs = dirfind(os.path.join(expdir, setdir, 'data', 'monolingual_text'), "%s.ltf.zip" % setdir)
  monooutdir = os.path.join(outdir, 'mono', 'extracted')
  monoerr = os.path.join(outdir, 'extract_mono.err')
  stepsbyname["extract_mono.py"].argstring = "--nogarbage -i %s -o %s" % \
    (' '.join(monoindirs), monooutdir)
  stepsbyname["extract_mono.py"].stderr = monoerr

  
  # since we package and extract all at once, use the ltf structure to declare the manifest names
  manfiles = [x for x in map(lambda y: '.'.join(os.path.basename(y).split('.')[:-2]), monoindirs)]


  # tweet 2 mono set here so that mono and tweet dirs are already established
  if stepsbyname["get_tweet_by_id.rb"].disabled:
    stepsbyname["extract_mono_tweet.py"].disable()
  else:
    stepsbyname["extract_mono_tweet.py"].argstring = "--nogarbage -i "+tweetdir+" -o "+monooutdir
    stepsbyname["extract_mono_tweet.py"].stderr = os.path.join(outdir, 'extract_mono_tweet.err')
    manfiles.append("tweets")
  
  # PACKAGE
  monoxml = outfile
  monostatsfile = outfile+".stats"
  manarg = ' '.join(manfiles)
  monoerr = os.path.join(outdir, 'make_mono_release.err')
  stepsbyname["make_mono_release.py"].argstring = "-r %s -l %s -c %s -s %s | gzip > %s" % \
                                                  (monooutdir, language, manarg, monostatsfile, monoxml)
  stepsbyname["make_mono_release.py"].stderr = monoerr

  for step in steps[start:stop]:
    step.run()

  print("Done.\nFile is %s" % outfile)


if __name__ == '__main__':
  main()
