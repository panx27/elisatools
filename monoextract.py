#!/usr/bin/env python3

# utilities for dealing with LRLPs
import argparse
import sys
import os
import re
import os.path
from zipfile import ZipFile as zf
import xml.etree.ElementTree as ET
import gzip
from io import TextIOWrapper

def main():
  import codecs
  parser = argparse.ArgumentParser(description="Print monolingual data")
  parser.add_argument("--infile", "-i", nargs='+', type=argparse.FileType('r'), default=[sys.stdin,], help="input zip file(s) (each contains a multi file)")
  #  parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('w'), default=sys.stdout, help="output file (single text file)")
  parser.add_argument("--outfile", "-o", help="output file (single text file)")
  parser.add_argument("--xml", "-x", action='store_true', help="process ltf xml files")
  parser.add_argument("--tokenize", action='store_true', help="use tokens (only applies if -x)")


  try:
    args = parser.parse_args()
  except IOError as msg:
    parser.error(str(msg))

  of = codecs.open(args.outfile, 'w', 'utf-8')
  for infile in args.infile:
    archive = zf(infile)
    for info in archive.infolist():
      if info.file_size < 20:
        continue
      # plain processing assumes rsd structure
      if not args.xml and os.path.dirname(info.filename) != 'rsd':
        continue
      # print info.filename
      with TextIOWrapper(archive.open(info, 'rU')) as ifh:
        if args.xml:
          xobj = ET.parse(ifh)
          if args.tokenize:
            of.writelines([ ' '.join([ y.text for y in x.findall(".//TOKEN") ])+"\n" for x in xobj.findall(".//SEG") ])
          else:
            of.writelines([ x.text+"\n" for x in xobj.findall(".//ORIGINAL_TEXT") ])
        else:
          lines = ifh.readlines()
          for line in lines:
            of.write(line.decode('utf8'))



if __name__ == '__main__':
  main()

