#! /usr/bin/env python
import argparse
import sys
import codecs
from itertools import izip, cycle
from collections import defaultdict as dd
import re
import os.path
scriptdir = os.path.dirname(os.path.abspath(__file__))

# http://stackoverflow.com/questions/600268/mkdir-p-functionality-in-python
import os, errno
def mkdir_p(path):
  try:
    os.makedirs(path)
  except OSError as exc: # Python >2.5
    if exc.errno == errno.EEXIST and os.path.isdir(path):
      pass
    else: raise

def main():
  parser = argparse.ArgumentParser(description="Given category per doc, idfile, data file, put data in category-specific dir",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--catfile", "-c", nargs='?', type=argparse.FileType('r'), help="doc cat file (docid cat)")
  parser.add_argument("--idfile", "-d", nargs='?', type=argparse.FileType('r'), help="id file (docid per line)")
  parser.add_argument("--infile", "-i", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="input file")
  parser.add_argument("--prefix", "-p", default=".", help="directory prefix for categories")

  try:
    args = parser.parse_args()
  except IOError, msg:
    parser.error(str(msg))

  reader = codecs.getreader('utf8')
  writer = codecs.getwriter('utf8')
  catfile = reader(args.catfile)
  infile = reader(args.infile)
  idfile = reader(args.idfile)

  basefile = os.path.basename(args.infile.name)
  cats = {}
  fhs = {}
  for line in catfile:
    doc, cat = line.strip().split('\t')
    prefix = os.path.join(args.prefix, cat)
    catfile = os.path.join(prefix, basefile)
    if catfile not in fhs:      
      mkdir_p(prefix)
      fhs[catfile]=writer(open(catfile, 'w'))
    cats[doc]=fhs[catfile]

  for lid, (doc, data) in enumerate(izip(idfile, infile)):
    cats[doc.strip()].write(data)

if __name__ == '__main__':
  main()