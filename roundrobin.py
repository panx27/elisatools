#!/usr/bin/env python3

import argparse
import sys
import codecs
from itertools import cycle
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
  parser.add_argument("--devlstfile", "-d", default=None, help="file of desired documents for dev (subject to length constraints, must be a set called 'dev')")



  try:
    args = parser.parse_args()
  except IOError as msg:
    parser.error(str(msg))

  wcfile =   args.wcfile
  filelist = args.filelist
  outfile =  args.outfile
  if args.devlstfile:
    devlst = open(args.devlstfile).read().split()
  else:
    devlst = list()

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

  # select specified dev docids
  added_devlst = list()
  if 'dev' in args.categories and devlst:
    for doc in devlst:
      if doc in files:
        if data['dev']["LEFT"] >= counts[doc]:
          data[cat]["SET"].append(doc)
          data[cat]["LEFT"]-=counts[doc]
          files.remove(doc)
          added_devlst.append(doc)
  for doc in added_devlst:
    sys.stderr.write("Added dev docid: %s \n" % (doc))

  for cat in cycle(list(data.keys())):
    if len(files) == 0:
      break
    if data[cat]["LEFT"] >= counts[files[0]]:
      doc = files.pop(0)
      data[cat]["SET"].append(doc)
      data[cat]["LEFT"]-=counts[doc]

  for cat in list(data.keys()):
    sys.stderr.write("%s %f\n" % (cat, data[cat]["LEFT"]))
    for doc in data[cat]["SET"]:
      outfile.write("%s\t%s\n" % (doc, cat))


if __name__ == '__main__':
  main()
