#!/usr/bin/env python3

import argparse
import sys
import codecs
from itertools import cycle
from collections import defaultdict as dd
import re
import os.path
from lputil import mkdir_p
scriptdir = os.path.dirname(os.path.abspath(__file__))

def addonoffarg(parser, arg, dest=None, default=True, help="TODO"):
  ''' add the switches --arg and --no-arg that set parser.arg to true/false, respectively'''
  group = parser.add_mutually_exclusive_group()
  dest = arg if dest is None else dest
  group.add_argument('--%s' % arg, dest=dest, action='store_true', default=default, help=help)
  group.add_argument('--no-%s' % arg, dest=dest, action='store_false', default=default, help="See --%s" % arg)

def backup(inp):
  ''' LDC universal document id (May 2017 edition): 9 character sequence at end of underscore-separated filename (after stripping any period-type extensions) '''
  cand = os.path.basename(inp).split('.')[0].split('_')[-1]
  if cand is not None and len(cand) == 9:
    return cand
  return inp
  
def main():
  parser = argparse.ArgumentParser(description="Given category per doc, idfile, data file, put data in category-specific dir",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--catfile", "-c", nargs='?', type=argparse.FileType('r'), help="doc cat file (docid cat)")
  parser.add_argument("--idfile", "-d", nargs='?', type=argparse.FileType('r'), help="id file (docid per line)")
  parser.add_argument("--infile", "-i", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="input file")
  parser.add_argument("--prefix", "-p", default=".", help="directory prefix for categories")
  parser.add_argument("--postfix", "-P", default=".", help="directory postfix after categories")
  parser.add_argument("--remainder", "-r", default="train", help="remainder category. Should match previous remainder category")
  addonoffarg(parser, 'backup', help="backup matches to universal docid, following strict ldc format (in May 2017)", default=True)
  
  try:
    args = parser.parse_args()
  except IOError as msg:
    parser.error(str(msg))

  catfile = args.catfile
  infile =  args.infile
  idfile =  args.idfile

  # the unsplit resource
  # e.g. base of tmp_170502/yor/parallel/filtered/agile-tokenized/fromsource.generic.agile-tokenized.eng.flat
  basefile = os.path.basename(args.infile.name)
  cats = {}
  backupcats = {}
  fhs = {}
  backupcount=0
  for line in catfile:
    # for each document, what category it belongs in
    # e.g. YOR_WL_001975_20150409_G0021WWLJ.eng	test
    doc, cat = line.strip().split('\t')
    # the prefix of the files that will be created
    # e.g. tmp_170502/yor/parallel/split / test / agile-tokenized
    prefix = os.path.join(args.prefix, cat, args.postfix)
    # the file that will be created
    # e.g. tmp_170502/yor/parallel/split/test/agile-tokenized/fromsource.generic.agile-tokenized.eng.flat
    innercatfile = os.path.join(prefix, basefile)
    if innercatfile not in fhs:      
      mkdir_p(prefix)
      fhs[innercatfile]=open(innercatfile, 'w')
    # doc -> file to write to
    cats[doc]=fhs[innercatfile]
    if args.backup:
      backupcats[backup(doc)]=fhs[innercatfile]
  # catchall remainder file
  remcatpref = os.path.join(args.prefix, args.remainder, args.postfix)
  remaindercatfile = os.path.join(remcatpref, basefile)
  if remaindercatfile not in fhs:
    mkdir_p(remcatpref)
    fhs[remaindercatfile]=open(remaindercatfile, 'w')
  # pairs of docids and lines
  # e.g. YOR_DF_001261_20031127_G0022DCKG.eng LESBIANISM IN NIGERIA IS A BIG SURPRISE 
  for doc, data in zip(idfile, infile):
    doc = doc.strip()
    if doc in cats:
      fh = cats[doc]
    elif backup(doc) in backupcats:
      fh = backupcats[backup(doc)]
      backupcount+=1
    else:
      fh = fhs[remaindercatfile]
    fh.write(data)
  if args.backup and backupcount > 0:
    sys.stderr.write("{} lines written via backup retrieval\n".format(backupcount))

if __name__ == '__main__':
  main()
