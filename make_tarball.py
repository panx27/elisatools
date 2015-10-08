#! /usr/bin/env python
import argparse
import sys
import codecs
from itertools import izip
from collections import defaultdict as dd
import re
import os.path
from lputil import mkdir_p
import shutil
import tarfile
scriptdir = os.path.dirname(os.path.abspath(__file__))


def main():
  parser = argparse.ArgumentParser(description="Add files and directories to a tarfile",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--outfile", "-o",
                      help='path to the tarfile')
  parser.add_argument("--prefix", "-p",
                      help='prefix to add to each file')
  parser.add_argument("--infiles", "-i", nargs='+',
                      help='files/directories to add to the tarfile')

  try:
    args = parser.parse_args()
  except IOError, msg:
    parser.error(str(msg))


  ofh = tarfile.open(name=args.outfile, mode='w:gz')
  for infile in args.infiles:
    if args.prefix is None:
      arcname = os.path.basename(infile)
    else:
      arcname = os.path.join(args.prefix, os.path.basename(infile))
    ofh.add(infile, arcname=arcname)
  ofh.close()

if __name__ == '__main__':
  main()

