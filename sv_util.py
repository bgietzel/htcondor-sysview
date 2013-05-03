#!/usr/bin/env python
#
# $Id: sv_util.py Exp $
#
# Util functions for sysview


import time, string

verbose = 0
print_times = False

class Timer:
    def __init__(self, name):
        self.name = name
        self.t0 = time.time()
    def __str__(self):
        return "%s %.2gs" % (self.name, time.time() - self.t0)
    def end(self):
        if print_times:
            print self


def HMS(x):
    x = int(x)
    s, x = x%60, int(x/60)
    m, x = x%60, int(x/60)
    return "%02d:%02d:%02d" % (x,m,s)

def strip_chars(x):
    valid_chars = "-_.%s%s" % (string.ascii_letters, string.digits)
    if x is None:
        x = "None"
    return ''.join(c for c in x if c in valid_chars)

def sec_to_HMS(x):
    x = int(x)
    s, x = x%60, int(x/60)
    m, x = x%60, int(x/60)
    return "%02d:%02d:%02d" % (x,m,s)

def HMS_to_sec(t):
    days = 0
    if '+' in t:
        days, t = t.split('+')
        days = int(days)
    r = 0
    tok = t.split(':')
    for x in tok:
        try:
            r = 60*r + int(x)
        except ValueError:
            return 0
    return days*86400 + r

def unitize(x,base=1024):
    suff='BKMGTPEZY'
    while x >= base and suff:
        x /= float(base)
        suff = suff[1:]
    return "%.1f%s" % (x, suff[0])

def parse_timestamp(ts):
    try:
        r = int(ts)
    except ValueError:
        r = time.mktime(time.strptime(ts.strip()))
    return r

