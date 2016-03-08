#!/usr/bin/env python3
import argparse
import sys
import codecs
if sys.version_info[0] == 2:
  from itertools import izip
from collections import defaultdict as dd
import re
import os.path
import gzip
import lxml.etree as ET
scriptdir = os.path.dirname(os.path.abspath(__file__))


reader = codecs.getreader('utf8')
writer = codecs.getwriter('utf8')


def prepfile(fh, code):
  ret = gzip.open(fh.name, code) if fh.name.endswith(".gz") else fh
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
  parser = argparse.ArgumentParser(description="given xml laf file with out offsets and ltf file with offsets, add the offsets to the laf",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--ltffile", "-t", nargs='?', type=argparse.FileType('rb'), default=sys.stdin, help="input file")
  parser.add_argument("--laffile", "-a", nargs='?', type=argparse.FileType('rb'), default=sys.stdin, help="input laf file")
  parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('w'), default=sys.stdout, help="output file")



  try:
    args = parser.parse_args()
  except IOError as msg:
    parser.error(str(msg))

  ltffile = args.ltffile
  laffile = args.laffile
  outfile = prepfile(args.outfile, 'w')



  lafroot = ET.parse(laffile)
  ltfroot = ET.parse(ltffile)

  for seg in lafroot.findall("//ANNOTATION"):
    st = seg.get("start_token")
    se = seg.get("end_token")
    ex = seg.find("EXTENT")
    try:
      sts = ltfroot.find("//TOKEN[@id='%s']" % st).get('start_char')
    except AttributeError:
      print("Couldn't find %s in %s" % (st, ltffile.name))
      continue
    try:
      see = ltfroot.find("//TOKEN[@id='%s']" % se).get('end_char')
    except AttributeError:
      print("Couldn't find %s in %s" % (se, ltffile.name))
      continue
    ex.set('start_char', sts)
    ex.set('end_char', see)
  outfile.write(ET.tostring(lafroot, pretty_print=True, encoding='utf-8').decode('utf-8'))
if __name__ == '__main__':
  main()

