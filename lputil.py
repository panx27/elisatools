#! /usr/bin/env python
# utilities for dealing with LRLPs
import argparse
import sys
import os
import re
import os.path
from collections import defaultdict as dd
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import ParseError
from subprocess import check_output, check_call, CalledProcessError

scriptdir = os.path.dirname(os.path.abspath(__file__))

# http://stackoverflow.com/questions/600268/mkdir-p-functionality-in-python
import os, errno
def mkdir_p(path):
  try:
    os.makedirs(path)
  except OSError as exc: # Python >2.5
    if exc.errno == errno.EEXIST and os.path.isdir(path):
      pass
    else: raise
    
def funornone(entity, fun, default="None"):
  ''' Apply fun to entity if it is not NoneType. Otherwise, return default '''
  if entity is None:
    return default
  return fun(entity)

def whitelistmatch(wlist, sents):
  ''' Given a list of words and a list of strings, return true if
  at least one word is in at least one string '''
  return any(any(w in s for s in sents) for w in wlist)

def get_aligned_sentences(srcfile, trgfile, alignfile,
                          xml=False):
  if xml:
    return get_aligned_sentences_xml(srcfile, trgfile,
                                     alignfile)
  return get_aligned_sentences_flat(srcfile, trgfile, alignfile)

def get_aligned_sentences_flat(srcfile, trgfile, alignfile):
  import codecs
  ''' Build sentence pairs given raw files and character alignment info '''
  slines = []
  tlines = []
  sids = []
  tids = []
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
      sids.append(srcfile+"\n")
      tids.append(trgfile+"\n")
  ret = []
  ret.append({"DOCID":sids,"ORIG":slines})
  ret.append({"DOCID":tids,"ORIG":tlines})
  return ret

def spans_from_xml(spans, xml, tokenize):
  ''' utility function; given list of start, end tuples and
  xml node return list of list of words '''
  # we expect this to be called twice, and get the segment id the second time. kludgy!!
  toks = []
  docid = xml.find(".//DOC").get('id')
  if tokenize:
    for tok in xml.findall(".//TOKEN"):
      toks.append((int(tok.get('start_char')), int(tok.get('end_char')),
                   tok, ""))
  else:
    for tok in xml.findall(".//SEG"):
      toks.append((int(tok.get('start_char')), int(tok.get('end_char')),
                   tok.find("ORIGINAL_TEXT"), tok.get('id')))
  segid = ""
  for start, end in spans:
    span = []
    firsts = 0
    laste = 0
    # TODO: make more efficient; consume tokens!
    for s, e, tok, id in toks:
      segid = id
      # Not yet in range (move on)
      if e < start:
        continue
      # In range (append)
      if s >= start and e <= end:
        if len(span) == 0:
          firsts = s
        span.append(tok)
        laste = e
        continue
      # Out of range (quit)
      if s > end:
        break
      # Border crossing (yell)
      if s < start and e >= start or s <= end and e > end:
        sys.stderr.write("Tokens cross alignment boundaries;" \
                         " (%d, %d) vs (%d, %d)\n" % (start, end, s, e))
        sys.exit(1)
    if firsts != start or laste+1 != end:
      sys.stderr.write("Warning: in %s should be (%d %d) but actually" \
                       " (%d %d)\n" % (docid, start, end, firsts, laste))
      continue
    yield span, docid, segid, start, end


