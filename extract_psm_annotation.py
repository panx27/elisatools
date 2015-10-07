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

# Scrape monolingual psms for posts and headlines (elsewhere)

def main():
  import codecs
  parser = argparse.ArgumentParser(description="Extract and print psm annotat" \
                                   "ion data from LRLP in a form that is amen" \
                                   "able to insertion into future xml",
                                   formatter_class=\
                                   argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--infile", "-i", nargs='+', type=argparse.FileType('r'),
                      default=[sys.stdin,], help="input zip file(s)" \
                      " (each contains a multi file)")
  parser.add_argument("--outfile", "-o", type=argparse.FileType('w'),
                      default=sys.stdout,
                      help="where to write extracted semantic info")
  try:
    args = parser.parse_args()
  except IOError, msg:
    parser.error(str(msg))

  writer = codecs.getwriter('utf8')
  outfile = writer(args.outfile)

  nonehash = {"value":"None"}

  for infile in args.infile:
    inbase = '.'.join(os.path.basename(infile.name).split('.')[:-2])
    archive = zf(infile)
    for info in archive.infolist():
      if info.file_size < 20:
        continue
      # Assume psm structure
      if os.path.dirname(info.filename) != 'psm':
        continue
      with archive.open(info, 'rU') as ifh:
        xobj = ET.parse(ifh)
        try:
          headlines = [(x.get("begin_offset"), x.get("char_length")) \
                       for x in xobj.findall("string[@type='headline']")]
          # TODO: funornone this back into functional
          postnodes = xobj.findall("string[@type='post']")
          posts = []
          for x in postnodes:
            post = []
            anode = x.find("attribute[@name='author']")
            if anode is None:
              anode = nonehash
            dnode = x.find("attribute[@name='datetime']")
            if dnode is None:
              dnode = nonehash
            posts.append((x.get("begin_offset"),
                          x.get("char_length"),
                          anode.get('value'),
                          dnode.get('value')))
        except:
          print info.filename
          raise
          sys.exit(1)

        # GENRE/LANG/DATE info will be gleaned from filename later.
        # assume psm.xml and strip it off
        fname = os.path.basename(info.filename).split(".psm.xml")[0]
        for h in headlines:
          outfile.write("\t".join(("headline", fname)+h)+"\n")
        for p in posts:
          outfile.write("\t".join(("post", fname)+p)+"\n")

if __name__ == '__main__':
  main()
