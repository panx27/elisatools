#! /usr/bin/env python
import argparse
import sys
import codecs
from itertools import izip
from collections import defaultdict as dd
import lxml.etree as ET
import re
import os.path
import os
from lputil import mkdir_p
scriptdir = os.path.dirname(os.path.abspath(__file__))


def find(name, paths):
  for path in paths:
    for root, dirs, files in os.walk(path):
      if name in files:
        return os.path.join(root, name)

def main():
  parser = argparse.ArgumentParser(description="Given a reflex lrlp laf with token ids and a ltf with token-to-start_char/end_char, create an laf with start_char/end_char. Operate per directory",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--indir", "-i", help="input directory. Presumed to contain x.laf.xml. Might contain x.ltf.xml for all x")
  parser.add_argument("--corpusdirs", "-c", nargs='+', help="directory tree or trees to find x.ltf.xml")
  parser.add_argument("--outdir", "-o", help="output directory. may not exist. will contain modified x.laf.xml for all x")


  try:
    args = parser.parse_args()
  except IOError, msg:
    parser.error(str(msg))

  reader = codecs.getreader('utf8')
  writer = codecs.getwriter('utf8')

  stderr = writer(sys.stderr)
  indir = args.indir
  outdir = args.outdir
  mkdir_p(outdir)

  localcount = 0
  remotecount = 0
  bothcount = 0
  for inlaf in filter(lambda x: x.endswith(".laf.xml"), os.listdir(indir)):
    base = inlaf.replace(".laf.xml", "")
    outlaf = os.path.join(outdir, inlaf)
    inlaf = os.path.join(indir, inlaf)
    inltf = os.path.join(indir, base+".ltf.xml")
    corpusltf = find(base+".ltf.xml", args.corpusdirs) if args.corpusdirs is not None else None
    # cases:
    # 1. local ltf exists with char offsets. no remote ltf. we use what local ltf gives us
    # 2. local and remote ltf exist, with the same number of tokens in the same order. we map local id to remote id and use those offsets
    # 3. remote ltf exists. local does not. We use remote ltf as in case 1
    # 4. local and remote exist with different numbers of tokens or nothing exists or something else. complain and skip this document

    try:
      # case 2: build id map
      idmap = {}
      useidmap = False
      if os.path.exists(inltf) and corpusltf is not None and os.path.exists(corpusltf):
        localroot = ET.parse(inltf)
        corpusroot = ET.parse(corpusltf)
        localtoks = localroot.findall(".//TOKEN")
        corpustoks = corpusroot.findall(".//TOKEN")
        if len(localtoks) != len(corpustoks):
          stderr.write("Token count mismatch; skipping "+inlaf+"\n")
          continue
        ok = True
        for localtok, corpustok in zip(localtoks, corpustoks):
          if localtok.text != corpustok.text:
            stderr.write("Token count mismatch; skipping "+inlaf+"\n")
            ok = False
            break
          idmap[localtok.get("id")]=corpustok.get("id")
        if not ok:
          continue
        useidmap = True

      # case 1: swap inltf and corpusltf (otherwise below handles case 2, 3)
      if os.path.exists(inltf) and ( corpusltf is None or not os.path.exists(corpusltf)):
        inltf, corpusltf = corpusltf, inltf
        remotecount+=1
      elif useidmap:
        bothcount+=1
      else:
        localcount+=1

      # Final token id-to-offset
      starts = {}
      ends = {}

      root = ET.parse(corpusltf)
      for node in root.findall(".//TOKEN"):
        id = node.get("id")
        starts[id]=node.get("start_char")
        ends[id]=node.get("end_char")
      #root.clear()
      # re-map
      root = ET.parse(inlaf)
      for node in root.findall(".//ANNOTATION"):
        stok = node.get("start_token")
        etok = node.get("end_token")
        stok = idmap[stok] if useidmap else stok
        etok = idmap[etok] if useidmap else etok
        start = starts[stok]
        end = ends[etok]
        ext = node.find(".//EXTENT")
        ext.set('start_char', start)
        ext.set('end_char', end)
      xmlstr = ET.tostring(root, pretty_print=True, encoding='unicode')
      writer(open(outlaf, 'w')).write(xmlstr+"\n")
    except:
      e = sys.exc_info()[0]
      stderr.write("Problem with %s: %s\n" % (inltf, e))
      continue
  stderr.write("%d using local only, %d using remote only, %d using both\n" % (localcount, remotecount, bothcount))
    
if __name__ == '__main__':
  main()

