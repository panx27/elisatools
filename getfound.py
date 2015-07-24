#! /usr/bin/env python
# utilities for dealing with LRLPs
import argparse
import sys
import os
import re
import os.path
import lputil

def main():
  parser = argparse.ArgumentParser(description="Print found parallel contents")
  parser.add_argument("--rootdir", "-r", help="root lrlp dir")
  parser.add_argument("--prefix", "-p", help="output files prefix")
  parser.add_argument("--src", "-s", default='uzb', help="source language 3 letter code")
  parser.add_argument("--trg", "-t", default='eng', help="target language 3 letter code")
  parser.add_argument("--xml", "-x", action='store_true', help="process ltf xml files")

  try:
    args = parser.parse_args()
  except IOError, msg:
    parser.error(str(msg))

  sfile = args.prefix+"."+args.src
  sman = sfile+".manifest"
  tfile = args.prefix+"."+args.trg
  tman = tfile+".manifest"
  sfh = open(sfile, 'w')
  tfh = open(tfile, 'w')
  smh = open(sman, 'w')
  tmh = open(tman, 'w')
  for s, t, a in lputil.all_found_tuples(args.rootdir, src=args.src, trg=args.trg, xml=args.xml):
    # TODO: xml case
    sl, tl = lputil.get_aligned_sentences_xml(s, t, a) if args.xml else lputil.get_aligned_sentences(s, t, a) 
    slen = len(sl)
    tlen = len(tl)
    if slen != tlen:
      sys.stderr.write("Warning: different number of lines in files:\n%s %d\n%s %d\n" % (s, slen, t, tlen))
      continue
    sfh.write(''.join(sl).encode('utf-8'))
    tfh.write(''.join(tl).encode('utf-8'))
#    tfh.writelines(tl)
    smh.write("%s %d\n" % (s, slen))
    tmh.write("%s %d\n" % (t, tlen))



if __name__ == '__main__':
  main()

