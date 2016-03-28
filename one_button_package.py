#!/usr/bin/env python3

import argparse
import sys
import codecs

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

  # package up audio and ephemera
  steps.append(Step('make_tarball.py',
                    help="package ephemera"))
  stepsbyname["tar-ephemera"]=steps[-1]

  # make_parallel_release.py
  for i in ('train', 'dev', 'test', 'syscomb', 'eval'):
    steps.append(Step('make_parallel_release.py',
                      help="package parallel flat %s data" % i))
    stepsbyname["parallel-%s" % i]=steps[-1]

  # package up everything
  steps.append(Step('make_tarball.py',
                    help="final package"))
  stepsbyname["tar-all"]=steps[-1]

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
  except IOError as msg:
    parser.error(str(msg))

  rootdir = args.root
  language = args.language
  start = args.start
  stop = args.stop + 1

  finalitems = []
  # READMES
  finalitems.append(os.path.join(scriptdir, "README.mono"))
  finalitems.append(os.path.join(scriptdir, "README.parallel"))
  # MONO RELEASE
  psmoutpath = os.path.join(rootdir, 'psm.ann')
  entityoutpath = os.path.join(rootdir, 'entity.ann')
  monooutdir = os.path.join(rootdir, 'mono', 'extracted')
  monoxml = os.path.join(rootdir, 'elisa.%s.y%dr%d.v%d.xml.gz' % \
                         (language, args.year, args.part, args.version))
  paradir = os.path.join(rootdir, 'parallel')
  finalitems.append(monoxml)

  manarg = ' '.join([re.sub('.manifest', '', f) for f in os.listdir \
                     (monooutdir)if re.match('(.+)\.manifest', f)])
  monoerr = os.path.join(rootdir, 'make_mono_release.err')
  stepsbyname["make_mono_release.py"].argstring = "-r %s -l %s -c %s" % (monooutdir, language, manarg)
  if os.path.exists(entityoutpath):
    stepsbyname["make_mono_release.py"].argstring+= (" -a "+entityoutpath)
  if os.path.exists(psmoutpath):
    stepsbyname["make_mono_release.py"].argstring+= (" -p "+psmoutpath)
  stepsbyname["make_mono_release.py"].argstring+= (" -pa %s | gzip > %s" % \
                                                         (paradir, monoxml))
  stepsbyname["make_mono_release.py"].stderr = monoerr

  # EPHEMERA PACKAGE
  ephemerapack = os.path.join(rootdir, 'elisa.%s.additional.y%dr%d.v%d.tgz' % \
                                                        (language, args.year,
                                                         args.part, args.version))
  finalitems.append(ephemerapack)
  stepsbyname["tar-ephemera"].argstring = "-p additional -i %s -o %s" % \
                                          (os.path.join(rootdir, 'ephemera', '*'),
                                           ephemerapack)
  stepsbyname["tar-ephemera"].stderr = os.path.join(rootdir, 'tar_ephemera.err')

  # PARALLEL RELEASES
  for i in ('train', 'dev', 'test', 'syscomb', 'eval'):
    paralleloutdir = os.path.join(rootdir, 'parallel', 'splits', i)
    parallelxml = os.path.join(rootdir,
                               'elisa.%s-eng.%s.y%dr%d.v%d.xml.gz' % \
                             (language, i, args.year, args.part, args.version))
    if i != "eval":
      finalitems.append(parallelxml)
    parallelerr = os.path.join(rootdir, 'make_parallel_release_%s.err' % i)

    pmanarg = ' '.join([re.sub('.eng.manifest', '', f) for f in os.listdir \
                      (paralleloutdir) if re.match('(.+)\.eng.manifest',f)])
    extra = "-e" if i == "eval" else ""
    stepsbyname["parallel-%s" % i] \
      .argstring = "-r %s -l %s -c %s"% (paralleloutdir, language, pmanarg)
    if os.path.exists(entityoutpath):
      stepsbyname["parallel-%s" % i] \
      .argstring+= (" -a "+entityoutpath)
    if os.path.exists(psmoutpath):
      stepsbyname["parallel-%s" % i] \
      .argstring+= (" -p "+psmoutpath)
    stepsbyname["parallel-%s" % i] \
      .argstring+= (" %s | gzip > %s" % \
                          (extra, parallelxml))
    stepsbyname["parallel-%s" % i].stderr = parallelerr

  # FINAL PACKAGE
  finalpack = os.path.join(rootdir, 'elisa.%s.package.y%dr%d.v%d.tgz' % \
                           (language, args.year, args.part, args.version))
  finalpackprefix = os.path.basename(finalpack)[:-4]
  stepsbyname["tar-all"].argstring = "-p %s -i %s -o %s" % \
                                     (finalpackprefix, ' '.join(finalitems), finalpack)

  for step in steps[start:stop]:
    step.run()

  print("Done")

if __name__ == '__main__':
  main()
