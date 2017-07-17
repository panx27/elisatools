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
from subprocess import check_call, CalledProcessError
import shlex
from lputil import morph_tok, getgarbagemask
from itertools import compress

def addonoffarg(parser, arg, dest=None, default=True, help="TODO"):
  ''' add the switches --arg and --no-arg that set parser.arg to true/false, respectively'''
  group = parser.add_mutually_exclusive_group()
  dest = arg if dest is None else dest
  group.add_argument('--%s' % arg, dest=dest, action='store_true', default=default, help=help)
  group.add_argument('--no-%s' % arg, dest=dest, action='store_false', default=default, help="See --%s" % arg)

def main():
  parser = argparse.ArgumentParser(description="Extract and print monolingual" \
                                   " data, tokenized, morph, pos tag and " \
                                   "original, with manifests")
  parser.add_argument("--infile", "-i", nargs='+', type=argparse.FileType('rb'),
                      default=[sys.stdin,],
                      help="input zip file(s) (each contains a multi file)")
  parser.add_argument("--outdir", "-o",
                      help="where to write extracted files")
  parser.add_argument("--nogarbage", action='store_true', default=False,
                      help="turn off garbage filtering")
  parser.add_argument("--toksubdir", default="raw.tokenized",
                      help="subdirectory for ldc-tokenized files")
  parser.add_argument("--cleantoksubdir", default="tokenized",
                      help="subdirectory for cleaned ldc-tokenized files")
  parser.add_argument("--cdectoksubdir", default="cdec-tokenized",
                      help="subdirectory for cdec-tokenized files")
  parser.add_argument("--morphtoksubdir", default="morph-tokenized",
                      help="subdirectory for tokenized files based on " \
                      "morphological segmentation")
  parser.add_argument("--morphsubdir", default="morph",
                      help="subdirectory for morphological information")
  parser.add_argument("--origsubdir", default="raw.original",
                      help="subdirectory for untokenized files")
  parser.add_argument("--cleanorigsubdir", default="original",
                      help="subdirectory for cleaned raw original")

  parser.add_argument("--garbagesubdir", default="garbage",
                      help="subdirectory for garbage files (under orig)")
  parser.add_argument("--possubdir", default="pos",
                      help="subdirectory for pos tag files")
  parser.add_argument("--cleanpath", default=os.path.join(scriptdir, 'clean.sh'),
                      help="path to cleaning script")
  parser.add_argument("--cdectokenizer", default=os.path.join(scriptdir,
                                                              "cdectok.sh"),
                      help="cdec tokenizer program wrapper")
  addonoffarg(parser, 'cdec', help="do cdec tokenization", default=True)
  addonoffarg(parser, 'removesn', help="remove SN from mono zip (to avoid underscore tweets)", default=False)
  
  try:
    args = parser.parse_args()
  except IOError as msg:
    parser.error(str(msg))


  tokoutdir=os.path.join(args.outdir, args.toksubdir)
  origoutdir=os.path.join(args.outdir, args.origsubdir)
  cleantokoutdir=os.path.join(args.outdir,  args.cleantoksubdir)
  cleanorigoutdir=os.path.join(args.outdir, args.cleanorigsubdir)
  cdectokoutdir=os.path.join(args.outdir, args.cdectoksubdir)
  morphtokoutdir=os.path.join(args.outdir, args.morphtoksubdir)
  morphoutdir=os.path.join(args.outdir, args.morphsubdir)
  posoutdir=os.path.join(args.outdir, args.possubdir)
  cleanpath = args.cleanpath
  dirs = [args.outdir,
          tokoutdir,
          origoutdir,
          cleantokoutdir,
          cleanorigoutdir,
          morphtokoutdir,
          morphoutdir,
          posoutdir]
  if args.cdec:
    dirs.append(cdectokoutdir)
  if args.nogarbage:
    garbageoutdir = None
  else:
    garbageoutdir=os.path.join(origoutdir, args.garbagesubdir)
    dirs.append(garbageoutdir)
  for dir in dirs:
    if not os.path.exists(dir):
      os.makedirs(dir)

  defaultcount=0
  for infile in args.infile:
    inbase = '.'.join(os.path.basename(infile.name).split('.')[:-2])
    if len(inbase) == 0:
      inbase="default.%d" % defaultcount
      defaultcount+=1
    archive = zf(infile)
    man_fh = open(os.path.join(args.outdir, "%s.manifest" % inbase),'w')
    orig_fh = open(os.path.join(origoutdir, "%s.flat" % inbase), 'w')
    if args.nogarbage:
      garbage_fh = None
      garbage_man_fh = None
    else:
      garbage_fh = open(os.path.join(garbageoutdir, "%s.flat" % inbase), 'w')
      garbage_man_fh = open(os.path.join(garbageoutdir, "%s.manifest" % inbase),'w')
    tok_fh = open(os.path.join(tokoutdir, "%s.flat" % inbase), 'w')
    morphtok_fh = open(os.path.join(morphtokoutdir,
                                           "%s.flat" % inbase), 'w')
    morph_fh = open(os.path.join(morphoutdir, "%s.flat" % inbase), 'w')
    pos_fh = open(os.path.join(posoutdir, "%s.flat" % inbase), 'w')
    for info in archive.infolist():
      if info.file_size < 20:
        continue
      # assume ltf filename
      if not info.filename.endswith("ltf.xml"):
        continue
      # print info.filename
      with archive.open(info, 'rU') as ifh:
        try:
          xobj = ET.parse(ifh)
          docid = xobj.findall(".//DOC")[0].get('id')
          # avoid anonymized tweets in packages but not relocated downloaded mono tweets
          if "tweets" not in inbase and args.removesn and "_SN_" in docid:
            sys.stderr.write("SN skip: not extracting {}\n".format(docid))
            continue
          origlines = [ x.text+"\n" for x in xobj.findall(".//ORIGINAL_TEXT") ]
          garbagemask = getgarbagemask(origlines, disabled=args.nogarbage)
          goodmask = [not x for x in garbagemask]
          seginfo = [ [ x.get(y) for y in ('id', 'start_char', 'end_char') ]
                      for x in xobj.findall(".//SEG") ]
          for line in compress(origlines, garbagemask):
            orig_fh.write(line)
          for tup in compress(seginfo, garbagemask):
            man_fh.write("\t".join(map(str, [info.filename,docid]+tup))+"\n")
          if not args.nogarbage:
            for line in compress(origlines, goodmask):
              garbage_fh.write(line)
            for tup in compress(seginfo, goodmask):
              garbage_man_fh.write("\t".join(map(str, [info.filename,docid]+tup))+"\n")
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
    tok_fh.close()
    # raw orig->clean orig
    # raw tok->clean tok
    clean_orig = os.path.join(cleanorigoutdir, "%s.flat" % inbase)
    clean_tok =  os.path.join(cleantokoutdir, "%s.flat" % inbase)
    for inclean, outclean in zip((orig_fh.name, tok_fh.name), (clean_orig, clean_tok)):
      cleancmd = "{cmd} {inclean} {outclean}".format(cmd=cleanpath, inclean=inclean, outclean=outclean)
      sys.stderr.write(cleancmd+"\n")
      try:
        check_call(shlex.split(cleancmd))
      except CalledProcessError as e:
        sys.stderr.write("Error code %d running %s\n" % (e.returncode, e.cmd))
        sys.exit(1)

    if args.cdec:
      cdec_cmd = "%s -i %s -o %s -t %s" % (args.cdectokenizer,
                                           orig_fh.name,
                                           os.path.join(cdectokoutdir,
                                                        "%s.flat.lc" % inbase),
                                           os.path.join(cdectokoutdir,
                                                        "%s.flat" % inbase))
      p = subprocess.Popen(shlex.split(cdec_cmd))
      p.wait()

if __name__ == '__main__':
  main()
