#!/usr/bin/env python
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
import subprocess
import shlex
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
  parser = argparse.ArgumentParser(description="decrypt bzipped tarred sets",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--rootdir", "-r", help="directory where sets are")
  parser.add_argument("--keys", "-k", nargs='+', default=[], help="decrypt keys")
  parser.add_argument("--sets", "-s", nargs='+', default=[], help="decrypt sets")
  parser.add_argument("--template", default=".tar.bz2.openssl", help="suffix of input files")
  parser.add_argument("--opensslargstr", default="enc -d -aes-256-cbc -salt", help="openssl options")
  parser.add_argument("--tarargstr", default="-jxf", help="tar options")



  try:
    args = parser.parse_args()
  except IOError as msg:
    parser.error(str(msg))

  if len(args.keys) != len(args.sets):
    sys.stderr.write("Must have same number of keys as sets\n")
    sys.exit(1)
  for k, s in zip(args.keys, args.sets):
    infile = os.path.join(args.rootdir, "%s%s" % (s, args.template))
    opensslcmd = "openssl %s -k %s" % (args.opensslargstr, k)
    tarcmd = "tar -C %s %s -" % (args.rootdir, args.tarargstr)
    op = subprocess.Popen(shlex.split(opensslcmd), stdin=open(infile, 'r'), stdout=subprocess.PIPE)
    tp = subprocess.check_call(shlex.split(tarcmd), stdin=op.stdout)

if __name__ == '__main__':
  main()

