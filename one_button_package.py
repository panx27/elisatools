#! /usr/bin/env python
import argparse
import sys
import codecs
from itertools import izip
from collections import defaultdict as dd
import re
import os.path
from lputil import Step, make_action
from subprocess import check_output, check_call, CalledProcessError
scriptdir = os.path.dirname(os.path.abspath(__file__))


def main():
  steps = []
  stepsbyname = {}
  # make_mono_release.py
  steps.append(Step('make_mono_release.py',
                    help="package mono flat data"))
  # TODO: lexicon, audio, readme, tarball
  for step in steps:
    stepsbyname[step.prog] = step

    # make_parallel_release.py
  for i in ('train', 'dev', 'test', 'eval'):
    steps.append(Step('make_parallel_release.py',
                      help="package parallel flat %s data" % i))
    stepsbyname["parallel-%s" % i]=steps[-1]

  parser = argparse.ArgumentParser(description="Process a flattened LRLP into xml tarballed release format",
                                   formatter_class= \
                                   argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--language", "-l", default='uzb',
                      help='three letter code of language')
  parser.add_argument("--version", "-v", type=int, default=1, help='version name of release')
  parser.add_argument("--year", "-yr", type=int, default=1, help='year of release')
  parser.add_argument("--part", "-pt", type=int, default=1, help='part of release')
  parser.add_argument("--root", "-r",
                      help='path to where the flat extraction is/output belongs')
  parser.add_argument("--start", "-s", type=int, default=0,
                      help='step to start at')
  parser.add_argument("--stop", "-p", type=int, default=len(steps)-1,
                      help='step to stop at (inclusive)')
  parser.add_argument("--liststeps", "-x", nargs=0, action=make_action(steps),
                      help='print step list and exit')
  
  try:
    args = parser.parse_args()
  except IOError, msg:
    parser.error(str(msg))

  rootdir = args.root
  language = args.language
  start = args.start
  stop = args.stop + 1


  # MONO RELEASE
  psmoutpath = os.path.join(rootdir, 'psm.ann')
  entityoutpath = os.path.join(rootdir, 'entity.ann')
  monooutdir = os.path.join(rootdir, 'mono', 'extracted')
  monoxml = os.path.join(rootdir,
                         'elisa.%s.y%dr%d.v%d.xml' % \
                         (language, args.year, args.part, args.version))
  manarg = ' '.join([re.sub('.manifest', '', f) for f in os.listdir \
                     (monooutdir)if re.match('(.+)\.manifest', f)])
  monoerr = os.path.join(rootdir, 'make_mono_release.err')
  stepsbyname["make_mono_release.py"].\
    argstring = "-r %s -o %s -l %s -c %s -a %s -p %s" % \
                (monooutdir, monoxml, language, manarg,
                  entityoutpath, psmoutpath)
  stepsbyname["make_mono_release.py"].stderr = monoerr

  # PARALLEL RELEASES
  for i in ('train', 'dev', 'test', 'eval'):
    paralleloutdir = os.path.join(rootdir, 'parallel', 'splits', i)
    parallelxml = os.path.join(rootdir, 
                               'elisa.%s-eng.%s.y%dr%d.v%d.xml' % \
                             (language, i, args.year, args.part, args.version))
    parallelerr = os.path.join(rootdir, 'make_parallel_release.err')

    pmanarg = ' '.join([re.sub('.eng.manifest', '', f) for f in os.listdir \
                      (paralleloutdir) if re.match('(.+)\.eng.manifest',f)])
    extra = "-e" if i == "eval" else ""
    stepsbyname["parallel-%s" % i] \
      .argstring = "-r %s -o %s -l %s -c %s -a %s -p %s %s" % \
                   (paralleloutdir, parallelxml, language, pmanarg,
                    entityoutpath, psmoutpath, extra)
    stepsbyname["parallel-%s" % i].stderr = parallelerr



  for step in steps[start:stop]:
    step.run()

  print "Done"

if __name__ == '__main__':
  main()
