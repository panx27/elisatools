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

def addonoffarg(parser, arg, dest=None, default=True, help="TODO"):
  ''' add the switches --arg and --no-arg that set parser.arg to true/false, respectively'''
  group = parser.add_mutually_exclusive_group()
  dest = arg if dest is None else dest
  group.add_argument('--%s' % arg, dest=dest, action='store_true', default=default, help=help)
  group.add_argument('--no-%s' % arg, dest=dest, action='store_false', default=default, help="See --%s" % arg)

def main():
  parser = argparse.ArgumentParser(description="merge xml files by adding a particular node type to a particular root type",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--infiles", "-i", nargs='+', type=argparse.FileType('r'), default=sys.stdin, help="input files")
  parser.add_argument("--root", "-r", default="ELISA_LRLP_CORPUS", help="parent of merged nodes")
  parser.add_argument("--node", "-n", default="DOCUMENT", help="type of merged nodes")
  parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('w'), default=sys.stdout, help="output file")

  workdir = tempfile.mkdtemp(prefix=os.path.basename(__file__), dir=os.getenv('TMPDIR', '/tmp'))

  def cleanwork():
    shutil.rmtree(workdir, ignore_errors=True)
  atexit.register(cleanwork)


  try:
    args = parser.parse_args()
  except IOError as msg:
    parser.error(str(msg))

  infiles = [prepfile(x, 'r') for x in args.infiles]
  outfile = prepfile(args.outfile, 'w')

  roots = [ET.parse(x) for x in infiles]
  prime = roots[0].getroot()
  if prime.tag != args.root:
    prime = prime.find(".//%s" % args.root)
  rest = roots[1:]
  for doc in rest:
    for node in doc.findall(".//%s" % args.node):
      prime.append(node)
  outfile.write(ET.tostring(prime, pretty_print=True, encoding='utf-8').decode('utf-8'))

if __name__ == '__main__':
  main()
