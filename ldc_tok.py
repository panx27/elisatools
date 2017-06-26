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
import os
import gzip
import tempfile
import shutil
import atexit
from lputil import mkdir_p, is_sn
from subprocess import check_call
import shlex
from glob import iglob

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


def tokrsd(dldir, ruby, exec, param, workdir):
  ''' create ltfs from rsds '''
  rsddir = dldir
  parent = os.path.dirname(rsddir)
  ltfdir = os.path.join(parent, 'ltf')
  if not os.path.exists(rsddir):
    sys.stderr.write("Directories not set up properly; couldn't find {}\n".format(rsddir))
    sys.exit(1)
  mkdir_p(ltfdir)
  listfile = os.path.join(workdir, 'list')
  lfh = prepfile(listfile, 'w')
  for l in iglob(os.path.join(rsddir, '*.rsd.txt')):
    lfh.write("{}\n".format(l))
  lfh.close()
  paramtxt = "" if param is None else "-t {}".format(param)
  cmd = "{} {} {} {}".format(ruby, exec, paramtxt, listfile)
  return check_call(shlex.split(cmd))

def validate(dldir, lrlpdir, logfile, args):
  ''' compare files about to be replaced '''
  tweetdir = dldir
  if not os.path.exists(tweetdir):
    sys.stderr.write("Directories not set up properly; couldn't find {}\n".format(tweetdir))
    sys.exit(1)
  counts = dd(int)
  for file in os.listdir(tweetdir):
    def log(msg):
      if args.verbose:
        logfile.write("{} for {}\n".format(msg, file))

    if not file.endswith(".ltf.xml"):
      continue
    counts["file"]+=1
    handfile = os.path.join(tweetdir, file)
    valfile = os.path.join(lrlpdir, file)
    if not os.path.exists(valfile):
      counts["no_file"]+=1
      log("Can't validate; no {}".format(valfile))
      continue
    handx = ET.parse(handfile)
    valx = ET.parse(valfile)
    try:
      if handx.find(".//DOC").get('raw_text_md5') != valx.find(".//DOC").get('raw_text_md5'):
        counts["bad_hash"]+=1
        log("md5 mismatch")
      if handx.find(".//DOC").get('raw_text_char_length') != valx.find(".//DOC").get('raw_text_char_length'):
        counts["bad_raw_text"]+=1
        log("raw char mismatch")
      handsegs = handx.findall(".//SEG")
      valsegs = valx.findall(".//SEG")
      if len(handsegs) != len(valsegs):
        counts["segcount"]+=1
        log("seg count mismatch: {} vs {}".format(len(handsegs), len(valsegs)))
      for hs, vs in zip(handsegs, valsegs):
        if hs.get("start_char") != vs.get("start_char") or hs.get("end_char") != vs.get("end_char"):
          counts["bad_seg_offset"]+=1
          log("segment offset mismatch: {} vs {} or {} vs {}".format(hs.get("start_char"), vs.get("start_char"),  hs.get("end_char"), vs.get("end_char")))
          continue
        for hst, vst in zip(hs.findall(".//TOKEN"), vs.findall(".//TOKEN")):
          offsets = [hst.get("start_char"), vst.get("start_char"), hst.get("end_char"), vst.get("end_char")]
          if offsets[0] != offsets[1] or offsets[2] != offsets[3]:
            counts["bad_tok_offset"]
            log("token offset mismatch in {}: {} vs {} or {} vs {}".format(hst.get("id"), *offsets))
    except AttributeError:
      counts["bad_xml"]+=1
      log("bad xml traversal for {}".format(file))
      continue
  logfile.write("Summary:\n")
  for k, v in counts.items():
    if v > 0:
      logfile.write("{} = {}\n".format(k, v))


