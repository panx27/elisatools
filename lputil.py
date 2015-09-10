#! /usr/bin/env python
# utilities for dealing with LRLPs
import argparse
import sys
import os
import re
import os.path
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import ParseError



def funornone(entity, fun, default="None"):
  ''' Apply fun to entity if it is not NoneType. Otherwise, return default '''
  if entity is None:
    return default
  return fun(entity)

def whitelistmatch(wlist, sents):
  ''' given a list of words and a list of strings, return true if at least one word is in at least one string '''
  return any(any(w in s for s in sents) for w in wlist)

def get_aligned_sentences(srcfile, trgfile, alignfile, tokenize=False, xml=False):
  if xml:
    return get_aligned_sentences_xml(srcfile, trgfile, alignfile, tokenize=tokenize)
  return get_aligned_sentences_flat(srcfile, trgfile, alignfile)


def get_aligned_sentences_flat(srcfile, trgfile, alignfile):
  import codecs
  ''' build sentence pairs given raw files and character alignment info '''
  slines = []
  tlines = []
  s = None
  t = None
  with codecs.open(srcfile, 'r', 'utf-8') as f:
    s = f.read()
  with codecs.open(trgfile, 'r', 'utf-8') as f:
    t = f.read()
  with open(alignfile) as f:
    for line in f.readlines():
      ss, sl, ts, tl = map(int, line.strip().split('\t'))
      slines.append(s[ss:ss+sl]+"\n")
      tlines.append(t[ts:ts+tl]+"\n")
  return (slines, tlines)



def spans_from_xml(spans, xml, tokenize=True):
  ''' utility function; given list of start, end tuples and 
  xml node return list of list of words '''
  toks = []
  if tokenize:
    for tok in  xml.findall(".//TOKEN"):
      toks.append((int(tok.get('start_char')), int(tok.get('end_char')), tok.text))
  else:
    for tok in xml.findall(".//SEG"):
      toks.append((int(tok.get('start_char')), int(tok.get('end_char')), tok.find("ORIGINAL_TEXT").text))
  for start, end in spans:
    span = []
    firsts = 0
    laste = 0
    # TODO: make more efficient; consume tokens!
    for s, e, text in toks:
      # not yet in range (move on)
      if e < start:
        continue
      # in range (append)
      if s >= start and e <= end:
        if len(span) == 0:
          firsts = s
        span.append(text)
        laste = e
        continue
      # out of range (quit)
      if s > end:
        break
      # border crossing (yell)
      if s < start and e >= start or s <= end and e > end:
        sys.stderr.write("Tokens cross alignment boundaries; (%d, %d) vs (%d, %d)\n" % (start, end, s, e))
        sys.exit(1)
    if firsts != start or laste+1 != end:
      id = xml.find(".//DOC").get('id')
      sys.stderr.write("Warning: in %s should be (%d %d) but actually (%d %d)\n" % (id, start, end, firsts, laste))
      continue
    yield span


def get_aligned_sentences_xml(srcfile, trgfile, alignfile, tokenize=False):
   ''' build sentence pairs given xml files and character alignment info '''
   slines = []
   tlines = []
   srcspans = []
   trgspans = []
   with open(alignfile) as f:
     for line in f.readlines():
       ss, sl, ts, tl = map(int, line.strip().split('\t'))
       srcspans.append((ss, ss+sl))
       trgspans.append((ts, ts+tl))
   import xml.etree.ElementTree as ET
   sroot = ET.parse(srcfile)
   for span in spans_from_xml(srcspans, sroot, tokenize):
     slines.append(' '.join(span)+'\n')
   troot = ET.parse(trgfile)
   for span in spans_from_xml(trgspans, troot, tokenize):
     tlines.append(' '.join(span)+'\n')
   return (slines, tlines)


