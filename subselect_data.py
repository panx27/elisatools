#!/usr/bin/env python3

import argparse
import sys
import codecs

from collections import defaultdict as dd
import re
import os
import os.path
from lputil import mkdir_p
from subprocess import check_output, STDOUT, CalledProcessError
scriptdir = os.path.dirname(os.path.abspath(__file__))


def runselection(prefix, idfile, engfile, termfile, categories, remainder, sizes, filetypes, srclang, indir, outdir, devlstfile=None):
  ''' do a data selection and apply it to a set of files '''
  rankfile = os.path.join(outdir, "%s.ranks" % prefix)
  countfile = os.path.join(outdir, "%s.counts" % prefix)
  catfile = os.path.join(outdir, "%s.cats" % prefix)
  try:
    cmd_output=check_output("%s/rankdocuments.py -i %s -d %s -t %s -o %s" %
                            (scriptdir, engfile, idfile, termfile, rankfile), stderr=STDOUT, shell=True)
    cmd_output=check_output("%s/countwords.py -i %s -d %s -o %s" %
                            (scriptdir, engfile, idfile, countfile), stderr=STDOUT, shell=True)
    roundrobin_cmd = "%s/roundrobin.py -w %s -f %s -s %s -c %s -r %s -o %s" % \
                     (scriptdir, countfile, rankfile, sizes, categories, remainder, catfile)
    if devlstfile:
      print("receive specified dev set ids")
      roundrobin_cmd += ' -d %s' % (devlstfile)
    cmd_output=check_output(roundrobin_cmd, stderr=STDOUT, shell=True)
    print ((cmd_output).decode('utf-8'))
    for filetype in filetypes:
      if os.path.exists(os.path.join(indir, filetype)):
        for flang in [srclang, 'eng']:
          flatfile = os.path.join(indir, filetype, "%s.%s.%s.flat" % (prefix, filetype, flang))
          if not(os.path.exists(flatfile)):
            print("***Warning: %s does not exist so not selecting" % flatfile)
            continue
          cmd = "%s/categorize.py -i %s -d %s -c %s -p %s -P %s" % (scriptdir, flatfile, idfile, catfile, outdir, filetype)
          print("Running "+cmd)
          cmd_output=check_output(cmd, stderr=STDOUT, shell=True)
  except CalledProcessError as exc:
    print("Status : FAIL", exc.returncode, exc.output)
    sys.exit(1)
  return catfile

