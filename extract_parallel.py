#!/usr/bin/env python3
#-*- coding: utf-8 -*-
import sys

import argparse
import codecs
from collections import defaultdict as dd
import re
import os
import os.path
import shutil
scriptdir = os.path.dirname(os.path.abspath(__file__))
import lputil
import datetime
import xml.etree.ElementTree as ET
from subprocess import check_call, CalledProcessError
from itertools import compress



def printout(prefix, path, src, trg, outdir, origoutdir, cleanorigoutdir, garbageoutdir,
             tokoutdir, cleantokoutdir, morphtokoutdir, cdectokoutdir, cdectoklcoutdir,
             agiletokoutdir, agiletoklcoutdir, morphoutdir, posoutdir,
             agiletokpath, cdectokpath, 
             stp=lputil.selected_translation_pairs, el=lputil.extract_lines,
             tweet=False, swap=False):
  ''' Find files and print them out '''
  src_man_fh=open(os.path.join(outdir, "%s.%s.manifest" % (prefix, src)), 'w')
  trg_man_fh=open(os.path.join(outdir, "%s.%s.manifest" % (prefix, trg)), 'w')

  # open a bunch of file handles
  # third element indicates whether it should actually be opened
  namedirpairs = [('orig', origoutdir,True),
                  ('cleanorig', cleanorigoutdir,False),
                  (       'tok',                       tokoutdir,True),
                  (       'cleantok',                       cleantokoutdir,False),
                  (  'morphtok',                  morphtokoutdir,True),
                  (   'cdectok',                   cdectokoutdir,False),
                  ( 'cdectoklc',                 cdectoklcoutdir,False),
                  (  'agiletok',                  agiletokoutdir,False),
                  ('agiletoklc',                agiletoklcoutdir,False),
                  (     'morph',                     morphoutdir,True),
                  (       'pos',                       posoutdir,True),
                  ]
  outfiles = dd(dict)
  for sidename, side in (('src', src),
                         ('trg', trg)):
    for dirname, dirval, doopen in namedirpairs:
      entry = os.path.join(outdir, dirval, "{}.{}.{}.flat".format(prefix, dirval, side))
      if doopen:
        entry = open(entry, 'w')
      outfiles[sidename][dirname]=entry

  garbagefhs = {}
  garbagedisabled=True
  if garbageoutdir is not None:
    garbagedisabled=False
    src_orig_garbage_fh=open(os.path.join(outdir, garbageoutdir, "%s.%s.flat" % \
                                          (prefix,src)), 'w')
    garbagefhs[outfiles['src']['orig']]=src_orig_garbage_fh
    trg_orig_garbage_fh=open(os.path.join(outdir, garbageoutdir, "%s.%s.flat" % \
                                          (prefix,trg)), 'w')
    garbagefhs[outfiles['trg']['orig']]=trg_orig_garbage_fh
    src_garbage_man_fh=open(os.path.join(outdir, garbageoutdir, "%s.%s.manifest" % (prefix, src)), 'w')
    garbagefhs[src_man_fh]=src_garbage_man_fh
    trg_garbage_man_fh=open(os.path.join(outdir, garbageoutdir, "%s.%s.manifest" % (prefix, trg)), 'w')
    garbagefhs[trg_man_fh]=trg_garbage_man_fh

  (stpsrc, stptrg) = (trg, src) if swap else (src, trg)
  for m in stp(path, src=stpsrc, trg=stptrg, xml=True, tweet=tweet):

    if not tweet:
      sdata, tdata = el(*m)
    else:
      sdata, tdata = el(*m, sxml=False, txml=True)

    # found data sometimes seems to require swap behavior
    if swap:
      sdata, tdata = tdata, sdata
      
    if sdata is None or tdata is None:
      sys.stderr.write("Warning: empty files:\n%s or %s\n" % (m[0], m[1]))
      continue
    # Strict rejection of different length lines. If these are desired,
    # do gale & church or brown et al or something similar here
    slen = len(sdata["ORIG"])
    tlen = len(tdata["ORIG"])
    #print(slen,tlen)
    if slen != tlen:
      sys.stderr.write("Warning: different number of lines in files:\n" \
                       "%s %d\n%s %d\n" % (m[0], slen, m[1], tlen))
      continue

    # filter out control code-bearing lines here. mask out the data from all fields
    garbagemask = lputil.getgarbagemask(sdata["ORIG"], tdata["ORIG"], disabled=garbagedisabled)

    goodmask = [not x for x in garbagemask]
    ### Write original
    for fh, data in zip((outfiles['src']['orig'], outfiles['trg']['orig']), (sdata["ORIG"], tdata["ORIG"])):
      for line in compress(data, garbagemask):
        fh.write(line)
      ### Write garbage original
      if not garbagedisabled:
        for line in compress(data, goodmask):
          garbagefhs[fh].write(line)
    
    ### Write manifest
    if not tweet:
      try:
        for fh, fname, tupgen in zip((src_man_fh, trg_man_fh), (m[0], m[1]),
                                     (list(zip(sdata["DOCID"], sdata["SEGID"],
                                          sdata["START"], sdata["END"])),
                                      list(zip(tdata["DOCID"], tdata["SEGID"],
                                          tdata["START"], tdata["END"])))):
          for tup in compress(tupgen, garbagemask):
            fh.write("\t".join(map(str, (fname,)+tup))+"\n")
          if not garbagedisabled:
            for tup in compress(tupgen, goodmask):
              garbagefhs[fh].write("\t".join(map(str, (fname,)+tup))+"\n")
      except:
        sys.stderr.write(src_man_fh.name)
        #sys.stderr.write(fname)
        raise
    else:
      # Source
      fh = src_man_fh
      field = sdata["DOCID"]
      for line in compress(field, garbagemask):
        line = line.strip()
        fh.write('%s\t%s\n' % (line,
#                               line))
                               re.search('.+/(\S*?)\.', line).group(1)))
      if not garbagedisabled:
        for line in compress(field, goodmask):
          line = line.strip()
          garbagefhs[fh].write('%s\t%s\n' % (line,
  #                                           line))
                                 re.search('.+/(\S*?)\.', line).group(1)))

      # Target
      try:
        fh = trg_man_fh
        fname = m[1]
        for tup in compress(list(zip(tdata["DOCID"], tdata["SEGID"],
                                     tdata["START"], tdata["END"])), garbagemask):
            fh.write("\t".join(map(str, (fname,)+tup))+"\n")
        if not garbagedisabled:
          for tup in compress(list(zip(tdata["DOCID"], tdata["SEGID"],
                                       tdata["START"], tdata["END"])), goodmask):
              garbagefhs[fh].write("\t".join(map(str, (fname,)+tup))+"\n")
      except:
        sys.stderr.write(fname)
        raise

    ### Write tokenized, morph tokenized, pos tag
    if not tweet:
      zipset = zip(((outfiles["src"]["tok"], outfiles["src"]["morphtok"], outfiles["src"]["morph"], outfiles["src"]["pos"]),
                    (outfiles["trg"]["tok"], outfiles["trg"]["morphtok"], outfiles["trg"]["morph"], outfiles["trg"]["pos"])),
                   (sdata, tdata))
    else:
      # no source tok/morph info in tweets
      zipset = zip(((outfiles["trg"]["tok"], outfiles["trg"]["morphtok"], outfiles["trg"]["morph"], outfiles["trg"]["pos"]),),
                   (tdata,))

    for fhset, data in zipset:
      for fh, field in zip(fhset, ("TOK", "MORPHTOK", "MORPH", "POS")):
        for line in compress(data[field], garbagemask):
          fh.write(line)

  # run agile tokenizer on target orig
  # TODO: lowercase
  outfiles['trg']['orig'].close()
  agiletok_cmd = "%s -i %s -o %s -t %s " % (agiletokpath, outfiles['trg']['orig'].name, outfiles["trg"]["agiletoklc"], outfiles["trg"]["agiletok"])
  sys.stderr.write(agiletok_cmd+"\n")
  try:
    check_call(agiletok_cmd, shell=True)
  except CalledProcessError as e:
    sys.stderr.write("Error code %d running %s\n" % (e.returncode, e.cmd))
    sys.exit(1)
  # run cdec tokenizer on source orig
  outfiles['src']['orig'].close()
  cdectok_cmd = "%s -i %s -o %s -t %s " % (cdectokpath, outfiles['src']['orig'].name, outfiles["src"]["cdectoklc"], outfiles["src"]["cdectok"])
  sys.stderr.write(cdectok_cmd+"\n")
  try:
    check_call(cdectok_cmd, shell=True)
  except CalledProcessError as e:
    sys.stderr.write("Error code %d running %s\n" % (e.returncode, e.cmd))
    sys.exit(1)