def pair_files(srcdir, trgdir, ext='txt'):
  ''' heuristically pair files from rsd directories together
  based on observed filename conventions. Warn on unmatched files 
  and mismatched lengths '''
  if (not os.path.exists(srcdir)) or (not os.path.exists(trgdir)):
    sys.stderr.write("Warning: couldn't find "+srcdir+" or "+trgdir+"\n")
    return ([], [], [])
  pats = []
  # from src:
    # DF_CHO_UZB_014366_20140900.eng.rsd.txt vs DF_CHO_UZB_014366_20140900.rsd.txt
  pat_from_src = re.compile(r"(.._...)_..._([^_.]+_[^_.]+).*\."+ext)
  repl_from_src = r"%s_..._%s.*\."+ext
  pats.append((pat_from_src, repl_from_src))

  # from trg news:
  # AFP_ENG_20020426.0319.uzb.rsd.txt vs AFP_ENG_20020426.0319.rsd.txt
  pat_from_trg_news = re.compile(r"([^\._]+)_..._([\d\.]+).*\."+ext)
  repl_from_trg_news = r"%s_..._%s.*\."+ext
  pats.append((pat_from_trg_news, repl_from_trg_news ))

  # from trg elic
  # XXX_Elicitation, elicitation_sentences, ???

  pat_from_trg_elic = re.compile(r"([^\.].*licitation[^.]*).*\."+ext)
  repl_from_trg_elic = r"%s.*\."+ext
  pats.append((pat_from_trg_elic, repl_from_trg_elic ))


  # from trg pbook

  pat_from_trg_pbook = re.compile(r"([^\.].*Phrasebook).*\."+ext)
  repl_from_trg_pbook = r"%s.*\."+ext
  pats.append((pat_from_trg_pbook, repl_from_trg_pbook ))

  matches = []
  unsrcs = []
  trgfiles = os.listdir(trgdir)
  for srcfile in os.listdir(srcdir):
    filematch = None
    for pat, repltmp in pats:
      #print "Trying "+str(pat)+" on "+srcfile
      if re.match(pat, srcfile):
        #print "Matched"
        repl = repltmp % re.match(pat, srcfile).groups()
        #print "Using "+repl+" to match "+srcfile
        for trgfile in trgfiles:
          if re.match(repl, trgfile):
            #print "Matched to "+trgfile+"!"
            filematch= trgfile
            break # from trg file search
        if filematch is not None:
          break # from pattern search
    if filematch is not None:
      trgfiles.remove(filematch)
      matches.append((os.path.join(srcdir, srcfile), 
                      os.path.join(trgdir, filematch)))
    else:
      #print "No match for "+srcdir+"/"+srcfile
      unsrcs.append(srcfile)
  return (matches, unsrcs, trgfiles)

def pair_found_files(srcdir, trgdir, aldir, ext='txt'):
  ''' heuristically pair files from found directories together
  based on observed filename conventions. Warn on unmatched files '''
  if (not os.path.exists(srcdir)) or (not os.path.exists(trgdir)) or (not os.path.exists(aldir)):
    sys.stderr.write("Warning: couldn't find "+srcdir+" or "+trgdir+"or "+aldir+"\n")
    return ([], [], [], [])

  pats = []
  # orig
  # NW_UZA_UZB_165826_20070808.align
  # NW_UZA_UZB_165826_20070808.rsd.txt
  # NW_UZA_UZB_165826_20070808.found.eng.rsd.txt

  pat_al = re.compile(r"([^.]+).*\.align")
  repl = r"%s.*\."+ext
  pats.append((pat_al, repl))

  matches = []
  unals = []
  trgfiles = os.listdir(trgdir)
  srcfiles = os.listdir(srcdir)
  alfiles = os.listdir(aldir)
  for alfile in alfiles:
    srcfilematch = None
    trgfilematch = None
    for pat, repltmp in pats:
#      print "Trying "+str(pat)+" on "+alfile
      if re.match(pat, alfile):
#        print "Matched"
        repl = repltmp % re.match(pat, alfile).groups()
#        print "Using "+repl+" to match "+alfile
        for trgfile in trgfiles:
          if re.match(repl, trgfile):
#            print "Matched to target "+trgfile+"!"
            trgfilematch= trgfile
            break # from trg file search
        if trgfilematch is None:
          break # from pattern search
        for srcfile in srcfiles:
          if re.match(repl, srcfile):