def get_aligned_sentences_xml(srcfile, trgfile, alignfile):
  ''' Build sentence pairs given xml files and character alignment info '''
  srcspans = []
  trgspans = []
  sdata = dd(list)
  tdata = dd(list)
  with open(alignfile) as f:
    for line in f.readlines():
      ss, sl, ts, tl = map(int, line.strip().split('\t'))
      srcspans.append((ss, ss+sl))
      trgspans.append((ts, ts+tl))
  import xml.etree.ElementTree as ET
  for file, spans, data in zip((srcfile, trgfile), (srcspans, trgspans), (sdata, tdata)):
    root = ET.parse(file)
    # cf. get_segments
    for span, docid, _, start, end in spans_from_xml(spans, root, True):
      data["DOCID"].append(docid)
      # segid is bad here
      data["START"].append(str(start))
      data["END"].append(str(end))
      data["TOK"].append(' '.join([x.text for x in span])+'\n')
      data["POS"].append(' '.join([x.get("pos") for x in span])+'\n')
      mt_tmp = []
      mtt_tmp = []
      for x in span:
        for mt, mtt in morph_tok(x):
          mt_tmp.append(mt)
          mtt_tmp.append(mtt)
      data["MORPH"].append(' '.join(mt_tmp)+'\n')
      data["MORPHTOK"].append(' '.join(mtt_tmp)+'\n')
    # TODO: is this needed?
    root = ET.parse(file)
    for span, _, segid, start, end in spans_from_xml(spans, root, False):
      # only segid is good here
      data["ORIG"].append(' '.join([x.text for x in span])+'\n')
      data["SEGID"].append(segid)
    lengths = [len(i) for i in data.values()]
    for length in lengths[1:]:
      if length != lengths[0]:
        sys.stderr.write("Length mismatch in "+x+": "+str(lengths))
        sys.exit(1)

  return [sdata, tdata]

def pair_files(srcdir, trgdir, ext='txt'):
  ''' Heuristically pair files from rsd directories together based on observed
  filename conventions. Warn on unmatched files and mismatched lengths
  if xml is False, .ltf.xml -> .rsd.txt'''
  if (not os.path.exists(srcdir)) or (not os.path.exists(trgdir)):
    sys.stderr.write("Warning: couldn't find "+srcdir+" or "+trgdir+"\n")
    return ([], [], [])
  pats = []
  # From src:
  # DF_CHO_UZB_014366_20140900.eng.ltf.xml vs DF_CHO_UZB_014366_20140900.ltf.xml
  pat_from_src = re.compile(r"(.._...)_..._([^_.]+_[^_.]+).*\."+ext)
  repl_from_src = r"%s_..._%s.*\."+ext
  pats.append((pat_from_src, repl_from_src))

  # From trg news:
  # AFP_ENG_20020426.0319.uzb.ltf.xml vs AFP_ENG_20020426.0319.ltf.xml
  pat_from_trg_news = re.compile(r"([^\._]+)_..._([\d\.]+).*\."+ext)
  repl_from_trg_news = r"%s_..._%s.*\."+ext
  pats.append((pat_from_trg_news, repl_from_trg_news))

  # From trg elic
  # elicitation_sentences.uzb.ltf.xml vs elicitation_sentences.ltf.xml
  pat_from_trg_elic = re.compile(r"([^\.].*licitation[^.]*).*\."+ext)
  repl_from_trg_elic = r"%s.*\."+ext
  pats.append((pat_from_trg_elic, repl_from_trg_elic))

  # From trg pbook
  # English_Phrasebook.uzb.ltf.xml vs English_Phrasebook.ltf.xml
  pat_from_trg_pbook = re.compile(r"([^\.].*Phrasebook).*\."+ext)
  repl_from_trg_pbook = r"%s.*\."+ext
  pats.append((pat_from_trg_pbook, repl_from_trg_pbook))
  matches = []
  unsrcs = []
  trgfiles = os.listdir(trgdir)
  for srcfile in os.listdir(srcdir):
    filematch = None
    for pat, repltmp in pats:
      # print "Trying "+str(pat)+" on "+srcfile
      if re.match(pat, srcfile):
        # print "Matched"
        repl = repltmp % re.match(pat, srcfile).groups()
        # print "Using "+repl+" to match "+srcfile
        for trgfile in trgfiles:
          if re.match(repl, trgfile):
            # print "Matched to "+trgfile+"!"
            filematch= trgfile
            break # From trg file search
        if filematch is not None:
          break # From pattern search
    if filematch is not None:
      trgfiles.remove(filematch)
      matches.append((os.path.join(srcdir, srcfile),
                      os.path.join(trgdir, filematch)))
    else:
      sys.stderr.write("No match for "+srcdir+"/"+srcfile+"\n")
      # unsrcs.append(srcfile)
      unsrcs.append(srcdir+"/"+srcfile)
  return (matches, unsrcs, ['%s/%s' % (trgdir, i) for i in trgfiles])

