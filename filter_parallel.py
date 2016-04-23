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
import os
import glob
import numpy as np
from lputil import mkdir_p
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


def filterlines(ifh, seq, keepfh, rejectfh, low, high):
  ''' pair ifh and seq; if low < seq < high, then write to keepfh, else write to rejectfh '''
  for val, line in zip(seq, ifh):
    if val < low or val > high:
      rejectfh.write(line)
    else:
      keepfh.write(line)

def countfiles(dir):
  ''' how many (non-directory) files in this dir? '''
  ret = 0
  for _, _, files in os.walk(dir):
    ret += len(files)
  return ret

def main():
  parser = argparse.ArgumentParser(description="filter extracted parallel data directory",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--indir", "-i", default="./extracted", help="input directory")
  parser.add_argument("--lang", "-l", help="input directory")
  parser.add_argument("--stds", "-s", type=int, default=1, help="number of standard deviations from mean to filter out")
  parser.add_argument("--filterdir", "-f", default="./filtered", help="output filter directory")
  parser.add_argument("--genre", "-g", default="original", help="genre to use when filtering (could try tokenized but not available for twitter)")
  parser.add_argument("--remaindir", "-r", default="./remainder", help="output remainder directory")



  try:
    args = parser.parse_args()
  except IOError as msg:
    parser.error(str(msg))

  # crawl indir for expected original files. cat them together, save ratios, get mean and stdev
  # for each file, including manifest, zip with ratios, determine whether it belongs in filter or remaindir

  # TODO: add deltas too!
  
  indir = args.indir
  filterdir = args.filterdir
  remaindir = args.remaindir
  mkdir_p(filterdir)
  mkdir_p(remaindir)

  # assumption: there are a number of *.eng.manifest files, each paired with *.<lang>.manifest, and for each i, there is original/i.eng.flat and original/i.<lang>.flat
  engmanifests = glob.glob(os.path.join(indir, "*.eng.manifest"))
  fmanifests = []
  ratios = dd(list)
  genres = set()
  for eman in engmanifests:
    ebase = os.path.basename(eman)
    genre = '.'.join(ebase.split('.')[:-2])
    genres.add(genre)
    fman = os.path.join(os.path.dirname(eman), "%s.%s.manifest" % (genre, args.lang))
    fmanifests.append(fman)
    eorig = os.path.join(args.indir, args.genre, "%s.%s.eng.flat" % (genre, args.genre))
    forig = os.path.join(args.indir, args.genre, "%s.%s.%s.flat" % (genre, args.genre, args.lang))
    # test existence
    for f in [eman, fman, eorig, forig]:
      if not os.path.exists(f):
        sys.stderr.write("ERROR: %s does not exist\n" % f)
        sys.exit(1)
    #slurp files, calculate ratios, store ratios
    eorig = prepfile(open(eorig, 'r'), 'r')
    forig = prepfile(open(forig, 'r'), 'r')
    for ln, (eline, fline) in enumerate(izip(eorig, forig)):
      ewords = eline.strip().split()
      fwords = fline.strip().split()
      ratios[genre].append((len(ewords)+0.0)/(len(fwords)+0.0))
  allratios = np.concatenate(list(map(np.array, ratios.values())), 0)
  ratiomean = np.mean(allratios)
  ratiostd = np.std(allratios)
  lowratio = ratiomean-(args.stds*ratiostd)
  highratio = ratiomean+(args.stds*ratiostd)
  rejectsize = len(list(filter(lambda x: x<lowratio or x > highratio, allratios)))

  sys.stderr.write("Rejecting %d of %d lines (%f %%) with ratio below %f or above %f\n" % (rejectsize, len(allratios), 100.0*rejectsize/len(allratios), lowratio, highratio))

  # iterate through manifests and all files and filter per ratio
  for manset in (engmanifests, fmanifests):
    for man in manset:
      sys.stderr.write("filtering %s\n" % man)
      base = os.path.basename(man)
      genre = '.'.join(base.split('.')[:-2])
      sys.stderr.write("genre %s\n" % genre)
      rats = ratios[genre]
      rejectsize = len(list(filter(lambda x: x<lowratio or x > highratio, rats)))
      sys.stderr.write("rejecting %d of %d\n" % (rejectsize, len(rats)))
      infile = prepfile(open(man, 'r'), 'r')
      filterfile = prepfile(open(os.path.join(filterdir, base), 'w'), 'w')
      remainfile = prepfile(open(os.path.join(remaindir, base), 'w'), 'w')
      filterlines(infile, ratios[genre], filterfile, remainfile, lowratio, highratio)

  # for directories in extracted
  #http://stackoverflow.com/questions/973473/getting-a-list-of-all-subdirectories-in-the-current-directory
  for subdir in next(os.walk(indir))[1]:
    # make parallel directories
    # for genres in genre set
    # for languages
    # filter lines
    insubdir = os.path.join(indir, subdir)
    filtersubdir = os.path.join(filterdir, subdir)
    mkdir_p(filtersubdir)
    remainsubdir = os.path.join(remaindir, subdir)
    mkdir_p(remainsubdir)
    for genre in genres:
      for lang in (args.lang, 'eng'):
        base = "%s.%s.%s.flat" % (genre, subdir, lang)
        infilename = os.path.join(insubdir, base)
        if os.path.exists(infilename):
          infile = prepfile(open(infilename, 'r'), 'r')
          filterfile = prepfile(open(os.path.join(filtersubdir, base), 'w'), 'w')
          remainfile = prepfile(open(os.path.join(remainsubdir, base), 'w'), 'w')
          filterlines(infile, ratios[genre], filterfile, remainfile, lowratio, highratio)
        else:
          sys.stderr.write("%s does not exist\n" % infilename)

  # count files in each of the directories; should be the same
  for dir in (indir, filterdir, remaindir):
    sys.stderr.write("%d files in %s\n" % (countfiles(dir), dir))

if __name__ == '__main__':
  main()

