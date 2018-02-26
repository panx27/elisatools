#!/usr/bin/env python3
import argparse
import sys
import codecs
if sys.version_info[0] == 2:
  from itertools import izip
else:
  izip = zip
import tarfile as tf
from collections import defaultdict as dd
import lxml.etree as ET
import re
import os.path
import gzip
import tempfile
import shutil
import atexit

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

def addonoffarg(parser, arg, dest=None, default=True, help="TODO"):
  ''' add the switches --arg and --no-arg that set parser.arg to true/false, respectively'''
  group = parser.add_mutually_exclusive_group()
  dest = arg if dest is None else dest
  group.add_argument('--%s' % arg, dest=dest, action='store_true', default=default, help=help)
  group.add_argument('--no-%s' % arg, dest=dest, action='store_false', default=default, help="See --%s" % arg)

def main():
  parser = argparse.ArgumentParser(description="given submission tarball and unannotated elisa xml, produce annotated elisa xml",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--nistfile", "-n", help="nist tarball")
  parser.add_argument("--manfile", "-m", nargs='?', type=argparse.FileType('r'), default=None, help="optional manifest file listing docs to apply this to")
  parser.add_argument("--elisafile", "-e", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="elisa xml(.gz) file")
  parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('w'), default=sys.stdout, help="output file")


  workdir = tempfile.mkdtemp(prefix=os.path.basename(__file__), dir=os.getenv('TMPDIR', '/tmp'))

  def cleanwork():
    shutil.rmtree(workdir, ignore_errors=True)
  atexit.register(cleanwork)


  try:
    args = parser.parse_args()
  except IOError as msg:
    parser.error(str(msg))

  elisafile = prepfile(args.elisafile, 'r')
  manfile = None if args.manfile is None else prepfile(args.manfile, 'r')
  outfile = prepfile(args.outfile, 'w')
  
  archive = tf.open(args.nistfile, 'r:gz')

  manifest = None if manfile is None else set(map(lambda x: x.strip().split('\t')[0], manfile.readlines()))
  root = ET.parse(elisafile)

  removedocs = set()
  for file in archive:
    if file.size < 20:
      continue
    if not file.name.endswith("xml"):
      continue
    #print("file: "+file.name)
    docid = os.path.basename(file.name).split('.')[0]
    #print("doc: "+docid)
    if manifest is not None and docid not in manifest:
      removedocs.add(docid)
      continue
    with archive.extractfile(file) as ifh:
      xobj = ET.parse(ifh)
      for submitdoc in xobj.findall(".//doc"):
        docid = submitdoc.get("docid")
        #print("doc: "+docid)
        elisadoc = root.find(".//DOCUMENT[@id='%s']" % docid)
        if elisadoc is None:
          sys.stderr.write("Couldn't find %s in elisa doc!\n" % docid)
          sys.exit(1)
          #continue
        for elisaseg in elisadoc.findall(".//SOURCE"):
          segid = elisaseg.find(".//ORIG_SEG_ID").text
          #print(segid)
          submitseg = submitdoc.find(".//seg[@id='%s']" % segid)
          if submitseg is None:
            sys.stderr.write("Couldn't find %s in submit doc %s!\n" % (segid, docid))
            thetext = "NONE"
          else:
            thetext = submitseg.text
          ET.SubElement(ET.SubElement(ET.SubElement(elisaseg, 'NBEST'), 'HYP'), 'TEXT').text = thetext
  remcount=0
  for docid in removedocs:
    elisadoc = root.find(".//DOCUMENT[@id='%s']" % docid)
    if elisadoc is not None:
      elisadoc.getparent().remove(elisadoc)
      remcount+=1
  sys.stderr.write("Removed %d nodes from elisa doc\n" % remcount)
  outfile.write(ET.tostring(root, pretty_print=True, encoding='utf-8').decode('utf-8'))

if __name__ == '__main__':
  main()
