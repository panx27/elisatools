#!/usr/bin/env python3
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
from lxml import etree as ET # pip install lxml
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
  parser = argparse.ArgumentParser(description="Keep only documents in a document list",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--infile", "-i", help="input file; this is filtered down")
  parser.add_argument("--document", default="DOCUMENT", help="document object to keep or reject")
  parser.add_argument("--manifest", "-m", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="manifest file; doc id in first tab")
  parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('w'), default=sys.stdout, help="output file")



  try:
    args = parser.parse_args()
  except IOError as msg:
    parser.error(str(msg))

  manifestfile = prepfile(args.manifest, 'r')
  outfile = prepfile(args.outfile, 'w')

  manifest = set()
  for line in manifestfile:
    manifest.add(line.strip().split('\t')[0])
  inode = ET.parse(args.infile)
  keepcount=0
  removecount=0
  for doc in inode.findall('.//%s' % args.document):
    if doc.get('id') not in manifest:
      doc.getparent().remove(doc)
      removecount+=1
    else:
      keepcount+=1
  xmlstr = ET.tostring(inode, pretty_print=True, encoding='utf-8', xml_declaration=True).decode('utf-8')
  outfile.write(xmlstr+"\n")
  sys.stderr.write("{} kept, {} removed ({} in keep set)\n".format(keepcount, removecount, len(manifest)))

if __name__ == '__main__':
  main()