'''
 Move extracted src tweets (.rsd) to translation directory
'''
def move_extracted_tweet(datadir, src, extwtdir):
  outdir = '%s/from_%s/%s/rsd' % (datadir, src, src)
  if os.path.exists(outdir):
    shutil.rmtree(outdir)
  os.makedirs(outdir)
  for i in os.listdir(extwtdir):
    '''
     .raw means character offsets are not well align, it may cause
     diferrent number of lines warning and entity annotations cannot be aligned
    '''
    if not i.endswith('.rsd.txt'):
      continue
    shutil.copy('%s/%s' % (extwtdir, i),
                '%s/%s' % (outdir, i))

def main():
  parser = argparse.ArgumentParser(description="extract parallel data from " \
                                   "expanded lrlp to flat files and manifests.")
  parser.add_argument("--rootdir", "-r", default=".",
                      help="root lrlp dir")
  parser.add_argument("--datadirs", nargs='+', default=['data', 'translation'],
                      help="elements in path from root to ltf files")
  parser.add_argument("--outdir", "-o", default="./parallel/extracted",
                      help="where to write extracted files")
  parser.add_argument("--src", "-s", default='uzb',
                      help="source language 3 letter code")
  parser.add_argument("--trg", "-t", default='eng',
                      help="target language 3 letter code")
  parser.add_argument("--origsubdir", default="raw.original",
                      help="subdirectory for untokenized files")
  parser.add_argument("--cleanorigsubdir", default="original",
                      help="subdirectory for cleaned raw original")
  parser.add_argument("--garbagesubdir", default="garbage",
                      help="subdirectory for garbage files (under orig)")
  parser.add_argument("--nogarbage", action='store_true', default=False,
                      help="turn off garbage filtering")
  parser.add_argument("--toksubdir", default="raw.tokenized",
                      help="subdirectory for ldc-tokenized but raw files")
  parser.add_argument("--cleantoksubdir", default="tokenized",
                      help="subdirectory for cleaned ldc-tokenized files")
  parser.add_argument("--cdectoksubdir", default="cdec-tokenized",
                      help="subdirectory for cdec-tokenized files")
  parser.add_argument("--agiletoksubdir", default="agile-tokenized",
                      help="subdirectory for agile-tokenized files (target side only)")
  parser.add_argument("--morphtoksubdir", default="morph-tokenized",
                      help="subdirectory for tokenized files based on " \
                      "morphological segmentation")
  parser.add_argument("--morphsubdir", default="morph",
                      help="subdirectory for morphological files")
  parser.add_argument("--possubdir", default="pos",
                      help="subdirectory for pos tag files")
  parser.add_argument("--extwtdir", "-et", default=None,
                      help="directory of extracted tweet rsd files")
  parser.add_argument("--agiletokpath", default=os.path.join(scriptdir, 'agiletok.sh'),
                      help="path to agile tokenizer binary")
  parser.add_argument("--cdectokpath", default=os.path.join(scriptdir, 'cdectok.sh'),
                      help="path to cdec tokenizer binary")

  try:
    args = parser.parse_args()
  except IOError as msg:
    parser.error(str(msg))

  origoutdir=args.origsubdir
  cleanorigoutdir=args.cleanorigsubdir
  tokoutdir=args.toksubdir
  cleantokoutdir=args.toksubdir
  morphtokoutdir=args.morphtoksubdir
  cdectokoutdir=args.cdectoksubdir
  agiletokoutdir=args.agiletoksubdir
  cdectoklcoutdir=args.cdectoksubdir+".lc"
  agiletoklcoutdir=args.agiletoksubdir+".lc"
  morphoutdir=args.morphsubdir
  posoutdir=args.possubdir
  agiletokpath = args.agiletokpath
  cdectokpath = args.cdectokpath
  dirs = [origoutdir,
          cleanorigoutdir,
          tokoutdir,
          cleantokoutdir,
          morphtokoutdir,
          cdectokoutdir,
          agiletokoutdir,
          cdectoklcoutdir,
          agiletoklcoutdir,
          morphoutdir,
          posoutdir]
  if args.nogarbage:
    garbageoutdir = None
  else:
    garbageoutdir=os.path.join(origoutdir, args.garbagesubdir)
    dirs.append(garbageoutdir)

  for dir in dirs:
    fulldir = os.path.join(args.outdir, dir)
    lputil.mkdir_p(fulldir)
  source_fh = open(os.path.join(args.outdir, "source"), 'a')
  source_fh.write("Extracted parallel data from %s to %s on %s\nusing %s;" \
                  " command issued from %s\n" % (args.rootdir, args.outdir,
                                                 datetime.datetime.now(),
                                                 ' '.join(sys.argv),
                                                 os.getcwd()))
  datadirs=[args.rootdir,]+args.datadirs

  '''
  from_eng/ -- manual translations from English into LRLP (elicitation,
  phrasebook, core REFLEX news text, additional news text)

  from_xxx/ -- manual translations from LRLP into English in multiple
  genres
  '''

  # name of corpus and location in lrlp (for cases that don't do anything special)
  corpustuples = [("fromsource.generic", os.path.join(*(datadirs+["from_%s" % args.src,]))),
                  ("fromtarget.news", os.path.join(*(datadirs+["from_%s" % args.trg, "news"]))),
                  ("fromtarget.phrasebook", os.path.join(*(datadirs+["from_%s" % args.trg, "phrasebook"]))),
                  ("fromtarget.elicitation", os.path.join(*(datadirs+["from_%s" % args.trg, "elicitation"])))
  ]
  commonargs=[args.src, args.trg, args.outdir, origoutdir, cleanorigoutdir, garbageoutdir,
             tokoutdir, cleantokoutdir, morphtokoutdir, cdectokoutdir, cdectoklcoutdir,
             agiletokoutdir, agiletoklcoutdir, morphoutdir, posoutdir,
             agiletokpath, cdectokpath]
  for corpustuple in corpustuples:
    printout(corpustuple[0], corpustuple[1], *commonargs)


  # Found data
  printout("found.generic", args.rootdir, *commonargs, 
           stp=lputil.all_found_tuples, el=lputil.get_aligned_sentences, swap=True)

  # Tweet data
  if args.extwtdir is not None and os.path.exists(args.extwtdir):
    move_extracted_tweet(os.path.join(*datadirs), args.src, args.extwtdir)
    printout("fromsource.tweet",
             os.path.join(*(datadirs+["from_%s" % args.src,])), *commonargs,
             tweet=True)

if __name__ == '__main__':
  main()
