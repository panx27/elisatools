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


def getrootandid(line, idmap):
  ''' parse align line and adjust to match xml '''
#  print("Parsing "+line)
  root, id = line.split('-')
  if root in idmap:
    root = idmap[root]
  id = int(id)-1
  return root, id

def getxmlitem(root, indir, lang, id, oldxml):
  ''' open xml and get relevant item '''
  xfile = os.path.join(indir, lang, 'ltf', "%s.ltf.xml" % root)
  newxml = oldxml
  if ( not os.path.exists(xfile) ):
      sys.stderr.write("Couldn't find %s\n" % xfile)
      sys.exit(1)
  if oldxml is None or oldxml.docinfo.URL != xfile:
#      print("Loading "+xfile)
      newxml = ET.parse(xfile)
  xpath = "//SEG[@id='%s-%d']" % (root, id)
#  print("Looking for "+xpath)
  item = newxml.find(xpath)
  if item is None:
      sys.stderr.write("Couldn't find %s-%d in %s\n" % (root, id, xfile))
      sys.exit(1)
  so = int(item.get("start_char"))
  eo = int(item.get("end_char"))
  return newxml, so, eo

def main():
  parser = argparse.ArgumentParser(description="Given Hungarian segment alignments with mapper, create character alignments",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--alignfile", "-a", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="seg align file (engid tab hunid)")
  parser.add_argument("--mapfile", "-m", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="doc map file")
  parser.add_argument("--indir", "-i", default='.', help="input directory")
  parser.add_argument("--srclang", default='hun', help="src lang")
  parser.add_argument("--trglang", default='eng', help="trg lang")
  parser.add_argument("--outdir", "-o", default='sentence_alignment', help="output alignment file directory")



  try:
    args = parser.parse_args()
  except IOError as msg:
    parser.error(str(msg))

  mapfile = prepfile(args.mapfile, 'r')
  alignfile = prepfile(args.alignfile, 'r')

  idmap = {} # from alignfile id to xmlfile id
  for line in mapfile:
    toks = line.strip().split('\t')
    idmap[toks[1]]=toks[0]


  charalignments = dd(list)
  srcxml = None
  trgxml = None
  for line in alignfile:
    # turn contents of align line into mapped values
    trgline, srcline = line.strip().split('\t')
    if trgline=="None" or srcline=="None":
      continue
    trgroot, trgid = getrootandid(trgline, idmap)
    srcroot, srcid = getrootandid(srcline, idmap)

    # find the xml files and item appropriate to the line
    # find the segments referenced (convert from 1-based to 0-based)
    try:
      srcxml, srcstart, srcend = getxmlitem(srcroot, args.indir, args.srclang, srcid, srcxml)
      trgxml, trgstart, trgend = getxmlitem(trgroot, args.indir, args.trglang, trgid, trgxml)
    except TypeError:
      continue
    # append or update alignment list
    if len(charalignments[srcroot]) > 0:
      lastlist = charalignments[srcroot][-1]
      if lastlist[0] == srcstart and lastlist[1] == srcend:
        lastlist[3] = trgend
        charalignments[srcroot].pop()
      elif lastlist[2] == trgstart and lastlist[3] == trgend:
        lastlist[1] = srcend
        charalignments[srcroot].pop()
      else:
        lastlist = [srcstart, srcend, trgstart, trgend]
      charalignments[srcroot].append(lastlist)
    else:
      charalignments[srcroot].append([srcstart, srcend, trgstart, trgend])
  # write charalignments per file
  for fileid, offsetlist in charalignments.items():
    ofile = open(os.path.join(args.outdir, "%s.align" % fileid), 'w')
    for ss, se, ts, te in offsetlist:
      ofile.write("%d\t%d\t%d\t%d\n" % (ss, se-ss+1, ts, te-ts+1))
    ofile.close()

if __name__ == '__main__':
  main()

