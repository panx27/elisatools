#!/usr/bin/env python3

import argparse
import sys
import codecs

from collections import defaultdict as dd
import re
import os.path
from lputil import Step, make_action, dirfind
from subprocess import check_output, check_call, CalledProcessError
scriptdir = os.path.dirname(os.path.abspath(__file__))


def main():
  steps = []

  # unpack_lrlp.sh
  steps.append(Step('unpack_lrlp.sh', call=check_output,
                    help="untars lrlp into position for further processing"))

  # extract_mono.py
  steps.append(Step('extract_mono.py',
                    help="get flat form mono data"))

    # get_tweet_by_id.rb
  steps.append(Step('get_tweet_by_id.rb',
                    help="download tweets. must have twitter gem installed " \
                    "and full internet",
                    abortOnFail=False))

  # steps.append(Step('make_mono_release.py',
  #                   help="package mono flat data"))

  stepsbyname = {}
  for step in steps:
    stepsbyname[step.prog] = step

  parser = argparse.ArgumentParser(description="Build an eval IL monoset from LDC to elisa form",
                                   formatter_class= \
                                   argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--tarball", "-t", default='lrlp.tar.gz',
                      help='path to gzipped tar for processing')
  parser.add_argument("--setdir", "-d", default='.',
                      help='name of set directory (i.e. set1, setE, etc.)')
  parser.add_argument("--language", "-l", default='uzb',
                      help='three letter code of IL language')
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

  if args.expdir is not None and args.start <= 0:
    sys.stderr.write \
      ("Warning: expdir is set but will be ignored and determined dynamically")
  if args.expdir is None and args.start > 0:
    sys.stderr.write \
      ("Error: must explicitly set expdir if not starting at step 0")
    sys.exit(1)

  rootdir = args.root
  language = args.language
  outfile = args.outfile
  setdir = args.setdir
  start = args.start
  stop = args.stop + 1
  stepsbyname["unpack_lrlp.sh"].argstring="-l %s -r %s %s" % \
    (language, rootdir, args.tarball)

  if start == 0:
    expdir = steps[0].run().strip().decode("utf-8")
    start += 1
  else:
    expdir = args.expdir

  # Patchups for the rest
  if stop > 0:

    # TWEET
    tweetprogpath = os.path.join(expdir, 'set0', 'tools', 'twitter-processing')
    stepsbyname["get_tweet_by_id.rb"].progpath = tweetprogpath
    tweetdir = os.path.join(rootdir, language, 'tweet')
    stepsbyname["get_tweet_by_id.rb"].argstring = tweetdir+" -l "+language
    tweetintab = os.path.join(expdir, setdir, 'docs', 'twitter_info.tab')
    if os.path.exists(tweetintab):
      stepsbyname["get_tweet_by_id.rb"].stdin = tweetintab
    else:
      stepsbyname["get_tweet_by_id.rb"].disable()
    tweeterr = os.path.join(rootdir, language, 'extract_tweet.err')
    stepsbyname["get_tweet_by_id.rb"].stderr = tweeterr
    stepsbyname["get_tweet_by_id.rb"].scriptbin = args.ruby

    # TODO: log tweets!

    # MONO
    monoindirs = dirfind(os.path.join(expdir, setdir, 'data', 'monolingual_text'), "%s_ltf.zip" % setdir)
    print(monoindirs)
    monooutdir = os.path.join(rootdir, language, setdir, 'mono', 'extracted')
    print(monooutdir)
    monoerr = os.path.join(rootdir, language, 'extract_mono.err')
    stepsbyname["extract_mono.py"].argstring = "-i %s -o %s" % \
      (' '.join(monoindirs), monooutdir)
    stepsbyname["extract_mono.py"].stderr = monoerr

    # # PACKAGE
    # monoxml = os.path.join(rootdir, outfile)
    # monostatsfile = os.path.join(rootdir, outfile+".stats")

    # manarg = ' '.join([re.sub('.manifest', '', f) for f in os.listdir \
    #                    (monooutdir)if re.match('(.+)\.manifest', f)])
    # monoerr = os.path.join(rootdir, 'make_mono_release.err')
    # stepsbyname["make_mono_release.py"].argstring = "-r %s -l %s -c %s -s %s | gzip > %s" % \
    #                                                 (monooutdir, language, manarg, monostatsfile, monoxml)
    # stepsbyname["make_mono_release.py"].stderr = monoerr

    for step in steps[start:stop]:
      step.run()

  print("Done.\nExpdir is %s" % expdir)


if __name__ == '__main__':
  main()