def pair_found_files(srcdir, trgdir, aldir, ext='txt'):
  ''' Heuristically pair files from found directories together
  based on observed filename conventions. Warn on unmatched files '''
  if (not os.path.exists(srcdir)) or (not os.path.exists(trgdir)) or \
     (not os.path.exists(aldir)):
    sys.stderr.write("Warning: couldn't find "+srcdir+" or "+ \
                     trgdir+"or "+aldir+"\n")
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
      # print "Trying "+str(pat)+" on "+alfile
      if re.match(pat, alfile):
        # print "Matched"
        repl = repltmp % re.match(pat, alfile).groups()
        # print "Using "+repl+" to match "+alfile
        for trgfile in trgfiles:
          if re.match(repl, trgfile):
            # print "Matched to target "+trgfile+"!"
            trgfilematch= trgfile
            break # from trg file search
        if trgfilematch is None:
          break # from pattern search
        for srcfile in srcfiles:
          if re.match(repl, srcfile):
            # print "Matched to "+srcfile+"!"
            srcfilematch= srcfile
            break # from trg file search
        if srcfilematch is not None:
          break # from pattern search

    if srcfilematch is not None and trgfilematch is not None:
      # print "Matched "+alfile+" "+srcfilematch+" "+trgfilematch
      trgfiles.remove(trgfilematch)
      srcfiles.remove(srcfilematch)
      matches.append((os.path.join(srcdir, srcfilematch),
                      os.path.join(trgdir, trgfilematch),
                      os.path.join(aldir, alfile)))
    else:
      # print "No match for "+alfile
      unals.append(alfile)
  return (matches, srcfiles, trgfiles, unals)

def all_found_tuples(rootdir, src='uzb', trg='eng', xml=False):
  ''' traverse LRLP directory structure to build src, trg,
  align tuples of associated files '''
  matches = []
  tpath = os.path.join(rootdir, 'data', 'translation', 'found')
  pathext = "ltf" if xml else "rsd"
  fileext = "xml" if xml else "txt"

  src_path = os.path.join(tpath, src, pathext)
  trg_path = os.path.join(tpath, trg, pathext)
  al_path = os.path.join(tpath, 'sentence_alignment')
  (m, s, t, a) = pair_found_files(src_path, trg_path, al_path, ext=fileext)
  if len(s) > 0:
    sys.stderr.write("Warning: unmatched src files\n"+'\n'.join(s)+'\n')
  if len(t) > 0:
    sys.stderr.write("Warning: unmatched trg files\n"+'\n'.join(t)+'\n')
  if len(a) > 0:
    sys.stderr.write("Warning: unmatched align files\n"+'\n'.join(a)+'\n')
  return m

def selected_translation_pairs(path, src='uzb', trg='eng', xml=False):
  ''' Generalization of all_translation_pairs: build pairs of associated files
  from specified path '''
  pathext = "ltf" if xml else "rsd"
  fileext = "xml" if xml else "txt"
  (m, s, t) = pair_files(os.path.join(path, src, pathext),
                         os.path.join(path, trg, pathext), ext=fileext)
  if len(s) > 0:
    sys.stderr.write("Warning: unmatched src files\n"+'\n'.join(s)+'\n')
  if len(t) > 0:
    sys.stderr.write("Warning: unmatched trg files\n"+'\n'.join(t)+'\n')
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
    sys.stderr.write("Warning: unmatched src files\n"+'\n'.join(s)+'\n')
  if len(t) > 0:
    sys.stderr.write("Warning: unmatched trg files\n"+'\n'.join(t)+'\n')
  matches.extend(m)

  for domain in ('news', 'phrasebook', 'elicitation'):
    from_trg = os.path.join(tpath, "from_%s" % trg, domain)
    (m, s, t) = pair_files(os.path.join(from_trg, src, pathext),
                           os.path.join(from_trg, trg, pathext), ext=fileext)
    if len(s) > 0:
      sys.stderr.write("Warning: unmatched src files\n"+'\n'.join(s)+'\n')
    if len(t) > 0:
      sys.stderr.write("Warning: unmatched trg files\n"+'\n'.join(t)+'\n')
    matches.extend(m)
  return matches

