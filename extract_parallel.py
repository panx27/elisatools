#! /usr/bin/env python
#-*- coding: utf-8 -*-
import sys
reload(sys)
sys.setdefaultencoding('utf8')
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

def printout(prefix, path, src, trg, outdir, origoutdir,
             tokoutdir, morphtokoutdir, morphoutdir, posoutdir,
             stp=lputil.selected_translation_pairs, el=lputil.extract_lines):
  ''' Find files and print them out '''
  src_man_fh=open(os.path.join(outdir, "%s.%s.manifest" % (prefix, src)), 'w')
  trg_man_fh=open(os.path.join(outdir, "%s.%s.manifest" % (prefix, trg)), 'w')
  src_orig_fh=open(os.path.join(outdir, origoutdir, "%s.%s.%s.flat" % \
                                (prefix,origoutdir,src)), 'w')
  trg_orig_fh=open(os.path.join(outdir, origoutdir, "%s.%s.%s.flat" % \
                                (prefix,origoutdir,trg)), 'w')
  src_tok_fh=open(os.path.join(outdir, tokoutdir, "%s.%s.%s.flat" % \
                               (prefix,tokoutdir,src)), 'w')
  trg_tok_fh=open(os.path.join(outdir, tokoutdir, "%s.%s.%s.flat" % \
                               (prefix,tokoutdir,trg)), 'w')
  src_morphtok_fh=open(os.path.join(outdir, morphtokoutdir, "%s.%s.%s.flat" % \
                                    (prefix,morphtokoutdir,src)),'w')
  trg_morphtok_fh=open(os.path.join(outdir, morphtokoutdir, "%s.%s.%s.flat" % \
                                    (prefix,morphtokoutdir,trg)),'w')
  src_morph_fh=open(os.path.join(outdir, morphoutdir, "%s.%s.%s.flat" % \
                                 (prefix,morphoutdir,src)),'w')
  trg_morph_fh=open(os.path.join(outdir, morphoutdir, "%s.%s.%s.flat" % \
                                 (prefix,morphoutdir,trg)),'w')
  src_pos_fh=open(os.path.join(outdir, posoutdir, "%s.%s.%s.flat" % \
                               (prefix,posoutdir,src)),'w')
  trg_pos_fh=open(os.path.join(outdir, posoutdir, "%s.%s.%s.flat" % \
                               (prefix,posoutdir,trg)),'w')

  xml = True
  if prefix == 'fromsource.tweet':
    xml = False # Tweets data only have .rsd rather than .ltf

  for m in stp(path, src=src, trg=trg, xml=xml):
    sdata, tdata = el(*m, xml=xml)
    if sdata is None or tdata is None:
      sys.stderr.write("Warning: empty files:\n%s or %s\n" % (m[0], m[1]))
      continue
    # Strict rejection of different length lines. If these are desired,
    # do gale & church or brown et al or something similar here
    slen = len(sdata["ORIG"])
    tlen = len(tdata["ORIG"])
    if slen != tlen:
      sys.stderr.write("Warning: different number of lines in files:\n" \
                       "%s %d\n%s %d\n" % (m[0], slen, m[1], tlen))
      continue

    ### Write original
    src_orig_fh.write(''.join(sdata["ORIG"]))
    trg_orig_fh.write(''.join(tdata["ORIG"]))

    ### Write manifest
    if xml:
      for fh, fname, tupgen in zip((src_man_fh, trg_man_fh), (m[0], m[1]),
                                   (zip(sdata["DOCID"], sdata["SEGID"],
                                        sdata["START"], sdata["END"]),
                                    zip(tdata["DOCID"], tdata["SEGID"],
                                        tdata["START"], tdata["END"]))):
        for tup in tupgen:
          fh.write("\t".join((fname,)+tup)+"\n")
    else:
      for fh, field in zip((src_man_fh, trg_man_fh),
                           (sdata["DOCID"],tdata["DOCID"])):
        fh.write('%s\t%s\n' % (field[0].strip(),
                             re.search('.+/(\S*?)\.', field[0].strip()).group(1)))

    if not xml: # .rsd does not have tokenized, morph tokenized, pos tag info
      continue

    ### Write tokenized, morph tokenized, pos tag
    for fhset, data in zip(((src_tok_fh, src_morphtok_fh, src_morph_fh, src_pos_fh),
                            (trg_tok_fh, trg_morphtok_fh, trg_morph_fh, trg_pos_fh)),
                           (sdata, tdata)):
      for fh, field in zip(fhset, ("TOK", "MORPHTOK", "MORPH", "POS")):
        fh.write(''.join(data[field]))

