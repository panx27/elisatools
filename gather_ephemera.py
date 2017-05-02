#!/usr/bin/env python3

import argparse
import sys
import codecs

from collections import defaultdict as dd
import re
import os
import os.path
from lputil import mkdir_p
import shutil
scriptdir = os.path.dirname(os.path.abspath(__file__))


# the things you look for and where you put them
manifest = {"docs":"docs",
            "tools":"tools",
            "README.txt":"README.txt",
            "README_annotations.txt":"README_annotations.txt",
            os.path.join("data", "audio"):"audio",
            os.path.join("data", "annotation", "morph_alignment"):"morph_alignment",
            }

# things you shouldn't transfer
transferexcluded = set(["tools"])

def copything(src, dst):
  if os.path.isdir(src):
    shutil.copytree(src, dst)
  elif os.path.isfile(src):
    shutil.copy(src, dst)
  else:
    sys.stderr.write("%s not directory or file; skipping" % src)
  
def main():
  parser = argparse.ArgumentParser(description="relocate parts of a lrlp into a centralized location to make it easier to gather later",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--source", "-s",
                      help='path to the expanded lrlp')
  parser.add_argument("--old", "-o", default=None,
                      help='path to old ephemera directory')
  parser.add_argument("--target", "-t",
                      help='path to the desired catch-all directory')

  try:
    args = parser.parse_args()
  except IOError as msg:
    parser.error(str(msg))

  if os.path.exists(args.target):
    shutil.rmtree(args.target)
  mkdir_p(args.target)
  for indirstub, outdirstub in manifest.items():
    indir = os.path.join(args.source, indirstub)
    if os.path.exists(indir):
      outdir = os.path.join(args.target, outdirstub)
      sys.stderr.write("Copying {} to {}\n".format(indir, outdir))
      copything(indir, outdir)
  if args.old is not None:
    # traverse top level of old and move everything not in transferexcluded to target/old
    oldtarget=os.path.join(args.target, "old")
    mkdir_p(oldtarget)
    for oldfile in os.listdir(args.old):
      if oldfile not in transferexcluded:
        fullsource = os.path.join(args.old, oldfile)
        fulltarget = os.path.join(oldtarget, oldfile)
        sys.stderr.write("Transferring {} to {}\n".format(fullsource, fulltarget))
        copything(fullsource, fulltarget)

if __name__ == '__main__':
  main()

