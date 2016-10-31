#!/usr/bin/env python3

import argparse
import sys
import codecs

from collections import defaultdict as dd
import re
import os.path
from lputil import mkdir_p
from subprocess import check_output, STDOUT, CalledProcessError
scriptdir = os.path.dirname(os.path.abspath(__file__))


def runselection(prefix, idfile, categories, remainder, sizes, filetypes, srclang, indir, outdir, devlstfile=None, fromFront=True):
  ''' do a data selection and apply it to a set of files '''
  catfile = os.path.join(outdir, "%s.cats" % prefix)
  # read docs into uniq list
  docs = []
  with open(idfile) as fh:
    for line in fh:
      doc = line.strip()
      if len(docs)==0 or doc != docs[-1]:
        docs.append(doc)
  cats = [remainder,]*len(docs)
  currdoc = 0 if fromFront else -1
  inc = 1 if fromFront else -1
  try:
    for cat, size in zip(categories, sizes):
      for idx in range(size):
        cats[currdoc]=cat
        currdoc +=inc
  except IndexError as err:
    sys.stderr.write("not enough docs for declared categories; stopping in %s \n" % cat)
  # not the right way to handle devlst; but ok overkill i think
  if devlstfile is not None and "dev" in categories:
    devlst = set(open(args.devlstfile).read().split())
    for idx in range(len(docs)):
      if docs[idx] in devlst:
        cats[idx]="dev"
  with open(catfile, 'w') as fh:
    for tup in zip(docs, cats):
      fh.write("\t".join(tup)+"\n")

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
  return catfile


def addonoffarg(parser, arg, dest=None, default=True, help="TODO"):
  ''' add the switches --arg and --no-arg that set parser.arg to true/false, respectively'''
  group = parser.add_mutually_exclusive_group()
  dest = arg if dest is None else dest
  group.add_argument('--%s' % arg, dest=dest, action='store_true', default=default, help=help)
  group.add_argument('--no-%s' % arg, dest=dest, action='store_false', default=default, help="See --%s" % arg)

def main():
  parser = argparse.ArgumentParser(description="Deterministic subselect designed for nov 2016 uyghur evaluation: per-doc, from end",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--indir", "-i", help="location of parallel data")
  parser.add_argument("--language", "-l", help="source language three digit code")
  parser.add_argument("--extractpath", "-e", default="extracted", help="location of extracted data (might want to use 'filtered')")
  parser.add_argument("--sizes", "-s", nargs='+', type=int, help="list of sizes desired in each category")
  parser.add_argument("--categories", "-c", nargs='+', help="list of categories. Must match sizes")
  parser.add_argument("--remainder", "-r", default="train", help="remainder category. Should be a new category")
  parser.add_argument("--devlstfile", "-d", default=None, help="file of desired documents for dev (subject to length constraints, must be a set called 'dev')")
  addonoffarg(parser, 'fromFront', default=False, help="do doc assignment from the beginning (instead of the end)")


  try:
    args = parser.parse_args()
  except IOError as msg:
    parser.error(str(msg))

#  reader = codecs.getreader('utf8')
#  writer = codecs.getwriter('utf8')
#  outfile = writer(args.outfile)

  indir = args.indir
  origsizes = args.sizes


  # TODO: find these?
  # doc = keep full docs together  (can detect this by counting number of unique docs)
  # TODO: re-add found.generic to docprefixes
  docprefixes = ["fromsource.generic", "fromsource.tweet", "fromtarget.news"]
  # IL3: moving found.generic!!
  nodocprefixes = ["fromtarget.elicitation", "fromtarget.phrasebook", "found.generic"]

  # TODO: find these
  filetypes = ["morph", "morph-tokenized", "original", "pos", "tokenized", "mttok", "mttoklc", "agile-tokenized", "cdec-tokenized", "agile-tokenized.lc", "cdec-tokenized.lc"]

  extractpath = os.path.join(indir, args.extractpath)
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
    catfile = runselection(prefix, idfile, args.categories, args.remainder, origsizes, filetypes, args.language, extractpath, outpath, args.devlstfile, fromFront=args.fromFront)
    for i in (args.language, 'eng'):
      manifest = os.path.join(extractpath, "%s.%s.manifest" % (prefix, i))
      cmd = "%s/categorize.py -i %s -d %s -c %s -p %s -r %s" % (scriptdir, manifest, idfile, catfile, outpath, args.remainder)
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
    catfile = runselection(prefix, idfile, args.categories, args.remainder, origsizes, filetypes, args.language, extractpath, outpath, fromFront=args.fromFront)
    for i in (args.language, 'eng'):
      manifest = os.path.join(extractpath, "%s.%s.manifest" % (prefix, i))
      cmd = "%s/categorize.py -i %s -d %s -c %s -p %s -r %s" % (scriptdir, manifest, idfile, catfile, outpath, args.remainder)
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
