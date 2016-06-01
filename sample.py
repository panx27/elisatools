#!/usr/bin/env python3

# given file of line-segmented records, sample n of them.
# implements reservoir sampling -- efficient memory and runtime (one pass through data, memory O(sample)

# alg implementation borrowed from http://stackoverflow.com/questions/2612648/reservoir-sampling

import argparse
import sys
import os
import random
import codecs
if sys.version_info[0] == 2:
  from itertools import izip
else:
  izip = zip
from collections import defaultdict as dd
import re
import os.path
import gzip
scriptdir = os.path.dirname(os.path.abspath(__file__))


reader = codecs.getreader('utf8')
writer = codecs.getwriter('utf8')

def prepfile(fh, code):
  ret = gzip.open(fh.name, code if code.endswith("t") else code+"t") if fh.name.endswith(".gz") else fh
  if sys.version_info[0] == 2:
    if code.startswith('r'):
      ret = reader(fh)
    elif code.startswith('w'):
      ret = writer(fh)
    else:
      sys.stderr.write("I didn't understand code "+code+"\n")
      sys.exit(1)
  return ret

def main():
  parser = argparse.ArgumentParser(description="sample k records from file")
  parser.add_argument("--infile", "-i", type=argparse.FileType('r'), default=sys.stdin, help="input file")
  parser.add_argument("--outfile", "-o", type=argparse.FileType('w'), default=sys.stdout, help="output file")
  parser.add_argument("--remainderfile", "-r", type=argparse.FileType('w'), default=os.devnull, help="remainder (lines not sampled) file")
  parser.add_argument("--size", "-s", type=int, default=100, help="number of samples")

  try:
    args = parser.parse_args()
  except IOError as msg:
    parser.error(str(msg))
  infile = prepfile(args.infile, 'r')
  outfile = prepfile(args.outfile, 'w')
  remainderfile = prepfile(args.remainderfile, 'w')

  result = []
  N = 0
  K = args.size
  for item in infile:
    N += 1
    if len( result ) < K:
      result.append( item )
    else:
      s = int(random.random() * N)
      if s < K:
        remainderfile.write(result[s])
        result[s] = item
      else:
        remainderfile.write(item)
  if len(result) < K:
    sys.stderr.write("Warning: only %d items in input; you requested %d\n" % (len(result), K))
  for item in result:
    outfile.write(item)

if __name__ == '__main__':
  main()

