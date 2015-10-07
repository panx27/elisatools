#! /usr/bin/env python

# mt prep script. Specific to isi architecture

import argparse
import sys
import codecs
from itertools import izip
from collections import defaultdict as dd
import re
import os.path
from lputil import mkdir_p
from subprocess import check_output, STDOUT, CalledProcessError
scriptdir = os.path.dirname(os.path.abspath(__file__))


def main():
  parser = argparse.ArgumentParser(description="tokenize test data, write config script, launch test decode",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--sourcefile", "-s", help="input source-side file")
  parser.add_argument("--targetfile", "-t", help="input target-side file")
  parser.add_argument("--key", "-k", default="test", help="name for the experiment")
  parser.add_argument("--tunekey", default="dev", help="name for tuning")
  parser.add_argument("--iter", "-i", type=int, help="iteration of tuning to use")
  parser.add_argument("--outdir", "-o", help="where to write files and run tests. Should also be mt dir")
  parser.add_argument("--pipeline", default="/home/rcf-40/jonmay/projects/sbmt/pipeline.150707", help="mt pipeline")


  try:
    args = parser.parse_args()
  except IOError, msg:
    parser.error(str(msg))

  writer = codecs.getwriter('utf8')
#  outfile = writer(args.outfile)

  # cdec tokenize/lc source side (through qsub)
  # ulf tokenize/lc target side (through qsub)
  # write params file
  # launch prepdecode

  ulftok = os.path.join(scriptdir, 'ulftok.py')
  cdectok = os.path.join(scriptdir, 'cdectok.sh')

  decode = os.path.join(args.pipeline, 'runcorpusdecode.sh')

  sourcebase = os.path.basename(args.sourcefile)
  targetbase = os.path.basename(args.targetfile)

  sourcein = args.sourcefile  
  targetin = args.targetfile  

  sourceout = os.path.join(args.outdir, "%s.tok.lc" % sourcebase)
  targetout = os.path.join(args.outdir, "%s.tok.lc" % targetbase)

  # write here doc
  paramfile = writer(open(os.path.join(args.outdir, "%s.pipeline.resource" % args.key), 'w'))
  paramfile.write("""
corpus: %s
lc-tok-refs:
  - %s
""" % (os.path.basename(sourceout), os.path.basename(targetout)))

  # TODO: could maybe use Step class from one_button_lrlp?
  try:
    sourcetokcmd = "qsubrun %s -i %s -o %s" % (cdectok, sourcein, sourceout)
    sys.stderr.write("Calling "+sourcetokcmd+"\n")
    sourcetokid = check_output(sourcetokcmd, shell=True).strip()

    targettokcmd = "qsubrun %s -i %s -o %s" % (ulftok, targetin, targetout)
    sys.stderr.write("Calling "+targettokcmd+"\n")
    targettokid = check_output(targettokcmd, shell=True).strip()

    # launch decoding when ready
    decodecmd = "qsubrun -W depend=afterok:%s,afterok:%s -- %s %s %s %d" % (sourcetokid, targettokid, decode, args.key, args.tunekey, args.iter)
    sys.stderr.write("Calling "+decodecmd+" from "+args.outdir+"\n")
    decodeid = check_output(decodecmd, shell=True, cwd=args.outdir).strip()
    print "Launched "+decodeid
  except CalledProcessError as exc:
    sys.stderr.write("%s: FAIL: %d %s\n" % (exc.returncode, exc.output))


if __name__ == '__main__':
  main()
