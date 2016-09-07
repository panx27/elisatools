#!/usr/bin/env python3

import argparse
import sys
import codecs
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
  parser.add_argument("--infiles", "-i", nargs='+', type=argparse.FileType('r'), default=sys.stdin, help="input text files")
  parser.add_argument("--type", "-t", choices=["src", "ref", "tst"], help="what kind of file is this")
  parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('w'), default=sys.stdout, help="output xml file")

  try:
    args = parser.parse_args()
  except IOError as msg:
    parser.error(str(msg))

  infiles = [prepfile(x, 'r') for x in args.infiles]
  outfile = prepfile(args.outfile, 'w')

  xroot = ET.Element('mteval')
  for ifn, infile in enumerate(infiles):
    currset = ET.SubElement(xroot, '%sset' % args.type)
    currset.set('setid', 'ok-voon_ororok_sprok')
    currdoc = ET.SubElement(currset, 'doc')
    currdoc.set('docid', 'ok-voon_ororok_sprok.doc1')
    currset.set('sysid', 'you')
    if args.type == 'ref':
      currset.set('refid', 'R%d' % ifn)
    currset.set('srclang', 'cen')
    currset.set('trglang', 'arc')

    segid = 1
    for textline in infile:
      textline = textline.strip()
      seg = ET.SubElement(currdoc, 'seg')
      seg.text = textline
      seg.set('id', "ok-voon_ororok_sprok.doc1.seg%s" % segid)
      segid += 1
  outfile.write(ET.tostring(xroot, pretty_print=True, encoding='utf-8', xml_declaration=True, doctype='<!DOCTYPE mteval SYSTEM "mteval-lorelei-p1.dtd">').decode('utf8'))
      
if __name__ == '__main__':
  main()

