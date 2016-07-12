#!/usr/bin/env python3
import argparse
import sys
import codecs
if sys.version_info[0] == 2:
  from itertools import izip
else:
  izip = zip
from collections import defaultdict as dd
import re
import os.path
import gzip
scriptdir = os.path.dirname(os.path.abspath(__file__))


reader = codecs.getreader('utf8')
writer = codecs.getwriter('utf8')


def prepfile(fh, code):
  ret = gzip.open(fh.name, code if code.endswith("t") else code+"t") if fh.name.endswith(".gz") else fh
  if sys.version_info[0] == 2:
    if code.startswith('r'):
      ret = reader(fh)
    elif code.startswith('w'):
      ret = writer(fh)
    else:
      sys.stderr.write("I didn't understand code "+code+"\n")
      sys.exit(1)
  return ret


urlre = re.compile(r"(https?://\S+)")

def spacify(input, flags=None):
  ''' make a regex that matches this string with any amount of whitespace added'''
  ret = []
  for char in input[:-1]:
    ret.append(char)
    ret.append(" *")
  ret.append(input[-1])
  return re.compile(''.join(ret), flags=flags)

def scrub(matchtext, targetline, minsize=3):
  ''' remove scattered pieces of matchtext '''
  if matchtext in targetline:
    return targetline.replace(matchtext, "", 1)
  elif len(matchtext) > 2*minsize:
    for i in range(len(matchtext)-minsize, minsize, -1):
      if matchtext[:i] in targetline:
        targetline = scrub(matchtext[:i], targetline, minsize=minsize)
        return scrub(matchtext[i:], targetline, minsize=minsize)
  return targetline

def main():
  parser = argparse.ArgumentParser(description="Repair broken urls in translations based on source preservation",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--sourcefile", "-s", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="input source file")
  parser.add_argument("--targetfile", "-t", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="input target file")
  parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('w'), default=sys.stdout, help="output (fixed target) file")



  try:
    args = parser.parse_args()
  except IOError as msg:
    parser.error(str(msg))

  sourcefile = prepfile(args.sourcefile, 'r')
  targetfile = prepfile(args.targetfile, 'r')
  outfile = prepfile(args.outfile, 'w')


  linecount=0
  urlcount=0
  urlmatch=0
  casematch=0
  wsmatch=0
  wscasematch=0
  piece=0
  miss=0
  for sourceline, targetline in izip(sourcefile, targetfile):
    linecount+=1
    for match in urlre.finditer(sourceline):
      urlcount+=1
      matchtext = match.group()
      if matchtext in targetline:
        urlmatch+=1
        continue
      elif re.search(matchtext, targetline, flags=re.I) is not None:
        casematch+=1
        tgtmatch = re.search(matchtext, targetline, flags=re.I)
        targetline = targetline.replace(tgtmatch.group(), matchtext, 1)
        continue
      elif matchtext in targetline.replace(" ", ""):
        wsmatch+=1
        tgtmatch = spacify(matchtext).search(targetline)
        targetline = targetline.replace(tgtmatch.group(), matchtext, 1)
        continue
      elif re.search(matchtext, targetline.replace(" ", ""), flags=re.I) is not None:
        wscasematch+=1
        tgtmatch = spacify(matchtext, flags=re.I).search(targetline)
        targetline = targetline.replace(tgtmatch.group(), matchtext, 1)
        continue
      else:
        miss+=1
        # TODO: scrub and replace
        otl = targetline
        targetline = scrub(matchtext, targetline)
        # if otl != targetline:
        #   print("old: "+otl)
        #   print("new: "+targetline)
        if match.start() < len(sourceline)-match.start():
          targetline = matchtext+" "+targetline
        else:
          targetline = targetline.strip()+" "+matchtext+"\n"
        #print("URL MISS:"+sourceline+targetline)
    outfile.write(targetline)
  print("{} lines {} urls {} matched {} casematched {} wsmatched {} wscasematched {} missed".format(linecount, urlcount, urlmatch, casematch, wsmatch, wscasematch, miss))

if __name__ == '__main__':
  main()

