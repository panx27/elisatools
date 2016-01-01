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

def main():
  parser = argparse.ArgumentParser(description="Given category per doc, idfile, data file, put data in category-specific dir",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--catfile", "-c", nargs='?', type=argparse.FileType('r'), help="doc cat file (docid cat)")
  parser.add_argument("--idfile", "-d", nargs='?', type=argparse.FileType('r'), help="id file (docid per line)")
  parser.add_argument("--infile", "-i", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="input file")
  parser.add_argument("--prefix", "-p", default=".", help="directory prefix for categories")
  parser.add_argument("--postfix", "-P", default=".", help="directory postfix after categories")
  parser.add_argument("--remainder", "-r", default="train", help="remainder category. Should match previous remainder category")

  try:
    args = parser.parse_args()
  except IOError as msg:
    parser.error(str(msg))

  catfile = args.catfile
  infile =  args.infile
  idfile =  args.idfile

  basefile = os.path.basename(args.infile.name)
  cats = {}
  fhs = {}
  for line in catfile:
    doc, cat = line.strip().split('\t')
    prefix = os.path.join(args.prefix, cat, args.postfix)
    innercatfile = os.path.join(prefix, basefile)
    if innercatfile not in fhs:      
      mkdir_p(prefix)
      fhs[innercatfile]=open(innercatfile, 'w')
    cats[doc]=fhs[innercatfile]
  remcatpref = os.path.join(args.prefix, args.remainder, args.postfix)
  remaindercatfile = os.path.join(remcatpref, basefile)
  if remaindercatfile not in fhs:
    mkdir_p(remcatpref)
    fhs[remaindercatfile]=open(remaindercatfile, 'w')
    
  for doc, data in zip(idfile, infile):
    doc = doc.strip()
    fh = cats[doc] if doc in cats else fhs[remaindercatfile]
    fh.write(data)

if __name__ == '__main__':
  main()
