#!/usr/bin/env python3

import argparse
import sys
import codecs

from collections import defaultdict as dd
import re
import os
import os.path
from lputil import mkdir_p, touch
from subprocess import check_output, STDOUT, CalledProcessError
from shutil import copy
scriptdir = os.path.dirname(os.path.abspath(__file__))

def runselection(prefix, idfile, catfile, remainder, filetypes, srclang, indir, outdir):
  ''' apply a previous data selection to a set of files '''
  try:
    for filetype in filetypes:
      if os.path.exists(os.path.join(indir, filetype)):
        for flang in [srclang, 'eng']:
          flatfile = os.path.join(indir, filetype, "%s.%s.%s.flat" % (prefix, filetype, flang))
          if not(os.path.exists(flatfile)):
            print("***Warning: %s does not exist so not selecting" % flatfile)
            continue
          cmd = "%s/categorize.py -i %s -d %s -c %s -p %s -P %s -r %s" % (scriptdir, flatfile, idfile, catfile, outdir, filetype, remainder)
          print("Running "+cmd)
          cmd_output=check_output(cmd, stderr=STDOUT, shell=True)
  except CalledProcessError as exc:
    print("Status : FAIL", exc.returncode, exc.output)
    sys.exit(1)


def main():
  parser = argparse.ArgumentParser(description="Make dataset selections for experimentation given previously generated categorization files",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--indir", "-i", help="location of parallel data")
  parser.add_argument("--language", "-l", help="source language three digit code")
  parser.add_argument("--extractpath", "-e", default="filtered", help="location of extracted data (might want to use 'filtered')")
  parser.add_argument("--remainder", "-r", default="train", help="remainder category. Should match previous remainder category")
  parser.add_argument("--previous", "-p", help="location of previous cat files")



  try:
    args = parser.parse_args()
  except IOError as msg:
    parser.error(str(msg))

#  reader = codecs.getreader('utf8')
#  writer = codecs.getwriter('utf8')
#  outfile = writer(args.outfile)

  indir = args.indir
  # TODO: find these?
  # doc = keep full docs together  (can detect this by counting number of unique docs)
  # TODO: re-add found.generic to docprefixes
  docprefixes = ["fromsource.generic", "fromsource.tweet", "fromtarget.news", "found.generic"]
  nodocprefixes = ["fromtarget.elicitation", "fromtarget.phrasebook"]


  extractpath = os.path.join(indir, args.extractpath)

  #http://stackoverflow.com/questions/973473/getting-a-list-of-all-subdirectories-in-the-current-directory
  filetypes = [subdir for subdir in next(os.walk(extractpath))[1]]

  origpath = os.path.join(extractpath, 'original')
  outpath = os.path.join(indir, 'splits')
  mkdir_p(outpath)

  for preflist in [docprefixes, nodocprefixes]:
    for prefix in list(preflist):
      # don't deal with it more if there's nothing in the manifest
      manfile = os.path.join(extractpath, "%s.eng.manifest" % prefix)
      if (not os.path.exists(manfile)) or os.path.getsize(manfile) == 0:
        print("removing "+prefix)
        preflist.remove(prefix)
  # doc-based processing
  for prefix in docprefixes:
    idfile = os.path.join(outpath, "%s.ids" % prefix)
    manfile = os.path.join(extractpath, "%s.eng.manifest" % prefix)
    try:
      check_output("cut -f2 %s > %s" % (manfile, idfile), stderr=STDOUT, shell=True)
    except CalledProcessError as exc:
      print("Status : FAIL", exc.returncode, exc.output)
    catfile = os.path.join(args.previous, "%s.cats" % prefix)
    newcatfile = os.path.join(outpath, os.path.basename(catfile))
    if os.path.exists(catfile):
      copy(catfile, newcatfile)
    else:
      touch(newcatfile)
    runselection(prefix, idfile, newcatfile, args.remainder, filetypes, args.language, extractpath, outpath)
    for i in (args.language, 'eng'):
      manifest = os.path.join(extractpath, "%s.%s.manifest" % (prefix, i))
      cmd = "%s/categorize.py -i %s -d %s -c %s -p %s -r %s" % (scriptdir, manifest, idfile, newcatfile, outpath, args.remainder)
      print("Running "+cmd)
      check_output(cmd, stderr=STDOUT, shell=True)

  # nodoc-based processing

  for prefix in nodocprefixes:
    idfile = os.path.join(outpath, "%s.fakeids" % prefix)
    try:
      mansize = int(check_output("wc -l %s" % os.path.join(extractpath, "%s.eng.manifest" % prefix), shell=True).decode('utf-8').strip().split(' ')[0])
      check_output("seq %d > %s" % (mansize, idfile), stderr=STDOUT, shell=True)
    except CalledProcessError as exc:
      print("Status : FAIL", exc.returncode, exc.output)
    catfile = os.path.join(args.previous, "%s.cats" % prefix)
    newcatfile = os.path.join(outpath, os.path.basename(catfile))
    if os.path.exists(catfile):
      copy(catfile, newcatfile)
    else:
      touch(newcatfile)
    runselection(prefix, idfile, newcatfile, args.remainder, filetypes, args.language, extractpath, outpath)
    for i in (args.language, 'eng'):
      manifest = os.path.join(extractpath, "%s.%s.manifest" % (prefix, i))
      cmd = "%s/categorize.py -i %s -d %s -c %s -p %s -r %s" % (scriptdir, manifest, idfile, newcatfile, outpath, args.remainder)
      print("Running "+cmd)
      check_output(cmd, stderr=STDOUT, shell=True)

if __name__ == '__main__':
  main()
