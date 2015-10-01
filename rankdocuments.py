#! /usr/bin/env python
import argparse
import sys
import codecs
from collections import defaultdict as dd
import re
import os.path
from heapq import heappush, heappop
scriptdir = os.path.dirname(os.path.abspath(__file__))


def getoverlap(terms, words):
  ''' get fraction of words that are also terms '''
  return (len(terms.intersection(words))+0.0)/len(words)

def main():
  parser = argparse.ArgumentParser(description="Rank documents by bag-of-words type overlap with triggers",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--infile", "-i", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="input file, presumed to be tab-sep docid, segment")
  parser.add_argument("--termfile", "-t", nargs='?', type=argparse.FileType('r'), help="term file, presumed to be one term per line")
  parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('w'), default=sys.stdout, help="output file")

  try:
    args = parser.parse_args()
  except IOError, msg:
    parser.error(str(msg))

  reader = codecs.getreader('utf8')
  writer = codecs.getwriter('utf8')
  infile = reader(args.infile)
  termfile = reader(args.termfile)
  outfile = writer(args.outfile)

  terms = set()
  docs = dd(set)
  for line in termfile:
    terms.add(line.strip().lower())
  for line in infile:
    doc, seg = line.strip().split('\t')
    docs[doc].update([x.lower() for x in seg.split()])
  scores = []
  for doc, words in docs.iteritems():
    heappush(scores, (-getoverlap(terms, words), doc))
  while len(scores) > 0:
    score, doc = heappop(scores)
    outfile.write("%s\t%f\n" % (doc, -score))


if __name__ == '__main__':
  main()
