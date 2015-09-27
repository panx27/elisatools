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
  src_orig_fh=open(os.path.join(origoutdir, "%s.%s.flat" % (prefix,src)), 'w')
  trg_orig_fh=open(os.path.join(origoutdir, "%s.%s.flat" % (prefix,trg)), 'w')
  src_tok_fh=open(os.path.join(tokoutdir, "%s.tok.%s.flat" % (prefix,src)), 'w')
  trg_tok_fh=open(os.path.join(tokoutdir, "%s.tok.%s.flat" % (prefix,trg)), 'w')
  src_morphtok_fh=open(os.path.join(morphtokoutdir, "%s.morphtok.%s.flat" % \
                                    (prefix,src)),'w')
  trg_morphtok_fh=open(os.path.join(morphtokoutdir, "%s.morphtok.%s.flat" % \
                                    (prefix,trg)),'w')
  src_morph_fh=open(os.path.join(morphoutdir, "%s.morph.%s.flat" % \
                                 (prefix,src)),'w')
  trg_morph_fh=open(os.path.join(morphoutdir, "%s.morph.%s.flat" % \
                                 (prefix,trg)),'w')
  src_pos_fh=open(os.path.join(posoutdir, "%s.pos.%s.flat" % (prefix,src)),'w')
  trg_pos_fh=open(os.path.join(posoutdir, "%s.pos.%s.flat" % (prefix,trg)),'w')

  xml = True
  if prefix == 'fromsource.tweet':
    xml = False # Tweets do not have .ltf format files
  for m in stp(path, src=src, trg=trg, xml=xml):
    sl, tl = el(*m, xml=xml, tokenize=False, segment=False)
    if sl is None or tl is None:
      sys.stderr.write("Warning: empty files:\n%s or %s\n" % (m[0], m[1]))
      continue
    # Strict rejection of different length lines. If these are desired,
    # do gale & church or brown et al or something similar here
    slen = len(sl)
    tlen = len(tl)
    if slen != tlen:
      sys.stderr.write("Warning: different number of lines in files:\n" \
                       "%s %d\n%s %d\n" % (m[0], slen, m[1], tlen))
      continue

    ### Write original
    src_orig_fh.write(''.join(sl))
    trg_orig_fh.write(''.join(tl))

    ### Write manifest
    if xml:
      sxobj = ET.parse(m[0])
      sdocid = sxobj.findall(".//DOC")[0].get('id')
      src_seginfo = [ [ x.get(y) for y in ('id', 'start_char', 'end_char') ]
                      for x in sxobj.findall(".//SEG") ]
      for tup in src_seginfo:
        src_man_fh.write("\t".join([m[0],sdocid]+tup)+"\n")
      txobj = ET.parse(m[1])
      tdocid = txobj.findall(".//DOC")[0].get('id')
      trg_seginfo = [ [ x.get(y) for y in ('id', 'start_char', 'end_char') ]
                      for x in txobj.findall(".//SEG") ]
      for tup in trg_seginfo:
        trg_man_fh.write("\t".join([m[1],tdocid]+tup)+"\n")
    else:
      for i in xrange(len(sl)):
        src_man_fh.write(m[0]+"\n")
      for i in xrange(len(tl)):
        trg_man_fh.write(m[1]+"\n")

    ### Write tokenized, morph tokenized, pos tag
    if not xml:
      continue
    src_segments, trg_segments = el(*m, xml=True, tokenize=False, segment=True)
    # Tokenized
    try:
      stlen = len(src_segments[0])
      ttlen = len(trg_segments[0])
      assert stlen == slen
      assert ttlen == tlen
      src_tok_fh.write(''.join(src_segments[0]))
      trg_tok_fh.write(''.join(trg_segments[0]))
    except:
      sys.stderr.write("Warning: different number of lines in token files:\n" \
                       "%s %d\n%s %d\n" % (stlen, slen, ttlen, tlen))
    # tsl, ttl = el(*m, xml=True, tokenize=True)
    # src_tok_fh.write(''.join(tsl).encode('utf-8'))
    # trg_tok_fh.write(''.join(ttl).encode('utf-8'))

    # Morph tokenized
    try:
      smtlen = len(src_segments[1])
      tmtlen = len(trg_segments[1])
      assert smtlen == slen
      assert tmtlen == tlen
      src_morphtok_fh.write(''.join(src_segments[1]))
      trg_morphtok_fh.write(''.join(trg_segments[1]))
    except:
      sys.stderr.write("Warning: different number of lines in morph-tokenzied" \
                       " files:\n %s %d\n%s %d\n" % (smtlen, slen,
                                                     tmtlen, tlen))

    # Morph
    try:
      smlen = len(src_segments[2])
      tmlen = len(trg_segments[2])
      assert smlen == slen
      assert tmlen == tlen
      src_morph_fh.write(''.join(src_segments[2]))
      trg_morph_fh.write(''.join(trg_segments[2]))
    except:
      sys.stderr.write("Warning: different number of lines in morph files:\n" \
                       "%s %d\n%s %d\n" % (smlen, slen, tmlen, tlen))

    # Pos tag
    try:
      splen = len(src_segments[3])
      tplen = len(trg_segments[3])
      assert splen == slen
      assert tplen == tlen
      src_pos_fh.write(''.join(src_segments[3]))
      trg_pos_fh.write(''.join(trg_segments[3]))
    except:
      sys.stderr.write("Warning: different number of lines in pos files:\n" \
                       "%s %d\n%s %d\n" % (splen, slen, tplen, tlen))

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

  for i in os.listdir('%s/from_%s/%s/rsd' % (datadir, src, trg)):
    if i.startswith('SN_TWT_'):
      shutil.copy('%s/from_%s/%s/rsd/%s' % (datadir, src, trg, i),
                  '%s/%s/rsd/%s' % (dir_, trg, i))
  for i in os.listdir(extwtdir):
    '''
     .raw means character offsets are not well align, it may cause
     diferrent number of lines warning
    '''
    raw2rsd = re.sub('.raw', '.rsd.txt', i)
    shutil.copy('%s/%s' % (extwtdir, i),
                  '%s/%s/rsd/%s' % (dir_, src, raw2rsd))

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

  origoutdir=os.path.join(args.outdir, args.origsubdir)
  tokoutdir=os.path.join(args.outdir, args.toksubdir)
  morphtokoutdir=os.path.join(args.outdir, args.morphtoksubdir)
  morphoutdir=os.path.join(args.outdir, args.morphsubdir)
  posoutdir=os.path.join(args.outdir, args.possubdir)
  dirs = [args.outdir,
          tokoutdir,
          origoutdir,
          morphtokoutdir,
          morphoutdir,
          posoutdir]
  for dir in dirs:
    if not os.path.exists(dir):
      os.makedirs(dir)

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
           tokoutdir, morphoutdir, morphoutdir, posoutdir,
           stp=lputil.all_found_tuples, el=lputil.get_aligned_sentences)
  # Tweet data
  process_tweet(os.path.join(*datadirs), args.src, args.trg, args.extwtdir)
  printout("fromsource.tweet",
           os.path.join(*(datadirs+["from_%s_tweet" % args.src,])),
           args.src, args.trg, args.outdir, origoutdir,
           tokoutdir, morphtokoutdir, morphoutdir, posoutdir)

if __name__ == '__main__':
  main()
