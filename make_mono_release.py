#!/usr/bin/env python3
import argparse
import sys
import codecs
from collections import defaultdict as dd
import lxml.etree as ET
import gzip
import re
import os
import os.path
import hashlib

scriptdir = os.path.dirname(os.path.abspath(__file__))

def get_parallel_docs(paradir):
  paradocs = set()
  for root, dirs, files in os.walk(paradir):
    for file in files:
      if file.endswith('.manifest'):
        print(file)
        for line in open('%s/%s' % (root, file)):
          print(line)
          paradocs.add(line.split('\t')[1])
  return paradocs

def main():
  parser = argparse.ArgumentParser(description="Create xml from extracted" \
                                   " and transformed monolingual data",
                                   formatter_class= \
                                   argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--rootdir", "-r", default=".", help="root lrlp dir")
  parser.add_argument("--lang", "-l", help="lrlp language code")
  parser.add_argument("--corpora", "-c", nargs='+', help="prefixes that have " \
                      "at minimum a manifest and original/ file")
  parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('w'),
                      default=sys.stdout, help="output file")
  parser.add_argument("--psmfile", "-p", nargs='?', type=argparse.FileType('r'),
                      default=None, help="psm annotation file")
  parser.add_argument("--annfile", "-a", nargs='?', type=argparse.FileType('r'),
                      default=None, help="entity annotation file")
  parser.add_argument("--paradir", "-pa", default=None, help="parallel flat dir")
  parser.add_argument("--statsfile", "-s", type=argparse.FileType('w'),
                      default=sys.stderr, help="file to write statistics")

  try:
    args = parser.parse_args()
  except IOError as msg:
    parser.error(str(msg))

  outfile = args.outfile
  statsfile = args.statsfile
  # outfile = writer(args.outfile)

  paradocs = get_parallel_docs(args.paradir) if args.paradir is not None else set()

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
  outfile.write('<!DOCTYPE ELISA_LRLP_CORPUS SYSTEM "elisa.lrlp.v1.1.dtd">\n')
  outfile.write('<ELISA_LRLP_CORPUS source_language="%s">\n' % args.lang)
  for corpus in args.corpora:
    corpus = corpus.replace('.manifest', '')
    manifest =      open(os.path.join(args.rootdir, "%s.manifest" % corpus))
    origfile =      open(os.path.join(args.rootdir,
                                 "original", "%s.flat" % corpus))
    tokfile =       open(os.path.join(args.rootdir,
                                "tokenized", "%s.flat" % corpus))
    cdectokfile =   open(os.path.join(args.rootdir,"cdec-tokenized",
                                    "%s.flat" % corpus))
    cdectoklcfile = open(os.path.join(args.rootdir, "cdec-tokenized",
                                      "%s.flat.lc" % corpus))
    morphtokfile =  open(os.path.join(args.rootdir, "morph-tokenized",
                                     "%s.flat" % corpus))
    morphfile =     open(os.path.join(args.rootdir, "morph",
                                  "%s.flat" % corpus))
    posfile =       open(os.path.join(args.rootdir, "pos",
                                         "%s.flat" % corpus))
    lastfullid = None
    for manline, origline, tokline, cdectokline, cdectoklcline, morphtokline, \
    morphline, posline in zip(manifest, origfile, tokfile, cdectokfile,
                              cdectoklcfile, morphtokfile, morphfile, posfile):
      origline = origline.strip()
      tokline = tokline.strip()
      cdectokline = cdectokline.strip()
      cdectoklcline = cdectoklcline.strip()
      morphtokline = morphtokline.strip()
      morphline = morphline.strip()
      posline = posline.strip()
      man = manline.strip().split('\t')
      fullid = man[1]
      fullidsplit = fullid.split('_')
      # old style: genre(2)_prov(3)_lang(3)_id(var)_date(8)
      # new style: lang(3)_genre(2)_prov(6)_date(8)_id(9)
      fullidfields = ['GENRE', 'PROVENANCE', 'SOURCE_LANGUAGE', 'INDEX_ID', 'DATE']
      if fullid[3] == "_" and fullid[6] == "_" and fullid[13] == "_":
        fullidfields = ['SOURCE_LANGUAGE', 'GENRE', 'PROVENANCE', 'DATE', 'INDEX_ID']
      elif fullid[2] != "_" or fullid[6] != "_" or fullid[10] != "_":
        sys.stderr.write("unexpected filename format: "+fullid+"\n")
      if fullid in paradocs: # Parallel data is not repeated in the mono data
        #sys.stderr.write("Document %s exists in parallel data\n" % fullid)
        continue

      # Faking the document-level
      if lastfullid != fullid:
        stats[corpus]["DOCS"]+=1
        if lastfullid is not None:
          outfile.write("</DOCUMENT>\n")
        lastfullid = fullid
        # outfile.write('<DOCUMENT id="%s" ' % fullid +
        #               'genre="%s" provenance="%s" language="%s" ' \
        #               'index_id="%s" date="%s">\n' % tuple(fullidsplit))
        outfile.write('<DOCUMENT id="%s">\n' % fullid)
        for label, value in zip(fullidfields, fullidsplit):
          outfile.write("  <%s>%s</%s>\n" % (label, value, label))
        outfile.write("  <DIRECTION>fromsource</DIRECTION>\n")
      stats[corpus]["SEGMENTS"]+=1
      stats[corpus]["WORDS"] += len(origline.split())
      segroot = ET.Element('SEGMENT')
      if len(man) > 5 and man[5] == "dl":
        segroot.set("downloaded", "true")
      xroot = ET.SubElement(segroot, 'SOURCE')
      xroot.set('id', "%s.%s.%s.%s" % (man[1],man[2],man[3],man[4]))
      xroot.set('start_char', man[3])
      xroot.set('end_char', man[4])
      subelements = []
      # subelements.extend(zip(fullidfields, fullidsplit))
      # subelements.extend(zip(['SEGMENT_ID', 'START_CHAR', 'END_CHAR'], man[2:]))
      subelements.append(("FULL_ID_SOURCE", man[1])) # TODO: bad name
      subelements.append(("ORIG_SEG_ID", man[2])) # for nistification
      subelements.append(("ORIG_FILENAME", os.path.basename(man[0]))) # for nistification
      subelements.append(("ORIG_RAW_SOURCE", origline))
      subelements.append(("MD5_HASH_SOURCE",
                          hashlib.md5(origline.encode('utf-8')).hexdigest()))
      subelements.append(("LRLP_TOKENIZED_SOURCE", tokline))
      subelements.append(("CDEC_TOKENIZED_SOURCE", cdectokline))
      subelements.append(("CDEC_TOKENIZED_LC_SOURCE", cdectoklcline))
      subelements.append(("LRLP_POSTAG_SOURCE", posline))
      # don't add morph info if there's nothing interesting
      morphset = set(morphline.split())
      if len(morphset) == 1 and list(morphset)[0] == "none":
        pass
      else:
        subelements.append(("LRLP_MORPH_TOKENIZED_SOURCE", morphtokline))
        subelements.append(("LRLP_MORPH_SOURCE", morphline))


      # On-demand fill of psms and anns hashes that assumesit will be
      # used contiguously
      if fullid in psmtemp:
        psms.clear()
        data = psmtemp.pop(fullid)
        for tup in data:
          start = int(tup[2])
          end = start+int(tup[3])
          for i in range(start, end):
            psms[fullid][i].append(tup)

      if fullid in psms:
        # Collect the annotations
        psmcoll = set()
        startchar = int(man[3])
        endchar = int(man[4])
        if endchar > len(psms[fullid]):
          endchar = None
        for i in range(startchar, endchar):
          slot = psms[fullid][i]
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

      if fullid in anntemp:
        anns.clear()
        data = anntemp.pop(fullid)
        for tup in data:
          start = int(tup[2])
          end = int(tup[3])
          for i in range(start, end):
            anns[fullid][i].append(tup)

      if fullid in anns:
        # Collect the annotations
        anncoll = set()
        startchar = int(man[3])
        endchar = min(len(anns[fullid]), int(man[4]))
        for i in range(startchar, endchar):
          slot = anns[fullid][i]
          anncoll.update(list(map(tuple, slot)))
        if len(anncoll) > 0:
          ae = ET.SubElement(xroot, "ANNOTATIONS")
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
        se = ET.SubElement(xroot, key)
        se.text = text
      # Entity/semantic annotations in their own block if fullid in anns

      xmlstr = ET.tostring(segroot, pretty_print=True, encoding='utf-8',
                           xml_declaration=False).decode('utf-8')
      outfile.write(xmlstr)
    if lastfullid is not None:
      outfile.write("</DOCUMENT>\n")
  outfile.write("</ELISA_LRLP_CORPUS>\n")

  # TODO /corpus/document
  # TODO: verify empty psm
  for key in list(psmtemp.keys()):
    sys.stderr.write("Unvisited psm: %s\n" % key)
  for key in list(anntemp.keys()):
    sys.stderr.write("Unvisited ann: %s\n" % key)

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
