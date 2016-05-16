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
import unicodedata as ud
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
  parser = argparse.ArgumentParser(description="given xml ltf file with tokenization and original text, generate a version with [schar, echar] offsets at segment and token levels",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--infile", "-i", nargs='?', type=argparse.FileType('rb'), default=sys.stdin, help="input file")
  parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('w'), default=sys.stdout, help="output file")



  try:
    args = parser.parse_args()
  except IOError as msg:
    parser.error(str(msg))

#  infile = prepfile(args.infile, 'r')
  infile = args.infile
  outfile = prepfile(args.outfile, 'w')



  root = ET.parse(infile)
  offset=0
  for seg in root.findall("//SEG"):
    ot = seg.find("ORIGINAL_TEXT")
    segtext = ot.text
    if segtext is None:
      continue
    # no whitespace on the ends please and no newlines
    segtext = segtext.replace('\n', ' ')
    segtext = segtext.replace('\t', ' ')
    segtext = segtext.strip()
    # and only one space between words
    segtext = ' '.join(segtext.split())
    ot.text = segtext
    # span length
    seg.set("start_char", str(offset))
    seg.set("end_char", str(offset+len(segtext)-1))
    # iterate through tokens
    segchars = list(segtext)
    tokoffset = offset
    for tok in seg.findall("TOKEN"):
      # remove empty tokens
      if tok.text is None:
        sys.stderr.write("Removing empty token "+str(ET.tostring(tok))+"\n")
        tok.getparent().remove(tok)
        continue
      tokchars = list(tok.text)
      # find the first character
      while tokchars[0] != segchars[0]:
        if segchars[0] != " " and ud.category(segchars[0]) != "Zs":
          sys.stderr.write("Mismatch between "+segtext+" and its tokens (whitespace): ["+tokchars[0]+"] vs ["+segchars[0]+"]("+ud.category(segchars[0])+")\n")
#          sys.exit(1)
        discard = segchars.pop(0)
        #print("Found %s (discard) at %d" % (discard, tokoffset))
        tokoffset+=1
      schar = segchars.pop(0)
      tokchars.pop(0)
      #print("Found %s (start of token) at %d" % (schar, tokoffset))
      tok.set("start_char", str(tokoffset))
      tokoffset+=1
      # make sure the whole token matches
      while len(tokchars) > 0:
        sc = segchars.pop(0)
        tc = tokchars.pop(0)
        if sc != tc:
          sys.stderr.write("Mismatch between "+segtext+" and its tokens at "+tok.text+": "+tc+" vs "+sc+"\n")
          #sys.exit(1)
        #print("Found %s (intermediate) at %d" % (sc, tokoffset))
        tokoffset+=1
      #print("End of token at %d" % (tokoffset-1))
      tok.set("end_char", str(tokoffset-1))
    offset = offset+len(segtext)+1
  outfile.write(ET.tostring(root, pretty_print=True, encoding='utf-8').decode('utf-8'))
if __name__ == '__main__':
  main()