def relocate_ltf(dldir, lrlpdir, logfile):
  ''' relocate files and replace them '''
  # source of the new files
  parent = os.path.dirname(dldir)
  repldir = os.path.join(parent, 'ltf')
  if not os.path.exists(repldir):
    sys.stderr.write("Directories not set up properly; couldn't find {}\n".format(repldir))
    sys.exit(1)
  bkpdir = os.path.join(parent, 'ltf.retired')
  mkdir_p(bkpdir)
  mkdir_p(lrlpdir)
  for file in os.listdir(lrlpdir):
    if not is_sn(file) or not file.endswith(".ltf.xml"):
      continue
    oldfile = os.path.join(lrlpdir, file)
    bkpfile = os.path.join(bkpdir, file)
    shutil.move(oldfile, bkpfile)
  for file in os.listdir(repldir):
    if not file.endswith(".ltf.xml"):
      continue
    dstfile = os.path.join(lrlpdir, file)
    replfile = os.path.join(repldir, file)
    # introduce the replacement file in the new  location
    shutil.copyfile(replfile, dstfile)

def zip_and_copy (workdir, indir, outfile, logfile):
  ''' zip up directory tree; requires a relocation for files to all line up right '''
  if not os.path.exists(indir):
    sys.stderr.write("Directories not set up properly; couldn't find input {}\n".format(indir))
    sys.exit(1)
  # trying to get an ltf directory underneath so that zip file has ltf prefix before everything
  realwork = os.path.join(workdir, 'foo')
  shutil.copytree(indir, os.path.join(realwork, 'ltf'))
  mkdir_p(os.path.dirname(outfile))
  shutil.make_archive(outfile, 'zip', realwork)

  

def main():
  parser = argparse.ArgumentParser(description="wrapper for ldc ruby tok that identifies file list, sets things up",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  addonoffarg(parser, 'debug', help="debug mode", default=False)
  parser.add_argument("--ruby", "-r", default="/Users/jonmay/.rvm/rubies/ruby-2.3.0/bin/ruby", help="flavor of ruby")
  parser.add_argument("--dldir", "-d", required=True, help="rsd directory containing original tweets (probably subdir of 'tweet'; an 'ltf' will be built alongside it")
  parser.add_argument("--lrlpdir", "-l", required=True, help="the 'ltf' directory in an expanded lrlp that contains anonymized tweet files (usu. data/translation/from_xxx/xxx/ltf for lang xxx)")
  parser.add_argument("--monodir", "-m", required=True, help="the directory in the mono tree for treating this data as monolingual (usu. data/monolingual_text)")
  parser.add_argument("--mononame", default="tweets.ltf", help="monolingual ltf ball (will have 'zip' appended)")
  parser.add_argument("--exec", "-e", required=True, help="path to ldc tokenizer; usually in tools/ldclib/bin/token_parse.rb of the lrlp")
  parser.add_argument("--param", "-p", required=True, help="path to ldc tokenizer parameter set; usually tools/tokenization_parameters.v4.0.yaml in the lrlp", default=None)
  parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('w'), default=sys.stdout, help="output file")
  addonoffarg(parser, 'verbose', help="print specific errors per file", default=False)
  try:
    args = parser.parse_args()
  except IOError as msg:
    parser.error(str(msg))

  outfile = prepfile(args.outfile, 'w')
  workdir = tempfile.mkdtemp(prefix=os.path.basename(__file__), dir=os.getenv('TMPDIR', '/tmp'))

  def cleanwork():
    shutil.rmtree(workdir, ignore_errors=True)
  if args.debug:
    print(workdir)
  else:
    atexit.register(cleanwork)
  retval = tokrsd(args.dldir, args.ruby, args.exec, args.param, workdir)
  if retval != 0:
    sys.stderr.write("Error tokenizing: {}\n".format(retval))
    sys.exit(retval)
  validate(args.dldir, args.lrlpdir, outfile, args)
  relocate_ltf(args.dldir, args.lrlpdir, outfile)
  zip_and_copy(workdir, args.lrlpdir, os.path.join(args.monodir, args.mononame), outfile)

if __name__ == '__main__':
  main()
