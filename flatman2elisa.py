#!/usr/bin/env python3
# code by Jon May [jonmay@isi.edu]
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
import tempfile
import shutil
import atexit
import lxml.etree as ET
scriptdir = os.path.dirname(os.path.abspath(__file__))

reader = codecs.getreader('utf8')
writer = codecs.getwriter('utf8')


def prepfile(fh, code):
  if type(fh) is str:
    fh = open(fh, code)
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

def addonoffarg(parser, arg, dest=None, default=True, help="TODO"):
  ''' add the switches --arg and --no-arg that set parser.arg to true/false, respectively'''
  group = parser.add_mutually_exclusive_group()
  dest = arg if dest is None else dest
  group.add_argument('--%s' % arg, dest=dest, action='store_true', default=default, help=help)
  group.add_argument('--no-%s' % arg, dest=dest, action='store_false', default=default, help="See --%s" % arg)

def main():
  parser = argparse.ArgumentParser(description="flat file and segment id man file plus existing elisa file -> new elisa hypothesis file",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--infile", "-i", type=argparse.FileType('r'), default=sys.stdin, help="input file")
  parser.add_argument("--manfile", "-m", type=argparse.FileType('r'), default=sys.stdin, help="input manifest")
  parser.add_argument("--elisafile", "-e", type=argparse.FileType('r'), default=sys.stdin, help="model elisa file")
  parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('w'), default=sys.stdout, help="output xml file")

  workdir = tempfile.mkdtemp(prefix=os.path.basename(__file__), dir=os.getenv('TMPDIR', '/tmp'))

  def cleanwork():
    shutil.rmtree(workdir, ignore_errors=True)
  atexit.register(cleanwork)


  try:
    args = parser.parse_args()
  except IOError as msg:
    parser.error(str(msg))

  infile =  prepfile(args.infile, 'r')
  manfile =  prepfile(args.manfile, 'r')
  elisafile =  prepfile(args.elisafile, 'r')
  outfile = prepfile(args.outfile, 'w')

  root = ET.parse(elisafile)
  texts = {}
  for id, text in zip(manfile, infile):
    texts[id.strip()]=text.strip()
  for node in root.findall("/DOCUMENT/SEGMENT/SOURCE"):
    id = node.get('id')
    if id not in texts:
      sys.stderr.write("Couldn't find {}\n".format(id))
      continue
    old = node.find(".//NBEST")
    if old is not None:
      node.remove(old)
    nb = ET.SubElement(node, 'NBEST')
    hyp = ET.SubElement(nb, 'HYP')
    txt = ET.SubElement(hyp, 'TEXT')
    txt.text = texts[id]
  xmlstr=ET.tostring(root, pretty_print=True, encoding='utf-8', xml_declaration=True).decode('utf-8')
  outfile.write(xmlstr+"\n")

if __name__ == '__main__':
  main()
