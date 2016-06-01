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
import lxml.etree as ET
import tarfile as tf
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
  parser = argparse.ArgumentParser(description="Validate an xml file or a tarball of xml files",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--infiles", "-i", nargs='+', default=None,  help="input files; could be tarball or straight")
  parser.add_argument("--dtdfile", "-d", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="input dtd")
  parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('w'), default=sys.stdout, help="output file")



  try:
    args = parser.parse_args()
  except IOError as msg:
    parser.error(str(msg))

  infiles = []
  for file in args.infiles:
    if file.endswith("tgz") or file.endswith(".tar.gz"):
      tar = tf.open(file)
      infiles.append(tar)
    else:
      infiles.append([prepfile(open(file, 'r'), 'r'),])
  dtdfile = prepfile(args.dtdfile, 'r')
  outfile = prepfile(args.outfile, 'w')

  dtd = ET.DTD(dtdfile)
  good = True
  for fileset in infiles:
    for infile in fileset:
      origname = infile.name
      if not origname.endswith("xml"):
        outfile.write("Skipping "+infile.name+"\n")
        continue
      try:
        infile = fileset.extractfile(infile)
      except:
        infile = infile

      if not dtd.validate(ET.parse(infile)):
        good = False
        outfile.write(origname+":"+str(dtd.error_log.filter_from_errors())+"\n")

  if good:
    outfile.write("All good\n")
if __name__ == '__main__':
  main()

