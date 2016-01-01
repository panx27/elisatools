#!/usr/bin/env python3

import argparse
import sys
import codecs

from collections import defaultdict as dd
import re
import os.path
scriptdir = os.path.dirname(os.path.abspath(__file__))


def main():
  parser = argparse.ArgumentParser(description="Given LRLP lexicon flat representation attempt to normalize it to short phrase form",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--infile", "-i", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="input lexicon file")
  parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('w'), default=sys.stdout, help="output instruction file")
  parser.add_argument("--nosplit", "-n", action='store_true', default=False, help="don't split target on commas/semicolons/or/slash")
  parser.add_argument("--targetlimit", "-l", type=int, default=4, help="maximum length of target entry after splitting")
  parser.add_argument("--earlytargetlimit", "-L", type=int, default=20, help="maximum length of target entry before splitting")


  try:
    args = parser.parse_args()
  except IOError as msg:
    parser.error(str(msg))

  infile = args.infile
  outfile = args.outfile
  stderr = sys.stderr


  bad = 0
  tmword = 0
  smword = 0
  wrote = 0
  for line in infile:
#    outfile.write("ORIG: "+line)
    try:
      src, pos, trgs = line.lstrip().rstrip().split("\t")
    except:
      stderr.write("Bad line: "+line)
      bad+=1
      continue
    src = src.lower()
    trgs = trgs.lower()
    if len(trgs.split()) > args.earlytargetlimit:
      tmword+=1
      continue
    src = re.sub(r'\([^\(\)]+\)', '', src).split()
    # src singletons only
    if len(src) != 1:
      smword+=1
      continue
    src = src[0].lower()
    # get rid of parentheticals and split on commas or semicolons
    trgs = re.sub(r'\(.*\)', '', trgs) # harsh parenthetical stripping
    trgs = re.sub(r'e\.g\..*', '', trgs) # e.g. comes before garbage
    trgs = [trgs, ] if args.nosplit else re.split(r'[;,/]| or ', trgs)
    for trg in trgs:
      trg = trg.strip()
      if len(trg) == 0:
        continue
      # nothing too long
      if len(trg.split()) > args.targetlimit:
        tmword+=1
        continue
      # OTHER HEURISTICS...
      outfile.write("%s\t%s\t%s\n" % (src, pos, trg))
      wrote +=1
  stderr.write("%d bad %d source mword %d target mword %d wrote\n" % (bad, smword, tmword, wrote))
if __name__ == '__main__':
  main()

