#! /usr/bin/env python
import argparse
import sys
import codecs
from itertools import izip
from lxml import etree as ET
#from xml.etree import ElementTree as ET
from collections import defaultdict as dd
import re
import os.path
import gzip
scriptdir = os.path.dirname(os.path.abspath(__file__))


def main():
  parser = argparse.ArgumentParser(description="Given a compressed elisa xml file and list of attributes, print them out, tab separated",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--infile", "-i", nargs='?', type=argparse.FileType('rb'), default=sys.stdin, help="input file")
  parser.add_argument("--fields", "-f", nargs='+', help="list of fields to extract text from. if attribute is desired, use field.attribute")
  parser.add_argument("--segment", "-s", default="PARALLEL", help="segment name. PARALLEL for x-eng, SEGMENT for monolingual. More than one match per segment will be concatenated")
  parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('w'), default=sys.stdout, help="output file")



  try:
    args = parser.parse_args()
  except IOError, msg:
    parser.error(str(msg))

  reader = codecs.getreader('utf8')
  writer = codecs.getwriter('utf8')
  infile = args.infile
  infile = gzip.open(infile.name, 'r') if infile.name.endswith(".gz") else infile
  #infile = reader(infile)
  outfile = gzip.open(args.outfile.name, 'w') if args.outfile.name.endswith(".gz") else args.outfile
  outfile = writer(outfile)

  for _, element in ET.iterparse(infile, events=("end",), tag=args.segment):
    outfields = []
    for field in args.fields:
      subfields = field.split(".")
      matches = [element,] if subfields[0] == args.segment else element.findall(".//"+subfields[0])
      for match in matches:
        outfields.append(match.get(subfields[1]) if len(subfields) > 1 else match.text)
    element.clear()
    outfile.write("\t".join(outfields)+"\n")

if __name__ == '__main__':
  main()