def main():
  parser = argparse.ArgumentParser(description="Make dataset selections for experimentation",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--indir", "-i", help="location of parallel data")
  parser.add_argument("--language", "-l", help="source language three digit code")
  parser.add_argument("--extractpath", "-e", default="filtered", help="location of extracted data (might want to use 'filtered')")
  parser.add_argument("--minimum", "-m", default=100, help="minimum number of words per subselection")
  parser.add_argument("--sizes", "-s", nargs='+', type=int, help="list of sizes desired in each category")
  parser.add_argument("--categories", "-c", nargs='+', help="list of categories. Must match sizes")
  parser.add_argument("--termfile", "-t", help="file of desired terms, one per line")
  parser.add_argument("--remainder", "-r", default="train", help="remainder category. Should be a new category")
  parser.add_argument("--devlstfile", "-d", default=None, help="file of desired documents for dev (subject to length constraints, must be a set called 'dev')")



  try:
    args = parser.parse_args()
  except IOError as msg:
    parser.error(str(msg))

#  reader = codecs.getreader('utf8')
#  writer = codecs.getwriter('utf8')
#  outfile = writer(args.outfile)

  indir = args.indir
  origsizes = args.sizes
  termfile = args.termfile

  # TODO: find these?
  # doc = keep full docs together  (can detect this by counting number of unique docs)
  docprefixes = ["fromsource.generic", "fromsource.tweet", "fromtarget.news", "found.generic"]
  nodocprefixes = ["fromtarget.elicitation", "fromtarget.phrasebook"]

  extractpath = os.path.join(indir, args.extractpath)
  #http://stackoverflow.com/questions/973473/getting-a-list-of-all-subdirectories-in-the-current-directory
  filetypes = [subdir for subdir in next(os.walk(extractpath))[1]]

  origpath = os.path.join(extractpath, 'original')
  outpath = os.path.join(indir, 'splits')
  mkdir_p(outpath)

  # number of words in each file
  fullsizes = {}
  adjsizes = {}
  sizesum = 0.0
  for preflist in [docprefixes, nodocprefixes]:
    for prefix in list(preflist):
      # don't deal with it more if there's nothing in the manifest
      manfile = os.path.join(extractpath, "%s.eng.manifest" % prefix)
      if (not os.path.exists(manfile)) or os.path.getsize(manfile) == 0:
        print("removing "+prefix)
        preflist.remove(prefix)
  for prefix in docprefixes+nodocprefixes:
    engfile=os.path.join(origpath, "%s.original.eng.flat" % prefix)
    prefsize = int(check_output("wc -w %s" % engfile, shell=True).decode('utf8').strip().split(' ')[0])
    fullsizes[prefix] = prefsize
    sizesum +=prefsize
  # adjust size split by proportion, with minimum
  for prefix in docprefixes+nodocprefixes:
    mult = fullsizes[prefix]/sizesum
    adjsizes[prefix] = [max(args.minimum, int(mult*x)) for x in origsizes]
    print(prefix,adjsizes[prefix])
  # doc-based processing
  catlist = ' '.join(args.categories)
  for prefix in docprefixes:
    idfile = os.path.join(outpath, "%s.ids" % prefix)
    manfile = os.path.join(extractpath, "%s.eng.manifest" % prefix)
    try:
      check_output("cut -f2 %s > %s" % (manfile, idfile), stderr=STDOUT, shell=True)
    except CalledProcessError as exc:
      print("Status : FAIL", exc.returncode, exc.output)
    engfile=os.path.join(origpath, "%s.original.eng.flat" % prefix)
    sizelist = ' '.join(map(str, adjsizes[prefix]))
    catfile = runselection(prefix, idfile, engfile, termfile, catlist, args.remainder, sizelist, filetypes, args.language, extractpath, outpath, args.devlstfile)
    for i in (args.language, 'eng'):
      manifest = os.path.join(extractpath, "%s.%s.manifest" % (prefix, i))
      cmd = "%s/categorize.py -i %s -d %s -c %s -p %s" % (scriptdir, manifest, idfile, catfile, outpath)
      print("Running "+cmd)
      check_output(cmd, stderr=STDOUT, shell=True)

  # nodoc-based processing
  for prefix in nodocprefixes:
    idfile = os.path.join(outpath, "%s.fakeids" % prefix)
    try:
      mansize = int(check_output("wc -l %s" % os.path.join(extractpath, "%s.eng.manifest" % prefix), shell=True).decode('utf8').strip().split(' ')[0])
      check_output("seq %d > %s" % (mansize, idfile), stderr=STDOUT, shell=True)
    except CalledProcessError as exc:
      print("Status : FAIL", exc.returncode, exc.output)
    engfile=os.path.join(origpath, "%s.original.eng.flat" % prefix)
    sizelist = ' '.join(map(str, adjsizes[prefix]))
    catfile = runselection(prefix, idfile, engfile, termfile, catlist, args.remainder, sizelist, filetypes, args.language, extractpath, outpath)
    for i in (args.language, 'eng'):
      manifest = os.path.join(extractpath, "%s.%s.manifest" % (prefix, i))
      cmd = "%s/categorize.py -i %s -d %s -c %s -p %s" % (scriptdir, manifest, idfile, catfile, outpath)
      print("Running "+cmd)
      check_output(cmd, stderr=STDOUT, shell=True)

  # warning if entries not found in given dev list
  if args.devlstfile:
    devlst = set(open(args.devlstfile).read().split())
    all_docids = list()
    for prefix in docprefixes:
      all_docids += open(os.path.join(outpath, "%s.ids" % prefix)).read().split('\n')
    for i in devlst - set(all_docids):
      print ("***Warning: docid not found: %s" % i)

if __name__ == '__main__':
  main()
