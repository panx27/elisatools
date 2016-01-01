#!/usr/bin/env python3

import argparse
import sys
import codecs
from collections import defaultdict as dd
import re
import os
import os.path
scriptdir = os.path.dirname(os.path.abspath(__file__))


#http://code.activestate.com/recipes/496682-make-ranges-of-contiguous-numbers-from-a-list-of-i/
def list2range(lst):
    '''make iterator of ranges of contiguous numbers from a list of integers'''

    tmplst = lst[:]
    tmplst.sort()
    start = tmplst[0]

    currentrange = [start, start + 1]

    for item in tmplst[1:]:
        if currentrange[1] == item:
            # contiguous
            currentrange[1] += 1
        else:
            # new range start
            yield tuple(currentrange)
            currentrange = [item, item + 1]

    # last range
    yield tuple(currentrange)

def main():
  parser = argparse.ArgumentParser(description="Build train/dev/test sets from parallel data",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--infile", "-i", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="input file; tab-separated source and target texts")
  parser.add_argument("--smalltrainsize", default=150000, help="number of words in small training")
  parser.add_argument("--mediumtrainsize", default=300000, help="number of words in medium training")
  parser.add_argument("--largetrainsize", default=600000, help="number of words in large training")
  parser.add_argument("--smalllabel", default='small', help="label to distinguish small training")
  parser.add_argument("--mediumlabel", default='medium', help="label to distinguish medium training")
  parser.add_argument("--largelabel", default='large', help="label to distinguish large training")
  parser.add_argument("--traindevgap", default=10000, help="number of words to skip between train and dev")
  parser.add_argument("--devsize", default=20000, help="number of words in dev after filtering")
  parser.add_argument("--devtestgap", default=100000, help="number of words to skip between dev and test")
  parser.add_argument("--testsize", default=20000, help="number of words in test")
  parser.add_argument("--outdir", "-o", help="output directory prefix")
  parser.add_argument("--src", "-s", default="tur", help="source language (ISO 639.3-letter code)")
  parser.add_argument("--trg", "-t", default="eng", help="target language (ISO 639.3-letter code)")
  parser.add_argument("--label", "-l", default="tok.lc", help="label applied to data set. filenames will be OUTDIR/{training,dev,test}.LABEL.{SRC,TRG}")

    

  try:
    args = parser.parse_args()
  except IOError as msg:
    parser.error(str(msg))

  reader = codecs.getreader('utf8')
  writer = codecs.getwriter('utf8')
  infile = reader(args.infile)
  try:
    os.makedirs(args.outdir)
  except OSError:
    pass
  outfiles = [(writer(open(os.path.join(args.outdir, "training.%s.%s.%s" % (args.largelabel,args.label, args.src)), 'w')),
               writer(open(os.path.join(args.outdir, "training.%s.%s.%s" % (args.largelabel,args.label, args.trg)), 'w')),
               writer(open(os.path.join(args.outdir, "training.%s.manifest" % args.largelabel), 'w'))),
              (writer(open(os.path.join(args.outdir, "dev.%s.%s" % (args.label, args.src)), 'w')),
               writer(open(os.path.join(args.outdir, "dev.%s.%s" % (args.label, args.trg)), 'w')),
               writer(open(os.path.join(args.outdir, "dev.manifest"), 'w'))),
              (writer(open(os.path.join(args.outdir, "test.%s.%s" % (args.label, args.src)), 'w')),
               writer(open(os.path.join(args.outdir, "test.%s.%s" % (args.label, args.trg)), 'w')),
               writer(open(os.path.join(args.outdir, "test.manifest"), 'w')))]

  
  smallertrains = [(writer(open(os.path.join(args.outdir, "training.%s.%s.%s" % (args.smalllabel,args.label, args.src)), 'w')),
                    writer(open(os.path.join(args.outdir, "training.%s.%s.%s" % (args.smalllabel,args.label, args.trg)), 'w')),
                    writer(open(os.path.join(args.outdir, "training.%s.manifest" % args.smalllabel), 'w'))),
                   (writer(open(os.path.join(args.outdir, "training.%s.%s.%s" % (args.mediumlabel,args.label, args.src)), 'w')),
                    writer(open(os.path.join(args.outdir, "training.%s.%s.%s" % (args.mediumlabel,args.label, args.trg)), 'w')),
                    writer(open(os.path.join(args.outdir, "training.%s.manifest" % args.mediumlabel), 'w')))]

  mansed = []
  for mantype in ["training.%s" % args.largelabel, "training.%s" % args.smalllabel, "training.%s" % args.mediumlabel, "dev", "test"]:
    mansed.append((os.path.join(args.outdir, "%s.manifest" % mantype), 
                   os.path.join(args.outdir, "%s.sed" % mantype)))

  # filter out bad sentences, especially from dev
  # write manifest indicating the original line number of each line of train/dev/test
  # write scripts for reconstructing the files from scratch from source

  milestones = [args.largetrainsize, # on
                args.largetrainsize+args.traindevgap, # off
                args.largetrainsize+args.traindevgap+args.devsize, # on
                args.largetrainsize+args.traindevgap+args.devsize+args.devtestgap, # off
                args.largetrainsize+args.traindevgap+args.devsize+args.devtestgap+args.testsize] # on
  devstart =    args.largetrainsize+args.traindevgap
  devend =      args.largetrainsize+args.traindevgap+args.devsize
  counter = 0
  outsrc, outtrg, outman = outfiles.pop(0)
  writing = True
  milestone = milestones.pop(0)
  for lnum, line in enumerate(infile, start=1):
    if counter > milestone:
      writing = not writing
      if writing:
        outsrc, outtrg, outman = outfiles.pop(0)
      else:
        if len(outfiles) == 0:
          break
        outsrc.close()
        outtrg.close()
        outman.close()
        outsrc, outtrg, outman = [writer(open(x, 'w')) for x in [os.devnull]*3]
      milestone = milestones.pop(0)
    if len(smallertrains) == 2 and counter > args.smalltrainsize:
      [x.close() for x in smallertrains.pop(0)]
    if len(smallertrains) == 1 and counter > args.mediumtrainsize:
      [x.close() for x in smallertrains.pop(0)]
      
    src, trg = line.rstrip('\n').split('\t')
    # filters for dev
    if counter > devstart and counter < devend:
      stoks = src.split()
      ttoks = trg.split()
      if len(stoks) < 3 or len(stoks) > 80 or\
      len(ttoks) < 3 or len(ttoks) > 80:
        continue
      ratio = (len(ttoks)+0.0)/len(stoks)
      if ratio > 10 or ratio < 0.1:
        continue
    counter += len(trg.split())
    for sfile, tfile, mfile in smallertrains:
      sfile.write(src+"\n")
      tfile.write(trg+"\n")
      mfile.write("%d\n" % lnum)
    outsrc.write(src+"\n")
    outtrg.write(trg+"\n")
    outman.write("%d\n" % lnum)
  outsrc.close()
  outtrg.close()
  outman.close()
  if counter < milestone:
    sys.stderr.write("Warning: Input too small to meet all milestones; stopped at %d\n" + counter)
  for manfile, sedfile in mansed:
    itemlist = list(map(int, open(manfile).readlines()))
    ofh = open(sedfile, 'w')
    ofh.write("#n\n")
    for s, e in list2range(itemlist):
      ofh.write("%d,%dp;\n" % (s, e-1))
    ofh.close()

if __name__ == '__main__':
  main()
