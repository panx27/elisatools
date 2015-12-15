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
scriptdir = os.path.dirname(os.path.abspath(__file__))


# the things you look for and where you put them
manifest = {"docs":"docs",
            "tools":"tools",
            "README.txt":"README.txt",
            os.path.join("data", "audio"):"audio",
            os.path.join("data", "annotation", "morph_alignment"):"morph_alignment",
            }


def main():
  parser = argparse.ArgumentParser(description="relocate parts of a lrlp into a centralized location to make it easier to gather later",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--source", "-s",
                      help='path to the expanded lrlp')
  parser.add_argument("--target", "-t",
                      help='path to the desired catch-all directory')

  try:
    args = parser.parse_args()
  except IOError, msg:
    parser.error(str(msg))

  if os.path.exists(args.target):
    shutil.rmtree(args.target)
  mkdir_p(args.target)
  for indirstub, outdirstub in manifest.iteritems():
    indir = os.path.join(args.source, indirstub)
    if os.path.exists(indir):
      outdir = os.path.join(args.target, outdirstub)
      if os.path.isdir(indir):
        shutil.copytree(indir, outdir)
      elif os.path.isfile(indir):
        shutil.copy(indir, outdir)
      else:
        sys.stderr.write("%s not directory or file; skipping" % indir)

if __name__ == '__main__':
  main()

