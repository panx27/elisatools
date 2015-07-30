#! /usr/bin/env python
import argparse
import sys
import codecs
from collections import defaultdict as dd
import lxml.etree as ET
import gzip
import re
import os.path
import hashlib
from itertools import izip
#from xml.dom import minidom
scriptdir = os.path.dirname(os.path.abspath(__file__))

# TODO: option to build gzip file

def main():
  parser = argparse.ArgumentParser(description="Create xml from extracted and transformed monolingual data",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--rootdir", "-r", default=".", help="root lrlp dir")
  parser.add_argument("--corpora", "-c", nargs='+', help="prefixes that have at minimum a manifest and original/ file")
  parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('w'), default=sys.stdout, help="output file")

  try:
    args = parser.parse_args()
  except IOError, msg:
    parser.error(str(msg))

  reader = codecs.getreader('utf-8')
  writer = codecs.getwriter('utf-8')
  outfile = args.outfile
#  outfile = writer(args.outfile)


  # each segment is a legit xml block. the corpus/language/document are faked
  # TODO: corpus/document
  # TODO: make this more generalizable!
  for corpus in args.corpora:
    manifest = reader(open(os.path.join(args.rootdir, "%s.manifest" % corpus)))
    origfile = reader(open(os.path.join(args.rootdir, "original", "%s.flat" % corpus)))
    tokfile = reader(open(os.path.join(args.rootdir, "tokenized", "%s.flat" % corpus)))
    cdectokfile = reader(open(os.path.join(args.rootdir, "cdec-tokenized", "%s.flat" % corpus)))
    cdectoklcfile = reader(open(os.path.join(args.rootdir, "cdec-tokenized", "%s.flat.lc" % corpus)))
    morphtokfile = reader(open(os.path.join(args.rootdir, "morph-tokenized", "%s.flat" % corpus)))
    morphfile = reader(open(os.path.join(args.rootdir, "morph", "%s.flat" % corpus)))
    for manline, origline, tokline, cdectokline, cdectoklcline, morphtokline, morphline in izip(manifest, origfile, tokfile, cdectokfile, cdectoklcfile, morphtokfile, morphfile):
      origline = origline.strip()
      tokline = tokline.strip()
      cdectokline =   cdectokline.strip()
      cdectoklcline = cdectoklcline.strip()
      morphtokline =   morphtokline.strip()
      morphline =   morphline.strip()
      man = manline.strip().split('\t')
      fields = man[1].split('_') # genre, provenance, lang, id, date
      xroot = ET.Element('SEGMENT')
      subelements = []
      subelements.extend(zip(['GENRE', 'PROVENANCE', 'LANGUAGE', 'ID', 'DATE'], man[1].split('_')))
      subelements.extend(zip(['SEGMENT_ID', 'START_CHAR', 'END_CHAR'], man[2:]))
      subelements.append(("ORIG_RAW_SOURCE", origline))
      subelements.append(("MD5_HASH", hashlib.md5(origline.encode('utf-8')).hexdigest()))
      subelements.append(("LRLP_TOKENIZED_SOURCE", tokline))
      subelements.append(("CDEC_TOKENIZED_SOURCE", cdectokline))
      subelements.append(("CDEC_TOKENIZED_LC_SOURCE", cdectoklcline))
      subelements.append(("MORPH_TOKENIZED_SOURCE", morphtokline))
      subelements.append(("MORPH_SOURCE", morphline))
      # TODO: more tokenizations, etc
      for key, text in subelements:
        se = ET.SubElement(xroot, key)
        se.text = text
      #et = ET.ElementTree(element=xroot)
      xmlstr = ET.tostring(xroot, pretty_print=True, encoding='utf-8', xml_declaration=False)
#      xmlstr = minidom.parseString(ET.tostring(xroot)).toprettyxml(indent="   ")
      outfile.write(xmlstr)
  # TODO /corpus/document
if __name__ == '__main__':
  main()
