#! /usr/bin/env python
import argparse
import sys
import codecs
from collections import defaultdict as dd
import re
import os.path
import os
scriptdir = os.path.dirname(os.path.abspath(__file__))
import lputil
import datetime

def printout(prefix, path, src, trg, outdir, origoutdir, tokoutdir, stp=lputil.selected_translation_pairs, el=lputil.extract_lines):
  ''' find files and print them out '''
  src_man_fh=open(os.path.join(outdir, "%s.%s.manifest" % (prefix, src)), 'w')
  trg_man_fh=open(os.path.join(outdir, "%s.%s.manifest" % (prefix, trg)), 'w')
  src_orig_fh=open(os.path.join(origoutdir, "%s.%s" % (prefix,src)), 'w')
  trg_orig_fh=open(os.path.join(origoutdir, "%s.%s" % (prefix,trg)), 'w')
  src_tok_fh=open(os.path.join(tokoutdir, "%s.tok.%s" % (prefix,src)), 'w')
  trg_tok_fh=open(os.path.join(tokoutdir, "%s.tok.%s" % (prefix,trg)), 'w')
  for m in stp(path, src=src, trg=trg, xml=True):
    sl, tl = el(*m, xml=True, tokenize=False)
    if sl is None or tl is None:
      continue
    # strict rejection of different length lines. If these are desired, do gale & church or brown et al or something similar here
    slen = len(sl)
    tlen = len(tl)
    if slen != tlen:
      sys.stderr.write("Warning: different number of lines in files:\n%s %d\n%s %d\n" % (m[0], slen, m[1], tlen))
      continue
    src_orig_fh.write(''.join(sl).encode('utf-8'))
    for i in xrange(len(sl)):
      src_man_fh.write(m[0]+"\n")
    for i in xrange(len(tl)):
      trg_man_fh.write(m[1]+"\n")
    trg_orig_fh.write(''.join(tl).encode('utf-8'))
    tsl, ttl = el(*m, xml=True, tokenize=True)
    src_tok_fh.write(''.join(tsl).encode('utf-8'))
    trg_tok_fh.write(''.join(ttl).encode('utf-8'))

def main():
  parser = argparse.ArgumentParser(description="extract parallel data from expanded lrlp to flat files and manifests.")
  parser.add_argument("--rootdir", "-r", default=".", help="root lrlp dir")
  parser.add_argument("--outdir", "-o", default="./parallel/extracted", help="where to write extracted files")
  parser.add_argument("--src", "-s", default='uzb', help="source language 3 letter code")
  parser.add_argument("--trg", "-t", default='eng', help="target language 3 letter code")
  parser.add_argument("--toksubdir", default="tokenized", help="subdirectory for tokenized files")
  parser.add_argument("--origsubdir", default="original", help="subdirectory for untokenized files")

  try:
    args = parser.parse_args()
  except IOError, msg:
    parser.error(str(msg))

  tokoutdir=os.path.join(args.outdir, args.toksubdir)
  origoutdir=os.path.join(args.outdir, args.origsubdir)
  if not os.path.exists(args.outdir):
    os.makedirs(args.outdir)
    os.makedirs(tokoutdir)
    os.makedirs(origoutdir)
  
  source_fh = open(os.path.join(args.outdir, "source"), 'a')
  source_fh.write("Extracted parallel data from %s to %s on %s\nusing %s; command issued from %s\n" % (args.rootdir, args.outdir, datetime.datetime.now(), ' '.join(sys.argv), os.getcwd()))
  datadirs=[args.rootdir, 'data', 'translation']

  # from source
  printout("fromsource.generic", os.path.join(*(datadirs+["from_%s" % args.src,])), args.src, args.trg, args.outdir, origoutdir, tokoutdir)
  # news from target
  printout("fromtarget.news", os.path.join(*(datadirs+["from_%s" % args.trg, "news"])), args.src, args.trg, args.outdir, origoutdir, tokoutdir)
  # phrase book from target
  printout("fromtarget.phrasebook", os.path.join(*(datadirs+["from_%s" % args.trg, "phrasebook"])), args.src, args.trg, args.outdir, origoutdir, tokoutdir)
  # elicitation from target
  printout("fromtarget.elicitation", os.path.join(*(datadirs+["from_%s" % args.trg, "elicitation"])), args.src, args.trg, args.outdir, origoutdir, tokoutdir)
  # found data
  printout("found.generic", args.rootdir, args.src, args.trg, args.outdir, origoutdir, tokoutdir, stp=lputil.all_found_tuples, el=lputil.get_aligned_sentences)

if __name__ == '__main__':
  main()
