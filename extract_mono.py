#! /usr/bin/env python
# utilities for dealing with LRLPs
import argparse
import codecs
import sys
import os
import re
import os.path
from zipfile import ZipFile as zf
import xml.etree.ElementTree as ET
import gzip
import os
scriptdir = os.path.dirname(os.path.abspath(__file__))
import datetime

def main():
  import codecs
  parser = argparse.ArgumentParser(description="Extract and print monolingual data, tokenized and original, with manifests")
  parser.add_argument("--infile", "-i", nargs='+', type=argparse.FileType('r'), default=[sys.stdin,], help="input zip file(s) (each contains a multi file)")
  parser.add_argument("--outdir", "-o", help="where to write extracted files")
  parser.add_argument("--toksubdir", default="tokenized", help="subdirectory for tokenized files")
  parser.add_argument("--origsubdir", default="original", help="subdirectory for untokenized files")

  try:
    args = parser.parse_args()
  except IOError, msg:
    parser.error(str(msg))

  writer = codecs.getwriter('utf8')

  tokoutdir=os.path.join(args.outdir, args.toksubdir)
  origoutdir=os.path.join(args.outdir, args.origsubdir)
  if not os.path.exists(args.outdir):
    os.makedirs(args.outdir)
    os.makedirs(tokoutdir)
    os.makedirs(origoutdir)

  for infile in args.infile:
    inbase = '.'.join(os.path.basename(infile.name).split('.')[:-2])
    archive = zf(infile)
    man_fh = writer(open(os.path.join(args.outdir, "%s.manifest" % inbase), 'w'))
    orig_fh = writer(open(os.path.join(origoutdir, "%s.flat" % inbase), 'w'))
    tok_fh = writer(open(os.path.join(tokoutdir, "%s.flat" % inbase), 'w'))
    for info in archive.infolist():
      if info.file_size < 20:
        continue
      # assume ltf structure
      if os.path.dirname(info.filename) != 'ltf':
        continue
      # print info.filename
      with archive.open(info, 'rU') as ifh:
        xobj = ET.parse(ifh)
        origlines = [ x.text+"\n" for x in xobj.findall(".//ORIGINAL_TEXT") ]
        orig_fh.writelines(origlines)
        for i in xrange(len(origlines)):
          man_fh.write("%s\n" % info.filename)
        tok_fh.writelines([ ' '.join([ y.text for y in x.findall(".//TOKEN") ])+"\n" for x in xobj.findall(".//SEG") ])





if __name__ == '__main__':
  main()

