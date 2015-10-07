#! /usr/bin/env python
import argparse
import sys
import codecs
from itertools import izip, cycle
from collections import defaultdict as dd
import re
import os.path
scriptdir = os.path.dirname(os.path.abspath(__file__))

# NOTE: always round robins into remainder. Should there be an option to not do this?

def main():
  parser = argparse.ArgumentParser(description="Given word counts and preferred order and distributions, assign documents to categories",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--wcfile", "-w", nargs='?', type=argparse.FileType('r'), help="word count file (docid count)")
  parser.add_argument("--filelist", "-f", nargs='?', type=argparse.FileType('r'), help="documents in order of distribution, possibly with other information")
  parser.add_argument("--sizes", "-s", nargs='+', type=int, help="list of sizes desired in each category")
  parser.add_argument("--categories", "-c", nargs='+', help="list of categories. Must match sizes")
  parser.add_argument("--remainder", "-r", default="train", help="remainder category. Should be a new category")
  parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('w'), default=sys.stdout, help="docid category")



  try:
    args = parser.parse_args()
  except IOError, msg:
    parser.error(str(msg))

  reader = codecs.getreader('utf8')
  writer = codecs.getwriter('utf8')
  wcfile = reader(args.wcfile)
  filelist = reader(args.filelist)
  outfile = writer(args.outfile)

  counts = {}
  for line in wcfile:
    word, count = line.strip().split('\t')
    counts[word]=int(count)

  files = []
  for line in filelist:
    files.append(line.strip().split()[0])
  if len(args.sizes) != len(args.categories):
    raise Exception("Sizes and categories must be same dimension")
  data = {}
  for cat, size in zip(args.categories, args.sizes):
    data[cat] = {"LEFT":size, "SET":[]}
  data[args.remainder] = {"LEFT":float("inf"), "SET":[]}

  for cat in cycle(data.keys()):
    if len(files) == 0:
      break
    if data[cat]["LEFT"] >= counts[files[0]]:
      doc = files.pop(0)
      data[cat]["SET"].append(doc)
      data[cat]["LEFT"]-=counts[doc]

  for cat in data.keys():
    sys.stderr.write("%s %f\n" % (cat, data[cat]["LEFT"]))
    for doc in data[cat]["SET"]:
      outfile.write("%s\t%s\n" % (doc, cat)) 

if __name__ == '__main__':
  main()
