#! /usr/bin/env python
import argparse
import sys
import codecs
from collections import defaultdict as dd
import re
import os.path
from heapq import heappush, heappop
scriptdir = os.path.dirname(os.path.abspath(__file__))



def main():
  parser = argparse.ArgumentParser(description="Given tab-sep docid, segment, show doc wordcount",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--infile", "-i", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="input file, presumed to be tab-sep docid, segment")
  parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('w'), default=sys.stdout, help="output file")

  try:
    args = parser.parse_args()
  except IOError, msg:
    parser.error(str(msg))

  reader = codecs.getreader('utf8')
  writer = codecs.getwriter('utf8')
  infile = reader(args.infile)
  outfile = writer(args.outfile)

  docs = dd(int)
  for line in infile:
    doc, seg = line.strip().split('\t')
    docs[doc]+=len(seg.split())
  for doc, count in docs.iteritems():
    outfile.write("%s\t%d\n" % (doc, count))


if __name__ == '__main__':
  main()
