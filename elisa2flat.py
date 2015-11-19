#! /usr/bin/env python
import argparse
import sys
import codecs
from itertools import izip
from lxml import etree as ET
#from xml.etree import ElementTree as ET
from collections import defaultdict as dd
import re
import os.path
import gzip
scriptdir = os.path.dirname(os.path.abspath(__file__))

# this code is used below but not in this form
#http://stackoverflow.com/questions/7171140/using-python-iterparse-for-large-xml-files
# def fast_iter(context, func, *args, **kwargs):
#   """
#   http://lxml.de/parsing.html#modifying-the-tree
#   Based on Liza Daly's fast_iter
#   http://www.ibm.com/developerworks/xml/library/x-hiperfparse/
#   See also http://effbot.org/zone/element-iterparse.htm
#   """
#   for event, elem in context:
#     func(elem, *args, **kwargs)
#     # It's safe to call clear() here because no descendants will be
#     # accessed
#     elem.clear()
#     # Also eliminate now-empty references from the root node to elem
#     for ancestor in elem.xpath('ancestor-or-self::*'):
#       while ancestor.getprevious() is not None:
#         del ancestor.getparent()[0]
#   del context


# def process_element(elem):
#   print elem.xpath( 'description/text( )' )

# context = etree.iterparse( MYFILE, tag='item' )
# fast_iter(context,process_element)

def main():
  parser = argparse.ArgumentParser(description="Given a compressed elisa xml file and list of attributes, print them out, tab separated",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--infile", "-i", nargs='?', type=argparse.FileType('rb'), default=sys.stdin, help="input file")
  parser.add_argument("--fields", "-f", nargs='+', help="list of fields to extract text from. if attribute is desired, use field.attribute. Separate fallback fields with :")
  parser.add_argument("--segment", "-s", default="PARALLEL", help="segment name. PARALLEL for x-eng, SEGMENT for monolingual. More than one match per segment will be concatenated")
  parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('w'), default=sys.stdout, help="output file")



  try:
    args = parser.parse_args()
  except IOError, msg:
    parser.error(str(msg))

  reader = codecs.getreader('utf8')
  writer = codecs.getwriter('utf8')
  infile = args.infile
  infile = gzip.open(infile.name, 'r') if infile.name.endswith(".gz") else infile
  #infile = reader(infile)
  outfile = gzip.open(args.outfile.name, 'w') if args.outfile.name.endswith(".gz") else args.outfile
  outfile = writer(outfile)

  ctxt = ET.iterparse(infile, events=("end", "start"))
  # don't delete when in the middle of an element you want to investigate
  lock = False
  for event, element in ctxt:
    if event == "start" and element.tag == args.segment:
      lock = True
    if event == "end" and element.tag == args.segment:
      outfields = []
      for fieldopts in args.fields:
        wrotesomething = False
        fieldopts = fieldopts.split(":")
        while len(fieldopts) > 0:
          field = fieldopts.pop(0)
          subfields = field.split(".")
          matches = [element,] if subfields[0] == args.segment else element.findall(".//"+subfields[0])
          for match in matches:
            value = match.get(subfields[1]) if len(subfields) > 1 else match.text
            value = value.replace('\n', ' ')
            value = value.replace('\t', ' ')
            if value is not None:
              outfields.append(value)
              wrotesomething = True
          del matches
          if wrotesomething:
            break
        if not wrotesomething:
          outfields.append("")
      outfile.write("\t".join(outfields)+"\n")
      lock = False
    # recover memory
    if event == "end" and not lock:
      element.clear()      
      for ancestor in element.xpath('ancestor-or-self::*'):
        while ancestor.getprevious() is not None and ancestor.getparent() is not None and ancestor.getparent()[0] is not None:
            del ancestor.getparent()[0]
  del ctxt


if __name__ == '__main__':
  main()

