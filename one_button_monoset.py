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


  # get_tweet_by_id.rb
  steps.append(Step('get_tweet_by_id.rb',
                    help="download tweets. must have twitter gem installed " \
                    "and full internet",
                    abortOnFail=False))

  steps.append(Step('ldc_tok.py',
                    help="run ldc tokenizer on tweets ",
                    abortOnFail=False))

  # extract_mono.py
  steps.append(Step('extract_mono.py',
                    help="get flat form mono data"))

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
  parser.add_argument("--notweets", "-n", action='store_true', default=None,
                      help='do not include tweets (for eval IL setE only)')
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
  monodir=os.path.join(expdir, setdir, 'data', 'monolingual_text')
  monoindirs = dirfind(monodir, "%s.ltf.zip" % setdir)

  # TWEET
  tweetintab = os.path.join(expdir, setdir, 'docs', 'twitter_info.tab')
  notweetsinmono = True
  if args.notweets or not os.path.exists(tweetintab):
    print("disabling twitter stuff; tweets in regular mono ok")
    notweetsinmono = False
    stepsbyname["get_tweet_by_id.rb"].disable()
    stepsbyname["ldc_tok.py"].disable()
  else:
    print("not disabling twitter stuff; look at {}; avoiding tweets in regular mono".format(tweetintab))
    stepsbyname["get_tweet_by_id.rb"].stdin = tweetintab
    tweetprogpaths = []
    #    for toolroot in (os.path.join(expdir, 'set0'), scriptdir): # bad ldc tools for eval
    for toolroot in (scriptdir, ):
      tweetprogpaths = dirfind(os.path.join(toolroot, 'tools'), 'get_tweet_by_id.rb')
      if len(tweetprogpaths) > 0:
        break
    if len(tweetprogpaths) == 0:
      sys.stderr.write("Can't find get_tweet_by_id.rb\n")
      sys.exit(1)
    else:
      tweetprogpath = os.path.dirname(tweetprogpaths[0])
    tweetdir = os.path.join(outdir, 'tweet', 'rsd')

    stepsbyname["get_tweet_by_id.rb"].progpath = tweetprogpath
    mkdir_p(tweetdir)
    stepsbyname["get_tweet_by_id.rb"].argstring = tweetdir+" -l "+language


    tweeterr = os.path.join(outdir, 'extract_tweet.err')
    stepsbyname["get_tweet_by_id.rb"].stderr = tweeterr
    stepsbyname["get_tweet_by_id.rb"].scriptbin = args.ruby

        # TOKENIZE AND RELOCATE TWEETS
    # find rb location, params file
    toxexecpaths = []
    thetoolroot = None
    for toolroot in (expdir, scriptdir):
      tokexecpaths = dirfind(os.path.join(toolroot, 'tools'), 'token_parse.rb')
      if len(tokexecpaths) > 0:
        thetoolroot = toolroot
        break
    if len(tokexecpaths) == 0:
      sys.stderr.write("Can't find token_parse.rb\n")
      sys.exit(1)
    tokexec = tokexecpaths[0]
    tokparamopts = dirfind(os.path.join(thetoolroot, 'tools'), 'yaml')
    tokparam = "--param {}".format(tokparamopts[0]) if len(tokparamopts) > 0 else ""
    # ugly: the base of the file monodir/mononame.zip; need to add it to monoindirs and just pass that base so it gets constructed
    mononame = "tweets.ltf"
    monoindirs.append(os.path.join(monodir, mononame+".zip"))
    stepsbyname["ldc_tok.py"].argstring = "--mononame {mononame} -m {monodir} --ruby {ruby} --dldir {tweetdir} --exec {tokexec} {tokparam} --outfile {outfile}".format(
      mononame=mononame,
      monodir=monodir,
      ruby=args.ruby,
      tweetdir=tweetdir,
      tokexec=tokexec,
      tokparam=tokparam,
      outfile=os.path.join(rootdir, language, 'ldc_tok.stats'))
    stepsbyname["ldc_tok.py"].stderr = os.path.join(rootdir, language, 'ldc_tok.err')

  # # TODO: log tweets!

  # MONO

  monooutdir = os.path.join(outdir, 'mono', 'extracted')
  monoerr = os.path.join(outdir, 'extract_mono.err')
  stepsbyname["extract_mono.py"].argstring = "--no-cdec --nogarbage -i %s -o %s" % \
    (' '.join(monoindirs), monooutdir)
  if notweetsinmono:
    stepsbyname["extract_mono.py"].argstring += " --removesn"
  stepsbyname["extract_mono.py"].stderr = monoerr

  
  # since we package and extract all at once, use the ltf structure to declare the manifest names
  manfiles = [x for x in map(lambda y: '.'.join(os.path.basename(y).split('.')[:-2]), monoindirs)]


  # tweet 2 mono set here so that mono and tweet dirs are already established
  # if stepsbyname["get_tweet_by_id.rb"].disabled:
  #   stepsbyname["extract_mono_tweet.py"].disable()
  # else:
  #   stepsbyname["extract_mono_tweet.py"].argstring = "--nogarbage -i "+tweetdir+" -o "+monooutdir
  #   stepsbyname["extract_mono_tweet.py"].stderr = os.path.join(outdir, 'extract_mono_tweet.err')
  #   manfiles.append("tweets")
  
  # PACKAGE
  monoxml = outfile
  monostatsfile = outfile+".stats"
  manarg = ' '.join(manfiles)
  monoerr = os.path.join(outdir, 'make_mono_release.err')
  stepsbyname["make_mono_release.py"].argstring = "--no-ext -r %s -l %s -c %s -s %s | gzip > %s" % \
                                                  (monooutdir, language, manarg, monostatsfile, monoxml)
  stepsbyname["make_mono_release.py"].stderr = monoerr

  for step in steps[start:stop]:
    step.run()

  print("Done.\nFile is %s" % outfile)


if __name__ == '__main__':
  main()
