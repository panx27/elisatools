#!/usr/bin/env python3

import argparse
import sys
import codecs
from collections import defaultdict as dd
import lxml.etree as ET
import gzip
import re
import os.path
import hashlib

from itertools import zip_longest
scriptdir = os.path.dirname(os.path.abspath(__file__))

# TODO: option to build gzip file

def strip(x):
  try:
    return x.strip()
  except:
    return None

def main():
  parser = argparse.ArgumentParser(description="Create xml from extracted" \
                                   " and transformed monolingual data",
                                   formatter_class= \
                                   argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--rootdirs", "-r", nargs='+', default=[".",], help="root lrlp dirs")
  parser.add_argument("--lang", "-l", help="lrlp language code")
  parser.add_argument("--corpora", "-c", nargs='+', help="prefixes that have " \
                      "at minimum a manifest and original/ file")
  parser.add_argument("--outfile", "-o", type=argparse.FileType('w'),
                      default=sys.stdout, help="output file")
  parser.add_argument("--psmfile", "-p", type=argparse.FileType('r'),
                      help="psm annotation file")
  parser.add_argument("--annfile", "-a", type=argparse.FileType('r'),
                      help="entity annotation file")
  parser.add_argument("--nonone", "-n", action='store_true',
                      default=False, help="filter out lines with NONE NONE")
  parser.add_argument("--statsfile", "-s", type=argparse.FileType('w'),
                      default=sys.stderr, help="file to write statistics")
  parser.add_argument("--evaluation", "-e", action='store_true',
                      default=False, help="prodece source side only")

  try:
    args = parser.parse_args()
  except IOError as msg:
    parser.error(str(msg))

  outfile = args.outfile
  statsfile = args.statsfile
  # outfile = writer(args.outfile)

  # For every document, for every position, a list of (pointers to) annotations
  # then for every segment, retrieve the sublist and create the set of
  # annotations relevant to the annotation

  # Needs to be two-pass so we create the proper list size
  # TODO: no it doesn't
  psmtemp = dd(list)

  # Data is kind (headline/post) id start length then if 'post',
  # author timestamp

  # Spans of length 0 are discarded (these seem to be multiply
  # occurring authors/datetimes/ids
  # TODO: what's with these bad entries?? There's a lot of them.
  # sometimes they make my window hang but sometimes they look totally normal

  if args.psmfile is not None:
    psmdiscardcount = 0
    for ln, line in enumerate(args.psmfile):
      try:
        toks = line.strip().split('\t')
        if len(toks) < 4:
          sys.stderr.write("Skipping line %d of psmfile; bad data (%d toks)\n" \
                           % (ln, len(toks)))
          continue
        if int(toks[3]) == 0:
          psmdiscardcount += 1
          continue
        doc = toks[1]
        psmtemp[doc].append(toks)
      except:
        print(ln)
        raise
    sys.stderr.write("Discarded %d psm entries\n" % psmdiscardcount)

  # Will fill on demand
  psms = dd(lambda: dd(list))
  # Entities: document/start/kind/data
  # Data is kind (NE/FE/SSA) id start end menid span, then
  # if NE, type
  # if FE, class (mention/head), subtype (NAM/NOM/TTL/?/None), entid, type
  # if SSA, pred/arg agent/patient/act/location/state,
  # pred reference (check readme)
  # anns = dd(lambda: dd(lambda: dd(list)))
  anntemp = dd(list)
  if args.annfile is not None:
    anndiscardcount = 0
    for ln, line in enumerate(args.annfile):
      try:
        toks = line.strip().split('\t')
        if len(toks) < 6:
          sys.stderr.write("Skipping line %d of annfile; bad data (%d toks)\n" \
                           % (ln, len(toks)))
          continue;
        if int(toks[3])-int(toks[2]) == 0:
          anndiscardcount+=1
          continue
        anntemp[toks[1]].append(toks)
      except ValueError:
        anndiscardcount+=1
        continue
      except:
        print(ln)
        raise
    sys.stderr.write("Discarded %d ann entries\n" % anndiscardcount)
  # Will fill on demand
  anns = dd(lambda: dd(list))

  # for printing out at the end
  stats = dd(lambda: dd(int))

  # Each segment is a legit xml block. the corpus/language/document are faked
  # TODO: corpus/document
  # TODO: make this more generalizable!
  outfile.write('<?xml version="1.0" encoding="UTF-8"?>\n')
  outfile.write('<!DOCTYPE ELISA_LRLP_CORPUS SYSTEM ' \
                '"elisa.lrlp.v1.1.dtd">\n')
  outfile.write('<ELISA_LRLP_CORPUS source_language="%s">\n' % args.lang)
  for rootdir in args.rootdirs:
    for corpus in args.corpora:
      corpus = corpus.replace('.manifest', '')
      rooted_corpus="%s_%s" % (rootdir, corpus)
      src_manifest = open(os.path.join(rootdir, "%s.%s.manifest" % \
                                       (corpus, args.lang)))
      trg_manifest = open(os.path.join(rootdir, "%s.eng.manifest" % \
                                       (corpus)))
      src_origfile = open(os.path.join(rootdir, "original",
                                       "%s.original.%s.flat" % \
                                       (corpus, args.lang)))
      trg_origfile = open(os.path.join(rootdir, "original",
                                       "%s.original.eng.flat" % (corpus)))
      src_tokfile =  open(os.path.join(rootdir, "tokenized",
                                      "%s.tokenized.%s.flat" % \
                                      (corpus, args.lang)))
      trg_tokfile =  open(os.path.join(rootdir, "tokenized",
                                             "%s.tokenized.eng.flat" % (corpus)))

      src_morphtokfile = open(os.path.join(rootdir, "morph-tokenized",
                                           "%s.morph-tokenized.%s.flat" % \
                                           (corpus,args.lang)))
      trg_morphtokfile = open(os.path.join(rootdir, "morph-tokenized",
                                          "%s.morph-tokenized.eng.flat" % \
                                           (corpus)))
      src_morphfile =    open(os.path.join(rootdir, "morph",
                                        "%s.morph.%s.flat" % \
                                        (corpus, args.lang)))
      trg_morphfile =    open(os.path.join(rootdir, "morph",
                                        "%s.morph.eng.flat" % (corpus)))
      src_posfile =      open(os.path.join(rootdir, "pos",
                                      "%s.pos.%s.flat" % \
                                      (corpus, args.lang)))
      trg_posfile =      open(os.path.join(rootdir, "pos",
                                             "%s.pos.eng.flat" % (corpus)))
      trg_agiletokfile = open(os.path.join(rootdir, "agile-tokenized",
                                             "%s.agile-tokenized.eng.flat" % (corpus)))
      src_cdectokfile = open(os.path.join(rootdir, "cdec-tokenized",
                                             "%s.cdec-tokenized.%s.flat" % (corpus, args.lang)))
      trg_agiletoklcfile = open(os.path.join(rootdir, "agile-tokenized.lc",
                                             "%s.agile-tokenized.lc.eng.flat" % (corpus)))
      src_cdectoklcfile = open(os.path.join(rootdir, "cdec-tokenized.lc",
                                             "%s.cdec-tokenized.lc.%s.flat" % (corpus, args.lang)))

      src_lastfullid = None

      # iteration = zip(src_manifest, trg_manifest, src_origfile, trg_origfile,
      #                 src_tokfile, trg_tokfile, src_morphtokfile, trg_morphtokfile,
      #                 src_morphfile, trg_morphfile, src_posfile, trg_posfile,
      #                 src_cdectokfile, trg_agiletokfile,
      #                 src_cdectoklcfile, trg_agiletoklcfile)

      # zip ---> zip_longest
      # in case of tweet src doest have ltf
      iteration = zip_longest(src_manifest, trg_manifest, src_origfile, trg_origfile,
                              src_tokfile, trg_tokfile, src_morphtokfile, trg_morphtokfile,
                              src_morphfile, trg_morphfile, src_posfile, trg_posfile,
                              src_cdectokfile, trg_agiletokfile,
                              src_cdectoklcfile, trg_agiletoklcfile)
      for src_manline, trg_manline, \
          src_origline, trg_origline, \
          src_tokline, trg_tokline, \
          src_morphtokline, trg_morphtokline, \
          src_morphline, trg_morphline, \
          src_posline, trg_posline, \
          src_cdectokline, trg_agiletokline, \
          src_cdectoklcline, trg_agiletoklcline \
          in iteration:

        src_origline = strip(src_origline)
        src_tokline = strip(src_tokline)
        src_morphtokline = strip(src_morphtokline)
        src_morphline = strip(src_morphline)
        src_posline = strip(src_posline)
        src_man = strip(src_manline).split('\t')
        src_fullid = src_man[1]
        src_fullidsplit = src_fullid.split('_')
        if corpus == 'fromtarget.elicitation':
          src_fullidsplit = ['ELICITATION', 'NONE', args.lang.upper(),
                             'NONE', 'NONE']
        if corpus == 'fromtarget.phrasebook':
          src_fullidsplit = ['PHRASEBOOK', 'NONE', args.lang.upper(),
                             'NONE', 'NONE']
        trg_origline = strip(trg_origline)
        trg_tokline = strip(trg_tokline)
        trg_morphtokline = strip(trg_morphtokline)
        trg_morphline = strip(trg_morphline)
        trg_posline = strip(trg_posline)
        src_cdectokline = strip(src_cdectokline)
        src_cdectoklcline = strip(src_cdectoklcline)
        trg_agiletokline = strip(trg_agiletokline)
        trg_agiletoklcline = strip(trg_agiletoklcline)
        trg_man = strip(trg_manline).split('\t')
        trg_fullid = trg_man[1]

        if args.nonone and ("NONE NONE" in src_origline or "NONE NONE" in trg_origline):
          continue
        # old style: genre(2)_prov(3)_lang(3)_id(var)_date(8)
        # new style: lang(3)_genre(2)_prov(6)_date(8)_id(9)

        fullidfields = ['GENRE', 'PROVENANCE', 'SOURCE_LANGUAGE',
                        'INDEX_ID', 'DATE']
        if src_fullid[3] == "_" and src_fullid[6] == "_" and src_fullid[13] == "_":
          fullidfields = ['SOURCE_LANGUAGE', 'GENRE', 'PROVENANCE', 'DATE', 'INDEX_ID']
        elif src_fullid[2] != "_" or src_fullid[6] != "_" or src_fullid[10] != "_":
          sys.stderr.write("unexpected filename format: "+src_fullid+"\n")

        # Faking the document-level
        if src_lastfullid != src_fullid:
          stats[rooted_corpus]["DOCS"]+=1
          if src_lastfullid is not None:
            outfile.write("</DOCUMENT>\n")
          src_lastfullid = src_fullid
          outfile.write('<DOCUMENT id="%s">\n' % src_fullid)
          for label, value in zip(fullidfields, src_fullidsplit):
            outfile.write("  <%s>%s</%s>\n" % (label, value, label))
          outfile.write("  <DIRECTION>%s</DIRECTION>\n" % \
                        re.match('(\w+)\..+', corpus).group(1))
        stats[rooted_corpus]["SEGMENTS"]+=1
        stats[rooted_corpus]["SRCWORDS"] += len(src_origline.split())
        stats[rooted_corpus]["TRGWORDS"] += len(trg_origline.split())
        xroot = ET.Element('SEGMENT')
        src_seg = ET.SubElement(xroot, 'SOURCE')
        # Non-tweet (ltf)
        if corpus != 'fromsource.tweet':
          src_seg.set('id', "%s.%s.%s.%s" % (src_man[1], src_man[2], src_man[3], src_man[4]))
          src_seg.set('start_char', src_man[3])
          src_seg.set('end_char', src_man[4])

          subelements = []
          subelements.append(("FULL_ID_SOURCE", src_man[1]))
          subelements.append(("ORIG_SEG_ID", src_man[2])) # for nistification
          subelements.append(("ORIG_FILENAME", os.path.basename(src_man[0]))) # for nistification
          subelements.append(("ORIG_RAW_SOURCE", src_origline))
          src_md5 = hashlib.md5(src_origline.encode('utf-8')).hexdigest()
          subelements.append(("MD5_HASH_SOURCE", src_md5))
          subelements.append(("LRLP_TOKENIZED_SOURCE", src_tokline))
          subelements.append(("LRLP_POSTAG_SOURCE", src_posline))
          subelements.append(("CDEC_TOKENIZED_SOURCE", src_cdectokline))
          subelements.append(("CDEC_TOKENIZED_LC_SOURCE", src_cdectoklcline))
          # don't add morph info if there's nothing interesting
          morphset = set(src_morphline.split())
          if len(morphset) == 1 and list(morphset)[0] == "none":
            pass
          else:
            subelements.append(("LRLP_MORPH_TOKENIZED_SOURCE", src_morphtokline))
            subelements.append(("LRLP_MORPH_SOURCE", src_morphline))
        # Tweet (rsd)
        else:
          src_seg.set('id', src_man[1])
          src_seg.set('start_char', '0')
          src_seg.set('end_char', str(len(src_origline.encode('utf-8'))-1))


          subelements = []
          subelements.append(("FULL_ID_SOURCE", src_man[1]))
          subelements.append(("ORIG_SEG_ID", "segment-0")) # for nistification
          subelements.append(("ORIG_FILENAME", os.path.basename(src_man[0]))) # for nistification
          subelements.append(("ORIG_RAW_SOURCE", src_origline))
          src_md5 = hashlib.md5(src_origline.encode('utf-8')).hexdigest()
          subelements.append(("MD5_HASH_SOURCE", src_md5))
          subelements.append(("CDEC_TOKENIZED_SOURCE", src_cdectokline))
          subelements.append(("CDEC_TOKENIZED_LC_SOURCE", src_cdectoklcline))

        # On-demand fill of psms and anns hashes that assumesit will be
        # used contiguously
        if src_fullid in psmtemp:
          psms.clear()
          data = psmtemp.pop(src_fullid)
          for tup in data:
            start = int(tup[2])
            end = start+int(tup[3])
            for i in range(start, end):
              psms[src_fullid][i].append(tup)

        if src_fullid in psms:
          # Collect the annotations
          psmcoll = set()
          try:
            startchar = int(src_man[3])
          except IndexError:
            startchar = 0
          try:
            endchar = int(src_man[4])
          except IndexError:
            endchar = len(anns[src_fullid])

          if endchar > len(psms[src_fullid]):
            endchar = len(psms[src_fullid])
          for i in range(startchar, endchar):
            slot = psms[src_fullid][i]
            psmcoll.update(list(map(tuple, slot)))
          for psmitem in psmcoll:
            if psmitem[0]=='headline':
              subelements.append(("IS_HEADLINE","1"))
              continue
            if psmitem[0]=='post':
              if len(psmitem) >= 5:
                subelements.append(("AUTHOR", psmitem[4]))
                if len(psmitem) >= 6:
                  subelements.append(("POST_DATE_TIME", psmitem[5]))
            else:
              sys.stderr.write("Not sure what to do with item that starts " + \
                               psmitem[0]+"\n")
              continue

        if src_fullid in anntemp:
          anns.clear()
          data = anntemp.pop(src_fullid)
          for tup in data:
            start = int(tup[2])
            end = int(tup[3])
            for i in range(start, end):
              anns[src_fullid][i].append(tup)

        if src_fullid in anns:
          # Collect the annotations
          anncoll = set()
          try:
            startchar = int(src_man[3])
          except IndexError:
            startchar = 0
          try:
            endchar = int(src_man[4])
          except IndexError:
            endchar = len(anns[src_fullid])
          for i in range(startchar, endchar):
            slot = anns[src_fullid][i]
            anncoll.update(list(map(tuple, slot)))
          if len(anncoll) > 0:
            ae = ET.SubElement(src_seg, "ANNOTATIONS")
          for annitem in anncoll: # TODO: sort by start_char?
            se = ET.SubElement(ae, "ANNOTATION", \
                               {'task':annitem[0],'annotation_id': annitem[4]})
            # se = ET.SubElement(ae, "ANNOTATION", \
            #                    {'task':annitem[0],'annotation_id': annitem[4],
            #                     'start_char':annitem[2], 'end_char':annitem[3]})
            # se.text=annitem[5]
            head = ET.SubElement(se, "HEAD")
            head.set('start_char', annitem[2])
            head.set('end_char', annitem[3])
            head.text = annitem[5]
            subsubs = []
            if annitem[0]=='NE':
              subsubs.append(("ENTITY_TYPE", annitem[6]))
            elif annitem[0]=='FE':
              if annitem[6] == 'HEAD':
                subsubs.append(("ANNOTATION_KIND", annitem[6]))
                subsubs.append(("MENTION_TYPE", annitem[7]))
                subsubs.append(("PHRASE_ID", annitem[8])) # Should be PHRASE ID
              else: # MENTION/ENTITY
                subsubs.append(("ENTITY_TYPE", annitem[9]))
                subsubs.append(("ANNOTATION_KIND", annitem[6]))
                subsubs.append(("MENTION_TYPE", annitem[7]))
                subsubs.append(("ENTITY_ID", annitem[8]))
            elif annitem[0]=='SSA':
              se.set('pred_or_arg', annitem[6])
              subsubs.append(("ROLE", annitem[7]))
              if annitem[6] == "argument":
                subsubs.append(("PREDICATE", annitem[8]))
            elif annitem[0]=='NPC':
              subsubs.append(("NPC_TYPE", annitem[6]))
            else:
              sys.stderr.write("Not sure what to do with item that starts " \
                               +annitem[0]+"\n")
              continue
            for key, text in subsubs:
              sse = ET.SubElement(se, key)
              sse.text = text

        # TODO: more tokenizations, etc.
        for key, text in subelements:
          se = ET.SubElement(src_seg, key)
          se.text = text
        # Entity/semantic annotations in their own block if fullid in anns

        # Target segements
        if not args.evaluation:
          trg_seg = ET.SubElement(xroot, 'TARGET')
          trg_seg.set('id', "%s.%s.%s.%s" % (trg_man[1], trg_man[2], trg_man[3], trg_man[4]))
          trg_seg.set('start_char', trg_man[3])
          trg_seg.set('end_char', trg_man[4])
          ET.SubElement(trg_seg, "FULL_ID_TARGET").text = trg_fullid
          ET.SubElement(trg_seg, "ORIG_RAW_TARGET").text = trg_origline
          trg_md5 = hashlib.md5(trg_origline.encode('utf-8')).hexdigest()
          ET.SubElement(trg_seg, "MD5_HASH_TARGET").text = trg_md5
          ET.SubElement(trg_seg, "LRLP_TOKENIZED_TARGET").text = trg_tokline
          ET.SubElement(trg_seg, "LRLP_POSTAG_TARGET").text = trg_posline
          ET.SubElement(trg_seg, "AGILE_TOKENIZED_TARGET").text = trg_agiletokline
          ET.SubElement(trg_seg, "AGILE_TOKENIZED_LC_TARGET").text = trg_agiletoklcline
          # don't add morph info if there's nothing interesting
          morphset = set(trg_morphline.split())
          if len(morphset) == 1 and list(morphset)[0] == "none":
            pass
          else:
            ET.SubElement(trg_seg,
                          "LRLP_MORPH_TOKENIZED_TARGET").text = trg_morphtokline
            ET.SubElement(trg_seg, "LRLP_MORPH_TARGET").text = trg_morphline


        xmlstr = ET.tostring(xroot, pretty_print=True, encoding='utf-8',
                             xml_declaration=False).decode('utf-8')
        outfile.write(xmlstr)
      if src_lastfullid is not None:
        outfile.write("</DOCUMENT>\n")
  outfile.write("</ELISA_LRLP_CORPUS>\n")

  statsfile.write("CORPUS STATISTICS\n")
  total = dd(int)
  for corpus, cstat in sorted(stats.items()):
    statsfile.write("%s :" % corpus)
    for stat, val in sorted(cstat.items()):
      total[stat]+=val
      statsfile.write(" %d %s" % (val, stat))
    statsfile.write("\n")
  statsfile.write("===============\n")
  statsfile.write("TOTAL :")
  for stat, val in sorted(total.items()):
    statsfile.write(" %d %s" % (val, stat))
  statsfile.write("\n")
if __name__ == '__main__':
  main()