#            print "Matched to "+srcfile+"!"
            srcfilematch= srcfile
            break # from trg file search
        if srcfilematch is not None:
          break # from pattern search

    if srcfilematch is not None and trgfilematch is not None:
#      print "Matched "+alfile+" "+srcfilematch+" "+trgfilematch
      trgfiles.remove(trgfilematch)
      srcfiles.remove(srcfilematch)
      matches.append((os.path.join(srcdir, srcfilematch), 
                      os.path.join(trgdir, trgfilematch),
                      os.path.join(aldir, alfile)))
    else:
#      print "No match for "+alfile
      unals.append(alfile)
  return (matches, srcfiles, trgfiles, unals)


def all_found_tuples(rootdir, src='uzb', trg='eng', xml=False):
  ''' traverse LRLP directory structure to build src, trg, align tuples of associated files '''
  matches = []
  tpath = os.path.join(rootdir, 'data', 'translation', 'found')
  pathext = "ltf" if xml else "rsd"
  fileext = "xml" if xml else "txt"

  src_path = os.path.join(tpath, src, pathext)
  trg_path = os.path.join(tpath, trg, pathext)
  al_path = os.path.join(tpath, 'sentence_alignment')
  (m, s, t, a) = pair_found_files(src_path, trg_path, al_path, ext=fileext)
  if len(s) > 0:
    sys.stderr.write("Warning: unmatched src files "+'\n'.join(s))
  if len(t) > 0:
    sys.stderr.write("Warning: unmatched trg files "+'\n'.join(t))
  if len(a) > 0:
    sys.stderr.write("Warning: unmatched align files "+'\n'.join(a))
  return m


def selected_translation_pairs(path, src='uzb', trg='eng', xml=False):
  ''' Generalization of all_translation_pairs: build pairs of associated files from
  specified path '''
  pathext = "ltf" if xml else "rsd"
  fileext = "xml" if xml else "txt"
  (m, s, t) = pair_files(os.path.join(path, src, pathext),
                         os.path.join(path, trg, pathext), ext=fileext)
  if len(s) > 0:
    sys.stderr.write("Warning: unmatched src files "+'\n'.join(s))
  if len(t) > 0:
    sys.stderr.write("Warning: unmatched trg files "+'\n'.join(t))
  return m

  
def all_translation_pairs(rootdir, src='uzb', trg='eng', xml=False):
  ''' traverse LRLP directory structure to build pairs of associated files '''
  matches = []
  tpath = os.path.join(rootdir, 'data', 'translation')
  pathext = "ltf" if xml else "rsd"
  fileext = "xml" if xml else "txt"
  from_src = os.path.join(tpath, "from_%s" % src)
  (m, s, t) = pair_files(os.path.join(from_src, src, pathext),
                         os.path.join(from_src, trg, pathext), ext=fileext)
  if len(s) > 0:
    sys.stderr.write("Warning: unmatched src files "+'\n'.join(s))
  if len(t) > 0:
    sys.stderr.write("Warning: unmatched trg files "+'\n'.join(t))
  matches.extend(m)


  for domain in ('news', 'phrasebook', 'elicitation'):
    from_trg = os.path.join(tpath, "from_%s" % trg, domain)
    (m, s, t) = pair_files(os.path.join(from_trg, src, pathext),
                           os.path.join(from_trg, trg, pathext), ext=fileext)
    if len(s) > 0:
      sys.stderr.write("Warning: unmatched src files "+'\n'.join(s)+'\n')
    if len(t) > 0:
      sys.stderr.write("Warning: unmatched trg files "+'\n'.join(t)+'\n')
    matches.extend(m)
  return matches

def get_tokens(xml):
  ''' Get tokenized data from xml ltf file '''
  return [ ' '.join([ y.text for y in x.findall(".//TOKEN") ])+"\n" for x in xml.findall(".//SEG") ]