'''
 Merge trg tweets and extracted src tweets (.rsd)
'''
def process_tweet(datadir, src, trg, extwtdir):
  dir_ = '%s/from_%s_tweet' % (datadir, src)
  if os.path.exists(dir_):
    shutil.rmtree(dir_)
  os.makedirs(dir_)
  os.makedirs('%s/%s/rsd' % (dir_, src))
  os.makedirs('%s/%s/rsd' % (dir_, trg))

  # Copy translated .rsd files
  for i in os.listdir('%s/from_%s/%s/rsd' % (datadir, src, trg)):
    if i.startswith('SN_TWT_'):
      shutil.copy('%s/from_%s/%s/rsd/%s' % (datadir, src, trg, i),
                  '%s/%s/rsd/%s' % (dir_, trg, i))
  # Copy tweet files
  for i in os.listdir(extwtdir):
    '''
     .raw means character offsets are not well align, it may cause
     diferrent number of lines warning and entity annotations cannot be aligned
    '''
    if not i.endswith('.rsd.txt'):
      continue
    shutil.copy('%s/%s' % (extwtdir, i),
                  '%s/%s/rsd/%s' % (dir_, src, i))

def main():
  parser = argparse.ArgumentParser(description="extract parallel data from " \
                                   "expanded lrlp to flat files and manifests.")
  parser.add_argument("--rootdir", "-r", default=".",
                      help="root lrlp dir")
  parser.add_argument("--outdir", "-o", default="./parallel/extracted",
                      help="where to write extracted files")
  parser.add_argument("--src", "-s", default='uzb',
                      help="source language 3 letter code")
  parser.add_argument("--trg", "-t", default='eng',
                      help="target language 3 letter code")
  parser.add_argument("--origsubdir", default="original",
                      help="subdirectory for untokenized files")
  parser.add_argument("--toksubdir", default="tokenized",
                      help="subdirectory for tokenized files")
  parser.add_argument("--morphtoksubdir", default="morph-tokenized",
                      help="subdirectory for tokenized files based on " \
                      "morphological segmentation")
  parser.add_argument("--morphsubdir", default="morph",
                      help="subdirectory for morphological files")
  parser.add_argument("--possubdir", default="pos",
                      help="subdirectory for pos tag files")
  parser.add_argument("--extwtdir", "-et",
                      help="directory of extracted tweet rsd files")
  try:
    args = parser.parse_args()
  except IOError, msg:
    parser.error(str(msg))

  origoutdir=args.origsubdir
  tokoutdir=args.toksubdir
  morphtokoutdir=args.morphtoksubdir
  morphoutdir=args.morphsubdir
  posoutdir=args.possubdir
  dirs = [origoutdir,
          tokoutdir,
          morphtokoutdir,
          morphoutdir,
          posoutdir]
  for dir in dirs:
    fulldir = os.path.join(args.outdir, dir)
    lputil.mkdir_p(fulldir)

  source_fh = open(os.path.join(args.outdir, "source"), 'a')
  source_fh.write("Extracted parallel data from %s to %s on %s\nusing %s;" \
                  " command issued from %s\n" % (args.rootdir, args.outdir,
                                                 datetime.datetime.now(),
                                                 ' '.join(sys.argv),
                                                 os.getcwd()))
  datadirs=[args.rootdir, 'data', 'translation']

  '''
  from_eng/ -- manual translations from English into LRLP (elicitation,
  phrasebook, core REFLEX news text, additional news text)

  from_xxx/ -- manual translations from LRLP into English in multiple
  genres
  '''
  # From source
  printout("fromsource.generic",
           os.path.join(*(datadirs+["from_%s" % args.src,])),
           args.src, args.trg, args.outdir, origoutdir,
           tokoutdir, morphtokoutdir, morphoutdir, posoutdir)
  # News from target
  printout("fromtarget.news",
           os.path.join(*(datadirs+["from_%s" % args.trg, "news"])),
           args.src, args.trg, args.outdir, origoutdir,
           tokoutdir, morphtokoutdir, morphoutdir, posoutdir)
  # Phrase book from target
  printout("fromtarget.phrasebook",
           os.path.join(*(datadirs+["from_%s" % args.trg, "phrasebook"])),
           args.src, args.trg, args.outdir, origoutdir,
           tokoutdir, morphtokoutdir, morphoutdir, posoutdir)
  # Elicitation from target
  printout("fromtarget.elicitation",
           os.path.join(*(datadirs+["from_%s" % args.trg, "elicitation"])),
           args.src, args.trg, args.outdir, origoutdir,
           tokoutdir, morphtokoutdir, morphoutdir, posoutdir)
  # Found data
  printout("found.generic",
           args.rootdir, args.src, args.trg, args.outdir, origoutdir,
           tokoutdir, morphtokoutdir, morphoutdir, posoutdir,
           stp=lputil.all_found_tuples, el=lputil.get_aligned_sentences)
  # Tweet data
  process_tweet(os.path.join(*datadirs), args.src, args.trg, args.extwtdir)
  printout("fromsource.tweet",
           os.path.join(*(datadirs+["from_%s_tweet" % args.src,])),
           args.src, args.trg, args.outdir, origoutdir,
           tokoutdir, morphtokoutdir, morphoutdir, posoutdir)

if __name__ == '__main__':
  main()
