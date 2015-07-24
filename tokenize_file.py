#! /usr/bin/env python
import argparse
import sys
import codecs
import lputil
import xml.etree.ElementTree as ET

def main():
  parser = argparse.ArgumentParser(description="given an ltf file, return its tokenized contents")
  parser.add_argument("--infile", "-i", nargs='?', help="input file name")
  parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('w'), default=sys.stdout, help="output file")



  try:
    args = parser.parse_args()
  except IOError, msg:
    parser.error(str(msg))

  writer = codecs.getwriter('utf8')
  outfile = writer(args.outfile)

  sroot = ET.parse(args.infile)
  outfile.write(''.join(lputil.get_tokens(sroot)).encode('utf-8'))

if __name__ == '__main__':
  main()

