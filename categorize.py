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
  parser = argparse.ArgumentParser(description="Given category per doc and doc file, put data in category-specific dir",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--catfile", "-c", nargs='?', type=argparse.FileType('r'), help="doc cat file (docid cat)")
  parser.add_argument("--infile", "-i", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="input file (docid data)")
  parser.add_argument("--prefix", "-p", default=".", help="directory prefix for categories")

  try:
    args = parser.parse_args()
  except IOError, msg:
    parser.error(str(msg))

  reader = codecs.getreader('utf8')
  writer = codecs.getwriter('utf8')
  catfile = reader(args.catfile)
  infile = reader(args.infile)

  cats = {}
  basefile = os.path.basename(args.infile)
  for line in catfile:
    doc, cat = line.strip().split('\t')
    prefix = os.path.join(args.prefix, cat)
    mkdir_p(prefix)
    cats[doc]=writer(open(os.path.join(prefix, basefile), 'w'))

  for line in infile:
    doc, data = line.strip().split('\t')
    cats[doc].write(data+"\n")

if __name__ == '__main__':
  main()
