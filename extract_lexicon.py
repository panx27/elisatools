#! /usr/bin/env python

# extract lexicon file 
import argparse
import sys
import os
import re
import os.path
import xml.etree.ElementTree as ET
import os
import datetime

def main():
  import codecs
  parser = argparse.ArgumentParser(description="Extract lexicon file from xml")
  parser.add_argument("--infile", "-i", nargs='+', type=argparse.FileType('r'), default=[sys.stdin,], help="input lexicon file")
  parser.add_argument("--outdir", "-o", help="output directory")


  try:
    args = parser.parse_args()
  except IOError, msg:
    parser.error(str(msg))

  if not os.path.exists(args.outdir):
    os.makedirs(args.outdir)
  outfile=os.path.join(args.outdir, "lexicon")
  counter = 1
  while os.path.exists(outfile):
    outfile = os.path.join(args.outdir, "lexicon.%d" % counter)
    counter += 1

  of = codecs.open(outfile, 'w', 'utf-8')
  for infile in args.infile:
    xobj = ET.parse(infile)
    for entry in xobj.findall(".//ENTRY"):
      of.write("%s\t%s\t%s\n" % (entry.find(".//WORD").text, entry.find(".//POS").text, entry.find(".//GLOSS").text))

    source_fh = open(os.path.join(args.outdir, "source"), 'a')
    source_fh.write("Extracted lexicon from %s to %s on %s\nusing %s; command issued from %s\n" % (infile.name, outfile, datetime.datetime.now(), ' '.join(sys.argv), os.getcwd()))


if __name__ == '__main__':
  main()

