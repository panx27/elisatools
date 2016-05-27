#!/usr/bin/env python3
import argparse
import sys
import codecs
if sys.version_info[0] == 2:
  from itertools import izip
else:
  izip = zip
from collections import defaultdict as dd
import re
import os.path
import gzip
import os
import glob
import numpy as np
from lputil import mkdir_p
import unicodedata as ud
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


def iscontrol(line):
  ''' does this line contain control characters? '''
  return "C" in set(map(lambda x: x[0], map(ud.category, list(line))))

def main():
  parser = argparse.ArgumentParser(description="filter a file into lines with and lines without control characters",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--infile", "-i", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="input file")
  parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('w'), default=sys.stdout, help="output file (no control chars)")
  parser.add_argument("--rejectfile", "-r", nargs='?', type=argparse.FileType('w'), default=os.devnull, help="output file (control chars)")

  try:
    args = parser.parse_args()
  except IOError as msg:
    parser.error(str(msg))

  infile = prepfile(args.infile, 'r')
  outfile = prepfile(args.outfile, 'w')
  rejectfile = prepfile(args.rejectfile, 'w')
  
  for line in infile:
    if iscontrol(line.strip()):
      rejectfile.write(line)
    else:
      outfile.write(line)
    
if __name__ == '__main__':
  main()