def extract_lines(s, t, xml=True, tokenize=True):
  ''' given two files, open them and get data from them. Return as two lists of strings '''
  sl = []
  tl = []
  if xml:
    try:
      sroot = ET.parse(s)
      troot = ET.parse(t)
    except ParseError as detail:
      sys.stderr.write("Parse error on "+s+" and/or "+t+": "+str(detail)+"\n")
      return
    if tokenize:
      sl = get_tokens(sroot)
      tl = get_tokens(troot)
    else:
      sl = [ x.text+"\n" for x in sroot.findall(".//ORIGINAL_TEXT") ]
      tl = [ x.text+"\n" for x in troot.findall(".//ORIGINAL_TEXT") ]
  else:
    import codecs
    with codecs.open(s, 'r', 'utf-8') as f:
      sl = f.readlines()
    with codecs.open(t, 'r', 'utf-8') as f:
      tl = f.readlines()
  return (sl, tl)

def main():
  parser = argparse.ArgumentParser(description="Print parallel contents")
  parser.add_argument("--rootdir", "-r", help="root lrlp dir")
  parser.add_argument("--prefix", "-p", help="output files prefix")
  parser.add_argument("--src", "-s", default='uzb', help="source language 3 letter code")
  parser.add_argument("--trg", "-t", default='eng', help="target language 3 letter code")
  parser.add_argument("--xml", "-x", action='store_true', help="process ltf xml files")
  # TODO: make this more general!
  parser.add_argument("--targetwhitelist", nargs='?', type=argparse.FileType('r'), help="terms that must appear in kept data")
  parser.add_argument("--elseprefix", help="prefix for files not matching the target list, if set")
  parser.add_argument("--tokenize", action='store_true', help="use tokens (only applies if -x)")

  try:
    args = parser.parse_args()
  except IOError, msg:
    parser.error(str(msg))

  sfile = args.prefix+"."+args.src
  sman = sfile+".manifest"
  tfile = args.prefix+"."+args.trg
  tman = tfile+".manifest"
  sfh = open(sfile, 'w')
  tfh = open(tfile, 'w')
  smh = open(sman, 'w')
  tmh = open(tman, 'w')

  if args.elseprefix is not None:
    elsesfile = args.elseprefix+"."+args.src
    elsesman = elsesfile+".manifest"
    elsetfile = args.elseprefix+"."+args.trg
    elsetman = elsetfile+".manifest"
    elsesfh = open(elsesfile, 'w')
    elsetfh = open(elsetfile, 'w')
    elsesmh = open(elsesman, 'w')
    elsetmh = open(elsetman, 'w')

  whitelist = None
  if args.targetwhitelist is not None:
    whitelist = [ x.strip() for x in args.targetwhitelist.readlines() ]
  for s, t in all_translation_pairs(args.rootdir, src=args.src, trg=args.trg, xml=args.xml):
    sl = []
    tl = []
    if args.xml:
      try:
        sroot = ET.parse(s)
        troot = ET.parse(t)
      except ParseError as detail:
        sys.stderr.write("Parse error on "+s+" and/or "+t+": "+str(detail)+"\n")
        continue
      if args.tokenize:
        sl = get_tokens(sroot)
        tl = get_tokens(troot)
      else:
        sl = [ x.text+"\n" for x in sroot.findall(".//ORIGINAL_TEXT") ]
        tl = [ x.text+"\n" for x in troot.findall(".//ORIGINAL_TEXT") ]
    else:
      import codecs
      with codecs.open(s, 'r', 'utf-8') as f:
        sl = f.readlines()
      with codecs.open(t, 'r', 'utf-8') as f:
        tl = f.readlines()
    slen = len(sl)
    tlen = len(tl)
    if slen != tlen:
      sys.stderr.write("Warning: different number of lines in files:\n%s %d\n%s %d\n" % (s, slen, t, tlen))
      continue
    if whitelist is None or whitelistmatch(whitelist, tl):
      sfh.write(''.join(sl).encode('utf-8'))
      tfh.write(''.join(tl).encode('utf-8'))
      smh.write("%s %d\n" % (s, slen))
      tmh.write("%s %d\n" % (t, tlen))
    elif args.elseprefix is not None:
      elsesfh.write(''.join(sl).encode('utf-8'))
      elsetfh.write(''.join(tl).encode('utf-8'))
      elsesmh.write("%s %d\n" % (s, slen))
      elsetmh.write("%s %d\n" % (t, tlen))



if __name__ == '__main__':
  main()

