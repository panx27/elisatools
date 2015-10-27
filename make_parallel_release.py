#! /usr/bin/env python
import argparse
import sys
import codecs
from collections import defaultdict as dd
import lxml.etree as ET
import gzip
import re
import os.path
import hashlib
from itertools import izip
from itertools import izip_longest
scriptdir = os.path.dirname(os.path.abspath(__file__))

# TODO: option to build gzip file

def main():
  parser = argparse.ArgumentParser(description="Create xml from extracted" \
                                   " and transformed monolingual data",
                                   formatter_class= \
                                   argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--rootdir", "-r", default=".", help="root lrlp dir")
  parser.add_argument("--lang", "-l", help="lrlp language code")
  parser.add_argument("--corpora", "-c", nargs='+', help="prefixes that have " \
                      "at minimum a manifest and original/ file")
  parser.add_argument("--outfile", "-o", type=argparse.FileType('w'),
                      default=sys.stdout, help="output file")
  parser.add_argument("--psmfile", "-p", type=argparse.FileType('r'),
                      help="psm annotation file")
  parser.add_argument("--annfile", "-a", type=argparse.FileType('r'),
                      help="entity annotation file")
  parser.add_argument("--evaluation", "-e", action='store_true',
                      default=False, help="prodece source side only")

  try:
    args = parser.parse_args()
  except IOError, msg:
    parser.error(str(msg))

  reader = codecs.getreader('utf-8')
  writer = codecs.getwriter('utf-8')
  outfile = args.outfile
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
    for ln, line in enumerate(reader(args.psmfile)):
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
        print ln
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
    for ln, line in enumerate(reader(args.annfile)):
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
        print ln
        raise
    sys.stderr.write("Discarded %d ann entries\n" % anndiscardcount)
  # Will fill on demand
  anns = dd(lambda: dd(list))

  # Each segment is a legit xml block. the corpus/language/document are faked
  # TODO: corpus/document
  # TODO: make this more generalizable!
  outfile.write('<?xml version="1.0" encoding="UTF-8"?>\n')
  outfile.write('<!DOCTYPE ELISA_BILINGUAL_LRLP_CORPUS SYSTEM ' \
                '"elisa.lrlp-eng.v1.0.dtd">\n')
  outfile.write('<ELISA_BILINGUAL_LRLP_CORPUS source_language="%s" ' \
                'target_language="eng">\n' % args.lang)
  count = 0
  for corpus in args.corpora:
    corpus = corpus.replace('.manifest', '')
    src_manifest = reader(open(os.path.join(args.rootdir, "%s.%s.manifest" % \
                                            (corpus, args.lang))))
    trg_manifest = reader(open(os.path.join(args.rootdir, "%s.eng.manifest" % \
                                            (corpus))))
    src_origfile = reader(open(os.path.join(args.rootdir, "original",
                                            "%s.original.%s.flat" % \
                                            (corpus, args.lang))))
    trg_origfile = reader(open(os.path.join(args.rootdir, "original",
                                            "%s.original.eng.flat" % (corpus))))
    src_tokfile = reader(open(os.path.join(args.rootdir, "tokenized",
                                           "%s.tokenized.%s.flat" % \
                                           (corpus, args.lang))))
    trg_tokfile = reader(open(os.path.join(args.rootdir, "tokenized",
                                           "%s.tokenized.eng.flat" % (corpus))))
    ### TODO: Add cede, isi tokenization

    src_morphtokfile = reader(open(os.path.join(args.rootdir, "morph-tokenized",
                                                "%s.morph-tokenized.%s.flat" % \
                                                (corpus,args.lang))))
    trg_morphtokfile = reader(open(os.path.join(args.rootdir, "morph-tokenized",
                                               "%s.morph-tokenized.eng.flat" % \
                                                (corpus))))
    src_morphfile = reader(open(os.path.join(args.rootdir, "morph",
                                             "%s.morph.%s.flat" % \
                                             (corpus, args.lang))))
    trg_morphfile = reader(open(os.path.join(args.rootdir, "morph",
                                             "%s.morph.eng.flat" % (corpus))))
    src_posfile = reader(open(os.path.join(args.rootdir, "pos",
                                           "%s.pos.%s.flat" % \
                                           (corpus, args.lang))))
    trg_posfile = reader(open(os.path.join(args.rootdir, "pos",
                                           "%s.pos.eng.flat" % (corpus))))
    src_lastfullid = None

    ### ---------------------- Regular Parallel ----------------------
    iteration = izip(src_manifest, trg_manifest, src_origfile, trg_origfile,
                src_tokfile, trg_tokfile, src_morphtokfile, trg_morphtokfile,
                src_morphfile, trg_morphfile, src_posfile, trg_posfile)
    for src_manline, trg_manline, \
        src_origline, trg_origline, \
        src_tokline, trg_tokline, \
        src_morphtokline, trg_morphtokline, \
        src_morphline, trg_morphline, \
        src_posline, trg_posline \
        in iteration:

      src_origline = src_origline.strip()
      src_tokline = src_tokline.strip()
      src_morphtokline = src_morphtokline.strip()
      src_morphline = src_morphline.strip()
      src_posline = src_posline.strip()
      src_man = src_manline.strip().split('\t')
      src_fullid = src_man[1]
      src_fullidsplit = src_fullid.split('_')
      if corpus == 'fromtarget.elicitation':
        src_fullidsplit = ['ELICITATION', 'NONE', args.lang.upper(),
                           'NONE', 'NONE']
      if corpus == 'fromtarget.phrasebook':
        src_fullidsplit = ['PHRASEBOOK', 'NONE', args.lang.upper(),
                           'NONE', 'NONE']
      trg_origline = trg_origline.strip()
      trg_tokline = trg_tokline.strip()
      trg_morphtokline = trg_morphtokline.strip()
      trg_morphline = trg_morphline.strip()
      trg_posline = trg_posline.strip()
      trg_man = trg_manline.strip().split('\t')
      trg_fullid = trg_man[1]

      fullidfields = ['GENRE', 'PROVENANCE', 'SOURCE_LANGUAGE',
                      'INDEX_ID', 'DATE']

      # Faking the document-level
      if src_lastfullid != src_fullid:
        if src_lastfullid is not None:
          outfile.write("</DOCUMENT>\n")
        src_lastfullid = src_fullid
        # outfile.write('<DOCUMENT id="%s" ' % fullid +
        #               'genre="%s" provenance="%s" language="%s" ' \
        #               'index_id="%s" date="%s">\n' % tuple(fullidsplit))
        outfile.write('<DOCUMENT id="%s">\n' % src_fullid)
        for label, value in zip(fullidfields, src_fullidsplit):
          outfile.write("  <%s>%s</%s>\n" % (label, value, label))
        outfile.write("  <TARGET_LANGUAGE>ENG</TARGET_LANGUAGE>\n")
        outfile.write("  <DIRECTION>%s</DIRECTION>\n" % \
                      re.match('(\w+)\..+', corpus).group(1))

      xroot = ET.Element('PARALLEL')
      # xroot.set('id', '{number:0{width}d}'.format(width=8, number=count))
      src_seg = ET.SubElement(xroot, 'SEGMENT_SOURCE')
      src_seg.set('id', src_man[2])
      src_seg.set('start_char', src_man[3])
      src_seg.set('end_char', src_man[4])

      subelements = []
      subelements.append(("FULL_ID_SOURCE", src_man[1]))
      subelements.append(("ORIG_RAW_SOURCE", src_origline))
      src_md5 = hashlib.md5(src_origline.encode('utf-8')).hexdigest()
      subelements.append(("MD5_HASH_SOURCE", src_md5))
      subelements.append(("LRLP_TOKENIZED_SOURCE", src_tokline))
      subelements.append(("LRLP_MORPH_TOKENIZED_SOURCE", src_morphtokline))
      subelements.append(("LRLP_MORPH_SOURCE", src_morphline))
      subelements.append(("LRLP_POSTAG_SOURCE", src_posline))

      # On-demand fill of psms and anns hashes that assumesit will be
      # used contiguously
      if src_fullid in psmtemp:
        psms.clear()
        data = psmtemp.pop(src_fullid)
        for tup in data:
          start = int(tup[2])
          end = start+int(tup[3])
          for i in xrange(start, end):
            psms[src_fullid][i].append(tup)

      if src_fullid in psms:
        # Collect the annotations
        psmcoll = set()
        startchar = int(src_man[3])
        endchar = int(src_man[4])
        if endchar > len(psms[src_fullid]):
          endchar = None
        for i in xrange(startchar, endchar):
          slot = psms[src_fullid][i]
          psmcoll.update(map(tuple, slot))
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
          for i in xrange(start, end):
            anns[src_fullid][i].append(tup)

      if src_fullid in anns:
        # Collect the annotations
        anncoll = set()
        startchar = int(src_man[3])
        endchar = min(len(anns[src_fullid]), int(src_man[4]))
        for i in xrange(startchar, endchar):
          slot = anns[src_fullid][i]
          anncoll.update(map(tuple, slot))
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
        trg_seg = ET.SubElement(xroot, 'SEGMENT_TARGET')
        trg_seg.set('id', trg_man[2])
        trg_seg.set('start_char', trg_man[3])
        trg_seg.set('end_char', trg_man[4])
        ET.SubElement(trg_seg, "FULL_ID_TARGET").text = trg_fullid
        ET.SubElement(trg_seg, "ORIG_RAW_TARGET").text = trg_origline
        trg_md5 = hashlib.md5(trg_origline.encode('utf-8')).hexdigest()
        ET.SubElement(trg_seg, "MD5_HASH_TARGET").text = trg_md5
        ET.SubElement(trg_seg, "LRLP_TOKENIZED_TARGET").text = trg_tokline
        ET.SubElement(trg_seg,
                      "LRLP_MORPH_TOKENIZED_TARGET").text = trg_morphtokline
        ET.SubElement(trg_seg, "LRLP_MORPH_TARGET").text = trg_morphline
        ET.SubElement(trg_seg, "LRLP_POSTAG_TARGET").text = trg_posline

      xmlstr = ET.tostring(xroot, pretty_print=True, encoding='utf-8',
                           xml_declaration=False)
      outfile.write(xmlstr)
      count += 1
    outfile.write("</DOCUMENT>\n")
    ### ------------------ End of Regular Parallel ------------------

    ### ---------------------- Tweets Parallel ----------------------
    if corpus == 'fromsource.tweet':
      iteration = izip(src_manifest, trg_manifest, src_origfile, trg_origfile)
      for src_manline, trg_manline, \
          src_origline, trg_origline \
          in iteration:

        src_origline = src_origline.strip()
        src_man = src_manline.strip().split('\t')
        src_fullid = src_man[1]
        src_fullidsplit = src_fullid.split('_')
        trg_origline = trg_origline.strip()
        trg_man = trg_manline.strip().split('\t')
        trg_fullid = trg_man[1]

        fullidfields = ['GENRE', 'PROVENANCE', 'SOURCE_LANGUAGE',
                        'INDEX_ID', 'DATE']

        # Faking the document-level
        if src_lastfullid != src_fullid:
          if src_lastfullid is not None:
            outfile.write("</DOCUMENT>\n")
          src_lastfullid = src_fullid
          # outfile.write('<DOCUMENT id="%s" ' % fullid +
          #               'genre="%s" provenance="%s" language="%s" ' \
          #               'index_id="%s" date="%s">\n' % tuple(fullidsplit))
          outfile.write('<DOCUMENT id="%s">\n' % src_fullid)
          for label, value in zip(fullidfields, src_fullidsplit):
            outfile.write("  <%s>%s</%s>\n" % (label, value, label))
          outfile.write("  <TARGET_LANGUAGE>ENG</TARGET_LANGUAGE>\n")
          outfile.write("  <DIRECTION>%s</DIRECTION>\n" % \
                        re.match('(\w+)\..+', corpus).group(1))

        xroot = ET.Element('PARALLEL')
        # xroot.set('id', '{number:0{width}d}'.format(width=8, number=count))
        src_seg = ET.SubElement(xroot, 'SEGMENT_SOURCE')
        src_seg.set('id', 'segment-0')
        src_seg.set('start_char', '0')
        # THE END OFFSET MIGHT BE WRONG
        src_seg.set('end_char', str(len(src_origline.encode('utf-8'))))

        subelements = []
        subelements.append(("FULL_ID_SOURCE", src_man[1]))
        subelements.append(("ORIG_RAW_SOURCE", src_origline))
        src_md5 = hashlib.md5(src_origline.encode('utf-8')).hexdigest()
        subelements.append(("MD5_HASH_SOURCE", src_md5))

        # On-demand fill of psms and anns hashes that assumesit will be
        # used contiguously
        if src_fullid in psmtemp:
          psms.clear()
          data = psmtemp.pop(src_fullid)
          for tup in data:
            start = int(tup[2])
            end = start+int(tup[3])
            for i in xrange(start, end):
              psms[src_fullid][i].append(tup)

        if src_fullid in psms:
          # Collect the annotations
          psmcoll = set()
          startchar = int(src_man[3])
          endchar = int(src_man[4])
          if endchar > len(psms[src_fullid]):
            endchar = None
          for i in xrange(startchar, endchar):
            slot = psms[src_fullid][i]
            psmcoll.update(map(tuple, slot))
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
            for i in xrange(start, end):
              anns[src_fullid][i].append(tup)

        if src_fullid in anns:
          # Collect the annotations
          anncoll = set()
          # startchar = int(src_man[3])
          # endchar = min(len(anns[src_fullid]), int(src_man[4]))
          startchar = 0
          endchar = len(anns[src_fullid])
          for i in xrange(startchar, endchar):
            slot = anns[src_fullid][i]
            anncoll.update(map(tuple, slot))
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
          trg_seg = ET.SubElement(xroot, 'SEGMENT_TARGET')
          trg_seg.set('id', 'segment-0')
          trg_seg.set('start_char', '0')
          # THE END OFFSET MIGHT BE WRONG
          trg_seg.set('end_char', str(len(trg_origline.encode('utf-8'))))
          ET.SubElement(trg_seg, "FULL_ID_TARGET").text = trg_fullid
          ET.SubElement(trg_seg, "ORIG_RAW_TARGET").text = trg_origline
          trg_md5 = hashlib.md5(trg_origline.encode('utf-8')).hexdigest()
          ET.SubElement(trg_seg, "MD5_HASH_TARGET").text = trg_md5

        xmlstr = ET.tostring(xroot, pretty_print=True, encoding='utf-8',
                             xml_declaration=False)
        outfile.write(xmlstr)
        count += 1
      outfile.write("</DOCUMENT>\n")
      ### ------------------ End of Tweets Parallel ------------------

  outfile.write("</ELISA_BILINGUAL_LRLP_CORPUS>\n")

  # Cannot retrieve all psm and ann
  # # TODO /corpus/document
  # # TODO: verify empty psm
  # for key in psmtemp.keys():
  #   print "Unvisited psm: " + key
  #   sys.stderr.write("Unvisited psm: %s\n" % key)
  # for key in anntemp.keys():
  #   print "Unvisited ann: " + key
  #   sys.stderr.write("Unvisited ann: %s\n" % key)

if __name__ == '__main__':
  main()
