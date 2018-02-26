#!/usr/bin/env python

import argparse
import os
import errno
import shlex
from subprocess import check_call, Popen, PIPE

# general purpose utility functions

# http://stackoverflow.com/questions/600268/mkdir-p-functionality-in-python
import os, errno
def mkdir_p(path):
  try:
    os.makedirs(path)
  except OSError as exc: # Python >2.5
    if exc.errno == errno.EEXIST and os.path.isdir(path):
      pass
    else: raise

    
# custom action to create new directory if default isn't used
# http://stackoverflow.com/questions/11415570/directory-path-types-with-argparse

class make_passed_dir(argparse.Action):
    def __call__(self,parser, namespace, values, option_string=None):
        prospective_dir=values
        if not os.path.isdir(prospective_dir):
            os.makedirs(prospective_dir)
        if os.access(prospective_dir, os.W_OK):
            setattr(namespace,self.dest,prospective_dir)
        else:
            raise argparse.ArgumentTypeError("writeable_dir:{0} is not a writeable dir".format(prospective_dir))


# get mean, std, min, max of a vector of numbers (use with getstats script for oneliners)
def get_stats(vec):
    import numpy
    retvec = (numpy.mean(vec), numpy.std(vec), min(vec), max(vec))
    print("mean: %f stdev: %f range: %f-%f" % retvec)
    return retvec

def isFloat(string):
    try:
        float(string)
        return True
    except ValueError:
        return False

def isInt(string):
    try:
        int(string)
        return True
    except ValueError:
        return False

def list_to_dict(l, tuple_size=2, key=0, val=1):
    ''' given a list of items, form a dict out of it '''
    # http://stackoverflow.com/questions/4576115/python-list-to-dictionary
    return dict(zip(l[key::tuple_size], l[val::tuple_size]))

def ngram(data, n, sep=' ', pref='START'):
    ''' given a list of tokens, return a list of n-grams by joining with sep, prepending with pref '''
    ret = []
    # prefix spans
    for i in range(1, min(n, len(data)+1)):
        ret.append(sep.join([pref]*(n-i)+data[0:i]))
    # regular spans
    for i in range(max(len(data)-n+1, 0)):
        ret.append(sep.join(data[i:i+n]))
    return ret

def shchain(cmds, input=None, output=None):
    ''' make and execute a Popen/check_call chain '''

    # single element corner case
    if len(cmds) == 1:
        startargs={}
        if input is not None:
            startargs['stdin']=input
        if output is not None:
            startargs['stdout'] = output
        check_call(shlex.split(cmds[0]), **startargs)
        return
    # normal cases
    startargs={'stdout':PIPE}
    if input is not None:
        startargs['stdin']=input
    lastcmd = Popen(shlex.split(cmds[0]), **startargs)
    for cmd in cmds[1:-1]:
        lastcmd = Popen(shlex.split(cmd), stdin=lastcmd.stdout, stdout=PIPE)
    endargs = {'stdin':lastcmd.stdout}
    if output is not None:
        endargs['stdout'] = output
    lastcmd = check_call(shlex.split(cmds[-1]), **endargs)