def get_tokens(xml):
  ''' Get tokenized data from xml ltf file '''
  return [ ' '.join([ y.text for y in x.findall(".//TOKEN") ])+"\n" \
           for x in xml.findall(".//SEG") ]

def morph_tok(node):
  ''' Get morph and morph tok from node if present, otherwise fall back to text '''
  if node.get("morph") is None:
    yield "none", node.text
  elif node.get("morph") == "none" or node.get("morph") == "unanalyzable":
    yield node.get("morph"), node.text
  else:
    try:
      morph = node.get("morph").split(' ')
    except AttributeError:
      sys.stderr.write(ET.dump(node)+"\n")
      raise
    for morphtok in morph:
      try:
        yield morphtok.split('=')[1], morphtok.split(':')[0]
      except IndexError:
        yield morphtok, morphtok

def get_segments(xml):
  ''' Get segments from xml ltf file '''
  all_toktext = list()
  all_morphtoktext = list()
  all_morphtext = list()
  all_postext = list()
  try:
    for x in xml.findall(".//SEG"):
      tokens = x.findall(".//TOKEN")
      toktext = []
      morphtoktext = []
      morphtext = []
      postext = []
      for y in tokens:
        if y.text is None:
          continue
        toktext.append(y.text)
        postext.append(y.get("pos") or "none")
        for mt, mtt in morph_tok(y):
          morphtext.append(mt)
          morphtoktext.append(mtt)
      all_toktext.append(' '.join(toktext)+"\n")
      all_morphtoktext.append(' '.join(morphtoktext)+"\n")
      all_morphtext.append(' '.join(morphtext)+"\n")
      all_postext.append(' '.join(postext)+"\n")
  except TypeError:
    sys.stderr.write(x.get('id')+"\n")
    raise
  return all_toktext, all_morphtoktext, all_morphtext, all_postext

def get_info(node):
  ''' get offset info from xml node '''
  sdocid = node.findall(".//DOC")[0].get('id')
  return [ [sdocid,]+[ x.get(y) for y in ('id', 'start_char', 'end_char') ] for x in node.findall(".//SEG") ]


def extract_lines(s, t, xml=True):
  ''' given two files, open them and get data from them in various forms.
  Return as two lists of lists of strings. (If not xml, only a single form is possible) '''
  from itertools import chain
  # if xml, get codes, offsets, native, tokens, segments. If not, return codes and native only
  ret = []
  for x in (s, t):
    l = dd(list)
    if xml:
      try:
        root = ET.parse(x)
      except ParseError as detail:
        sys.stderr.write("Parse error on "+x+": "+str(detail)+"\n")
        return
      for (docid, segid, start, end) in get_info(root):
        l["DOCID"].append(docid)
        l["SEGID"].append(segid)
        l["START"].append(start)
        l["END"].append(end)
      toks, morphtoks, morphs, poss = get_segments(root)
      l["TOK"].extend(toks)
      l["MORPHTOK"].extend(morphtoks)
      l["MORPH"].extend(morphs)
      l["POS"].extend(poss)
      l["ORIG"].extend([ node.text+"\n" for node in root.findall(".//ORIGINAL_TEXT") ])
    else:
      import codecs
      with codecs.open(x, 'r', 'utf-8') as f:
        l["ORIG"] = f.readlines()
      l["DOCID"] = [x+"\n"]*len(l["ORIG"])
    lengths = [len(i) for i in l.values()]
    for length in lengths[1:]:
      if length != lengths[0]:
        sys.stderr.write("Length mismatch in "+x+": "+str(lengths))
        sys.exit(1)
    ret.append(l)
  # check that each side is internally consistentthe same length
  return ret


