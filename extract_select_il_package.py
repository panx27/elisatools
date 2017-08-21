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
import gzip
import tempfile
import shutil
import atexit
from subprocess import run, STDOUT, PIPE
import shlex
from jmutil import mkdir_p

scriptdir = os.path.dirname(os.path.abspath(__file__))


reader = codecs.getreader('utf8')
writer = codecs.getwriter('utf8')

def dorun(cmd, log=sys.stderr, cmdlog=None):
  ''' run a command; log the calling and the output '''
  if cmdlog == None:
    cmdlog = log
  else:
    cmdlog = prepfile(cmdlog, 'w')
    cmdlog.write(cmd+"\n")
  log.write(cmd+"\n")
  cmdlog.write(run(shlex.split(cmd), check=True, stderr=STDOUT, stdout=PIPE).stdout.decode('utf-8'))

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
  parser = argparse.ArgumentParser(description="create elisa pack out of il pack",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  addonoffarg(parser, 'debug', help="debug mode", default=False)
  parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('w'), default=sys.stdout, help="output file")
  parser.add_argument("--tarball", "-t", required=True, help="input tarball")
  parser.add_argument("--language", "-l", required=True, help="iso 639 code/il code")
  parser.add_argument("--dst", "-d", required=True, help="directory of unpacking")
  parser.add_argument("--year", "-y", type=int, default=1, help="year of the eval")
  parser.add_argument("--version", "-v", type=int, default=1, help="version of the eval")
  parser.add_argument("--release", "-r", type=int, default=1, help="release of the eval")
  parser.add_argument("--ruby", default="/Users/jonmay/.rvm/rubies/ruby-2.3.0/bin/ruby",  help="path to good ruby")
  parser.add_argument("--lex", default="il3", help="lex variant; probably have to make a new one each year")
  parser.add_argument("--key", "-k", default=None, type=str, help="set 0 key")
  parser.add_argument("--sets", "-s", nargs='+', default=['syscomb', 'test', 'dev'], type=str, help="list of sets to make")
  parser.add_argument("--sizes", "-z", nargs='+', default=['10000', '10000', '20000'], type=str, help="list of set sizes")
  parser.add_argument("--devset", default=None, type=str, help="set of mandatory documents in the devset")
  addonoffarg(parser, 'swap', help="swap src/translation in found files", default=True)
  addonoffarg(parser, 'allperseg', help="divide persegment instead of perdoc", default=False)




  try:
    args = parser.parse_args()
  except IOError as msg:
    parser.error(str(msg))

  workdir = tempfile.mkdtemp(prefix=os.path.basename(__file__), dir=os.getenv('TMPDIR', '/tmp'))

  def cleanwork():
    shutil.rmtree(workdir, ignore_errors=True)
  if args.debug:
    print(workdir)
  else:
    atexit.register(cleanwork)

  if len(args.sets) != len(args.sizes):
    sys.stderr.write("sets and sizes must match!")
  outfile = prepfile(args.outfile, 'w')
  outdir=os.path.join(args.dst, args.language)
  mkdir_p(outdir)
  lrlpcmd = "{script}/one_button_lrlp.py --lexversion {lex} --evalil -t {tarball} -l {lang} -r {dst} --ruby {ruby}".format(script=scriptdir, lex=args.lex, tarball=args.tarball, lang=args.language, dst=args.dst, ruby=args.ruby)
  if args.key is not None:
    lrlpcmd += " -k {} -S set0".format(args.key)
  if args.swap:
    lrlpcmd += " --swap"
  dorun(lrlpcmd, log=outfile, cmdlog=os.path.join(outdir, 'one_button_lrlp.err'))
  subcmd = "{script}/subselect_data.py -i {outdir}/parallel -e filtered -l {lang} -s {sizes} -c {sets} -t {script}/incidentvocab".format(script=scriptdir, outdir=outdir, lang=args.language, sets=' '.join(args.sets), sizes=' '.join(args.sizes))
  if args.devset is not None:
    subcmd += " -d {}".format(args.devset)
  if args.allperseg:
    subcmd += " --allperseg"
  dorun(subcmd, log=outfile, cmdlog=os.path.join(outdir, 'subselect_data.err'))
  pkgcmd = "{script}/one_button_package.py --sets {sets} -l {lang} -y {year} -r {release} -v {version} -r {outdir}".format(script=scriptdir, year=args.year, version=args.version, release=args.release, lang=args.language, outdir=outdir, sets=' '.join(args.sets))
  dorun(pkgcmd, log=outfile, cmdlog=os.path.join(outdir, 'one_button_package.err'))
  subsets = ["train", "rejected"]+args.sets
  for subset in subsets:
    catcmd="{script}/elisa2flat.py -f FULL_ID_SOURCE SOURCE.id ORIG_SOURCE ORIG_TARGET -i {outdir}/elisa.{lang}-eng.{subset}.y{year}r{release}.v{ver}.xml.gz -o {outdir}/{subset}.tab".format(script=scriptdir, year=args.year, subset=subset,ver=args.version, release=args.release, lang=args.language, outdir=outdir)
    dorun(catcmd, log=outfile)
    sampcmd="{script}/sample.py -i {outdir}/{subset}.tab -s 10 -o {outdir}/{subset}.samples".format(script=scriptdir, subset=subset, outdir=outdir)
    dorun(sampcmd, log=outfile)
  catcmd="{script}/elisa2flat.py -f FULL_ID_SOURCE SOURCE.id ORIG_SOURCE -i {outdir}/elisa.{lang}.y{year}r{release}.v{ver}.xml.gz -o {outdir}/{lang}.tab".format(script=scriptdir, year=args.year, ver=args.version, release=args.release, lang=args.language, outdir=outdir)
  dorun(catcmd, log=outfile)
  sampcmd="{script}/sample.py -i {outdir}/{lang}.tab -s 10 -o {outdir}/{lang}.samples".format(script=scriptdir, lang=args.language, outdir=outdir)
  dorun(sampcmd, log=outfile)
  dorun("ls -l {}".format(outdir))
if __name__ == '__main__':
  main()
