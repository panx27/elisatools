#! /usr/bin/env python

import sys
import pickle
import gzip
import re
import os
import json

langid = sys.argv[1]
thisdir = os.path.abspath(os.path.dirname(__file__))
punkt_dir = os.path.join(thisdir, '../../../punkt/models')
t = pickle.load(gzip.open(punkt_dir + '/%s.pickle.gz' % langid, 'r'))

line = sys.stdin.readline()
while line:
    text = json.loads(line)
    sents = []
    for sent in t.tokenize(text):
        s = re.sub(r'\s+', ' ', sent).strip()
        sents.append(s)
    sys.stdout.write(json.dumps(sents))
    sys.stdout.write("\n")
    try:
        sys.stdout.flush()
    except IOError:
        pass
    line = sys.stdin.readline()