class Step:
  def __init__(self, prog, progpath=scriptdir, argstring="", stdin=None,
               stdout=None, stderr=None, help=None, call=check_call,
               abortOnFail=True, scriptbin=None):
    self.prog = prog
    self.scriptbin = scriptbin
    self.help = help
    self.progpath = progpath
    self.argstring = argstring
    self.stdin = stdin
    self.stdout = stdout
    self.stderr = stderr
    self.call = call
    self.abortOnFail = abortOnFail

  def run(self):
    kwargs = {}
    kwargs["shell"] = True
    if self.stdin is not None:
      kwargs["stdin"] = open(self.stdin)
    if self.stdout is not None:
      kwargs["stdout"] = open(self.stdout, 'w')
    if self.stderr is not None:
      kwargs["stderr"] = open(self.stderr, 'w')
    prog = os.path.join(self.progpath, self.prog)
    # TODO: could check that prog exists and is executable
    # TODO: fail or succeed based on return code and specified behavior
    retval = ""
    try:
      localstderr =  kwargs["stderr"] if self.stderr is not None else sys.stderr
      if self.scriptbin is None:
        callstring = "%s %s" % (prog, self.argstring)
      else:
        callstring = "%s %s %s" % (self.scriptbin, prog, self.argstring)
      basecallstring = callstring
      if self.stdin is not None:
        callstring = callstring+" < %s" % self.stdin
      if self.stdout is not None:
        callstring = callstring+" > %s" % self.stdout
      if self.stderr is not None:
        callstring = callstring+" 2> %s" % self.stderr

      localstderr.write("Calling %s\n" % callstring)
      retval = self.call(basecallstring, **kwargs)
      sys.stderr.write("%s: Done\n" % prog)
    except CalledProcessError as exc:
      sys.stderr.write("%s: FAIL: %d %s\n" % (prog, exc.returncode, exc.output))
      if self.abortOnFail:
        sys.exit(1)
    return retval

def make_action(steps):
  class customAction(argparse.Action):
    def __call__(self, parser, args, values, option_string=None):
      for stepnum, step in enumerate(steps):
        sys.stderr.write("%d: %s" % (stepnum, step.prog))
        if step.help is not None:
          sys.stderr.write(" = " + step.help)
        sys.stderr.write("\n")
      sys.exit(0)
  return customAction



def main():
  parser = argparse.ArgumentParser(description="Print parallel contents")
  parser.add_argument("--rootdir", "-r", help="root lrlp dir")
  parser.add_argument("--prefix", "-p", help="output files prefix")
  parser.add_argument("--src", "-s", default='uzb',
                      help="source language 3 letter code")
  parser.add_argument("--trg", "-t", default='eng',
                      help="target language 3 letter code")
  parser.add_argument("--xml", "-x", action='store_true',
                      help="process ltf xml files")
  # TODO: make this more general!
  parser.add_argument("--targetwhitelist", nargs='?',
                      type=argparse.FileType('r'), help="terms that must appear in kept data")
  parser.add_argument("--elseprefix",
                      help="prefix for files not matching the target list, if set")
  parser.add_argument("--tokenize", action='store_true',
                      help="use tokens (only applies if -x)")

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
  for s, t in all_translation_pairs(args.rootdir, src=args.src, trg=args.trg,
                                    xml=args.xml):
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
      sys.stderr.write("Warning: different number of lines in files" \
                       ":\n%s %d\n%s %d\n" % (s, slen, t, tlen))
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
