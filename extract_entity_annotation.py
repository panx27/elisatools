#! /usr/bin/env python
# utilities for dealing with LRLPs
import argparse
import codecs
import sys
import os
import re
import os.path
from zipfile import ZipFile as zf
import xml.etree.ElementTree as ET
import gzip
import os
scriptdir = os.path.dirname(os.path.abspath(__file__))
import datetime
from lputil import funornone

# TODO:
# handle noun phrase chunking

#http://stackoverflow.com/questions/2865278/in-python-how-to-find-all-the-files-under-a-directory-including-the-files-in-s
def recursive_file_gen(mydir):
    for root, dirs, files in os.walk(mydir):
        for file in files:
            yield os.path.join(root, file)

def main():
  import codecs
  parser = argparse.ArgumentParser(description="Extract and print laf annotation data from LRLP in a form that is amenable to insertion into future xml",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--rootdir", "-r", default=".", help="root lrlp dir")
  parser.add_argument("--outfile", "-o", type=argparse.FileType('w'), default=sys.stdout, help="where to write extracted semantic info")

  try:
    args = parser.parse_args()
  except IOError, msg:
    parser.error(str(msg))

  writer = codecs.getwriter('utf8')
  outfile = writer(args.outfile)

  anndir = os.path.join(args.rootdir, 'data', 'annotation')
  if not os.path.exists(anndir):
    sys.stderr.write("No annotation directory found")
    sys.exit(0)
  print anndir
  for annfile in recursive_file_gen(anndir):
    if annfile.endswith("laf.xml") and not os.path.basename(annfile).startswith("."):
      try:  
        xobj = ET.parse(annfile)
      except:
        sys.stderr.write("Problem parsing "+annfile+"\n")
        continue
      for xdoc in xobj.findall("DOC"):
        docid = xdoc.get("id")
        # store all annotations by id. if they have an extent, spit them out.
        # if no extent, check they are entities; nothing else should be extent-free
        # PREDICATE, ENTITY, and PHRASE are cross references to ids; for ENTITY the 
        # core type is copied, for everything else just the cross reference
        annset = {}
        for xann in xdoc.findall("ANNOTATION"):
          annid = xann.get("id")
          annset[annid] = xann
          anntask = xann.get("task")
          if xann.find("EXTENT") is None:
            if anntask != "FE":
              sys.stderr.write("Warning: extent-free non-full annotation in "+annfile+": "+ET.tostring(xann)+"\n")
              continue
            continue
          xextent = xann.find("EXTENT")
          tup = [anntask, docid, xextent.get("start_char"), xextent.get("end_char"), annid, xextent.text]
          if anntask == "NE": # simple ne annotation
            tup.append(xann.get("type"))
          else: # everything else has category/tag style
            try:
              tup.append(funornone(xann.find("CATEGORY"), lambda x: x.text))
              tup.append(funornone(xann.find("TAG"), lambda x: x.text))
              if (anntask == "FE"):
                if xann.find("ENTITY") is not None:
                  eid = xann.find("ENTITY").get("entity_id")
                  tup.append(eid)
                  tup.append(annset[eid].find("TAG").text if annset[eid].find("TAG") is not None else "NONE")
                elif xann.find("PHRASE") is not None:
                  tup.append(xann.find("PHRASE").get("phrase_id"))
                else:
                  sys.stderr("Expected ENTITY or PHRASE at "+annfile+"; "+ET.tostring(xann))
                  continue
              elif (anntask == "SSA"):
                if xann.find("PREDICATE") is not None:
                  tup.append(xann.find("PREDICATE").get("predicate_id"))
              else:
                sys.stderr.write(annfile+": Don't know how to process "+anntask+"\n")
                continue
            except:
              print annfile
              print ET.tostring(xann)
              raise
          outfile.write("\t".join(tup)+"\n")


if __name__ == '__main__':
  main()

