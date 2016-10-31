#!/usr/bin/env python3
#-*- coding: utf-8 -*-
import sys
# utilities for dealing with LRLPs
import argparse
import codecs
import os
import re
import os.path
from zipfile import ZipFile as zf
import xml.etree.ElementTree as ET
import gzip
import os
scriptdir = os.path.dirname(os.path.abspath(__file__))
import datetime
import subprocess
import shlex
from lputil import morph_tok, getgarbagemask
from itertools import compress


# TODO: unify codebase with extract_mono

def main():
  parser = argparse.ArgumentParser(description="Extract and print monolingual" \
                                   " data, tokenized, morph, pos tag and " \
                                   "original, with manifests from extracted files")
  parser.add_argument("--rootdir", "-r", default=".",
                      help="root lrlp dir")
  parser.add_argument("--datadirs", nargs='+', default=[],
                      help="elements in path from root to ltf files")
  parser.add_argument("--src", "-s", default='uzb',
                      help="source language 3 letter code")
  parser.add_argument("--trg", "-t", default='eng',
                      help="target language 3 letter code")
  parser.add_argument("--outdir", "-o",
                      help="where to write extracted files")
  parser.add_argument("--nogarbage", action='store_true', default=False,
                      help="turn off garbage filtering")
  parser.add_argument("--toksubdir", default="tokenized",
                      help="subdirectory for tokenized files")
  parser.add_argument("--cdectoksubdir", default="cdec-tokenized",
                      help="subdirectory for cdec-tokenized files")
  parser.add_argument("--morphtoksubdir", default="morph-tokenized",
                      help="subdirectory for tokenized files based on " \
                      "morphological segmentation")
  parser.add_argument("--morphsubdir", default="morph",
                      help="subdirectory for morphological information")
  parser.add_argument("--origsubdir", default="original",
                      help="subdirectory for untokenized files")
  parser.add_argument("--garbagesubdir", default="garbage",
                      help="subdirectory for garbage files (under orig)")
  parser.add_argument("--possubdir", default="pos",
                      help="subdirectory for pos tag files")
  parser.add_argument("--cdectokenizer", default=os.path.join(scriptdir,
                                                              "cdectok.sh"),
                      help="cdec tokenizer program wrapper")

  try:
    args = parser.parse_args()
  except IOError as msg:
    parser.error(str(msg))


  tokoutdir=os.path.join(args.outdir, args.toksubdir)
  origoutdir=os.path.join(args.outdir, args.origsubdir)
  cdectokoutdir=os.path.join(args.outdir, args.cdectoksubdir)
  morphtokoutdir=os.path.join(args.outdir, args.morphtoksubdir)
  morphoutdir=os.path.join(args.outdir, args.morphsubdir)
  posoutdir=os.path.join(args.outdir, args.possubdir)

  dirs = [args.outdir,
          tokoutdir,
          cdectokoutdir,
          origoutdir,
          morphtokoutdir,
          morphoutdir,
          posoutdir]
  if args.nogarbage:
    garbageoutdir = None
  else:
    garbageoutdir=os.path.join(origoutdir, args.garbagesubdir)
    dirs.append(garbageoutdir)
  for dir in dirs:
    if not os.path.exists(dir):
      os.makedirs(dir)


  datadirs=[args.rootdir,]+args.datadirs
  indir = os.path.join(*datadirs)
  man_fh = open(os.path.join(args.outdir, "mono.manifest"),'w')
  orig_fh = open(os.path.join(origoutdir, "mono.flat"), 'w')
  if args.nogarbage:
    garbage_fh = None
    garbage_man_fh = None
  else:
    garbage_fh = open(os.path.join(garbageoutdir, "mono.flat"), 'w')
    garbage_man_fh = open(os.path.join(garbageoutdir, "mono.manifest"),'w')
  tok_fh = open(os.path.join(tokoutdir, "mono.flat"), 'w')
  morphtok_fh = open(os.path.join(morphtokoutdir,
                                         "mono.flat"), 'w')
  morph_fh = open(os.path.join(morphoutdir, "mono.flat"), 'w')
  pos_fh = open(os.path.join(posoutdir, "mono.flat"), 'w')

  for srcfile in os.listdir(indir):
    if srcfile.startswith(".") or not srcfile.endswith("ltf.xml"):
      continue
    srcfile = os.path.join(indir, srcfile)
    with open(srcfile, 'r') as ifh:
      try:
        xobj = ET.parse(ifh)
        docid = xobj.findall(".//DOC")[0].get('id')
        origlines = [ x.text+"\n" for x in xobj.findall(".//ORIGINAL_TEXT") ]
        garbagemask = getgarbagemask(origlines, disabled=args.nogarbage)
        goodmask = [not x for x in garbagemask]
        seginfo = [ [ x.get(y) for y in ('id', 'start_char', 'end_char') ]
                    for x in xobj.findall(".//SEG") ]
        for line in compress(origlines, garbagemask):
          orig_fh.write(line)
        for tup in compress(seginfo, garbagemask):
          man_fh.write("\t".join(map(str, [srcfile,docid]+tup))+"\n")
        if not args.nogarbage:
          for line in compress(origlines, goodmask):
            garbage_fh.write(line)
          for tup in compress(seginfo, goodmask):
            garbage_man_fh.write("\t".join(map(str, [srcfile,docid]+tup))+"\n")
        for x in compress(xobj.findall(".//SEG"), garbagemask):
          tokens = x.findall(".//TOKEN")
          toktext = []
          morphtoktext = []
          morphtext = []
          postext = []
          for y in tokens:
            if y.text is None:
              continue
            toktext.append(y.text)
            postext.append(y.get("pos") or "none")
            for mt, mtt in morph_tok(y):
              morphtext.append(mt)
              morphtoktext.append(mtt)
          tok_fh.write(' '.join(toktext)+"\n")
          morphtok_fh.write(' '.join(morphtoktext)+"\n")
          morph_fh.write(' '.join(morphtext)+"\n")
          pos_fh.write(' '.join(postext)+"\n")
      except ET.ParseError:
        sys.stderr.write("Parse error on "+ifh.name+"\n")
        continue
  orig_fh.close()
  cdec_cmd = "%s -i %s -o %s -t %s" % (args.cdectokenizer,
                                       orig_fh.name,
                                       os.path.join(cdectokoutdir,
                                                    "mono.flat.lc"),
                                       os.path.join(cdectokoutdir,
                                                    "mono.flat"))
  p = subprocess.Popen(shlex.split(cdec_cmd))
  p.wait()

if __name__ == '__main__':
  main()
