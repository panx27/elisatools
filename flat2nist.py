#!/usr/bin/env python3
# revised for use in y1eval
import argparse
import sys
import codecs
if sys.version_info[0] == 2:
  from itertools import izip
else:
  izip = zip
from collections import defaultdict as dd
import re
import os.path
import gzip
import lxml.etree as ET
scriptdir = os.path.dirname(os.path.abspath(__file__))


reader = codecs.getreader('utf8')
writer = codecs.getwriter('utf8')


def prepfile(fh, code):
  ret = gzip.open(fh.name, code if code.endswith("t") else code+"t") if fh.name.endswith(".gz") else fh
  if sys.version_info[0] == 2:
    if code.startswith('r'):
      ret = reader(fh)
    elif code.startswith('w'):
      ret = writer(fh)
    else:
      sys.stderr.write("I didn't understand code "+code+"\n")
      sys.exit(1)
  return ret



def main():
  parser = argparse.ArgumentParser(description=" given manifest and text data, generate nist files (src/ref/tst)",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--infile", "-i", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="input text file")
  parser.add_argument("--lang", "-l", help="language code")
  parser.add_argument("--type", "-t", choices=["src", "ref", "tst"], help="what kind of file is this")
  parser.add_argument("--manfile", "-m", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="input manifest file")
  parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('w'), default=sys.stdout, help="output xml file")



  try:
    args = parser.parse_args()
  except IOError as msg:
    parser.error(str(msg))

  infile = prepfile(args.infile, 'r')
  manfile = prepfile(args.manfile, 'r')
  outfile = prepfile(args.outfile, 'w')

  lastdocid = None
  xroot = ET.Element('mteval')
  currdoc = None
  currset = ET.SubElement(xroot, '%sset' % args.type)
  currset.set('setid', 'foo')
  currset.set('sysid', 'bar')
  currset.set('refid', 'baz')
  currset.set('srclang', args.lang)
  currset.set('trglang', 'eng')

  # TODO: set properties
  for manline, textline in izip(manfile, infile):
    mantoks = manline.strip().split('\t')
    textline = textline.strip()
    fname, docid, segid = mantoks[:3]
    segid = segid.split('.')[0]
    if docid != lastdocid:
      currdoc = ET.SubElement(currset, 'doc')
      currdoc.set('docid', docid)
    lastdocid = docid
    seg = ET.SubElement(currdoc, 'seg')
    seg.text = textline
    seg.set('id', segid)
  outfile.write(ET.tostring(xroot, pretty_print=True, encoding='utf-8', xml_declaration=True, doctype='<!DOCTYPE mteval SYSTEM "mteval-lorelei-p1.dtd">').decode('utf8'))
      
if __name__ == '__main__':
  main()

