#!/usr/bin/env python3

# extract lexicon file
import argparse
import sys
import os
import re
import os.path
import xml.etree.ElementTree as ET
import os
import datetime
import shutil

class SkipEntry(Exception):
  pass

def main():
  import codecs
  parser = argparse.ArgumentParser(description="Extract lexicon file from xml")
  parser.add_argument("--infiles", "-i", nargs='+', type=argparse.FileType('r'),
                      help="input lexicon files")
  parser.add_argument("--outfile", "-o", help="output file")
  parser.add_argument("--version", "-v", choices=["1.4", "1.5", "il3"], default="1.4", help="dtd version")
  

  try:
    args = parser.parse_args()
  except IOError as msg:
    parser.error(str(msg))

  outdir = os.path.dirname(args.outfile)
  if not os.path.exists(outdir):
    os.makedirs(outdir)
  outfile=args.outfile

  if args.version == "1.4":
    wordlabel="WORD"
    glosslabel="GLOSS"
    dopos = True
  elif args.version == "1.5":
    wordlabel="LEMMA"
    glosslabel="GLOSS"
    dopos = True
  elif args.version == "il3":
    wordlabel="WORD"
    glosslabel="DEFINITION"
    dopos = False
  else:
    pass
  
  # for printing out at the end
  stats = 0

  of = codecs.open(outfile, 'w', 'utf-8')
  source_fh = open(os.path.join(outdir, "source"), 'a')
  for infile in args.infiles:
    xobj = ET.parse(infile)
    try:
      for entry in xobj.findall(".//ENTRY"):
        # POS hacked out and GLOSS->DEFINITION for IL
        words = entry.findall(".//%s" % wordlabel)
        poses = [x.text for x in entry.findall(".//POS")] if dopos else ["UNK",]
        glosses = entry.findall(".//%s" % glosslabel)
        if len(poses) != len(glosses):
          if len(poses) == 1:
            poses = [poses[0]]*len(glosses)
          else:
            raise SkipEntry(ET.dump(entry))
        for word in words:
          for pos, gloss in zip(poses, glosses):
            if gloss.text is None or word.text is None or pos is None:
              continue
            stats+=1
            of.write("%s\t%s\t%s\n" % (word.text.strip(),
                                       pos.strip(),
                                       gloss.text.strip()))
    except SkipEntry as e:
      raise


    source_fh.write("Extracted lexicon from %s to %s on %s\nusing %s; command" \
                    " issued from %s\n" % (infile.name, outfile,
                                           datetime.datetime.now(),
                                           ' '.join(sys.argv), os.getcwd()))

  # copy all files from lexicon directory to processed directory
  lexicon_dirs = set([os.path.dirname(x.name) for x in args.infiles])
  sys.stderr.write("Extracted %d entries\n" % (stats))
  for lexicon_dir in lexicon_dirs:
    for i in os.listdir(lexicon_dir):
      name = os.path.join(lexicon_dir, i)
      outname = '%s_%s' % (outfile, i)
      shutil.copy(name, outname)
      source_fh.write("Extracted extra lexicon from %s to %s\n" % (name, outname))

if __name__ == '__main__':
  main()
