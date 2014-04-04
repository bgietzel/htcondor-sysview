#!/usr/bin/env python
#
# $Id: util.py Exp $
#
# Util functions for memcache

import memcache, sys, string


usage = '1) mc_util.py get <key> \n2) mc_util.py set <key> <val> \n3) mc_util.py set <key> <val> <ttl>'

# memcache server
MC_HOSTLIST=['localhost:11211']

# 120 min timeout for memcache 
TTL = 120 * 60


mc = None
verbose = 0

# replace dots with underscores for memcache.  shortname is not really correct. change this.            
def shortname(hostname):
    return hostname.replace(".","_")
#    return hostname.split('.')[0]

def longname(hostname):
    return hostname.replace("_",".")

def mc_init():
    global mc
    if not mc:
        mc = memcache.Client(MC_HOSTLIST)
        
def mc_get(key):
    mc_init()
    try:
        r = mc.get(key)
    except:
        r = None
    if verbose:
        print "GET", key, r
    return r

def mc_set(key, val, ttl=TTL):
    mc_init()
    try:
        mc.set(key, val, ttl)
    except:
        pass
    if verbose:
        print "SET", key, val

def mc_get_multi(k):
    mc_init()
    try:
        d = mc.get_multi(k)
    except exception, e:
        if verbose > 1:
           print e
        pass
    if verbose:
        print "GET multi", d
    return d

def mc_set_multi(d, ttl=TTL):
    mc_init()
    try:
        mc.set_multi(d, ttl)
    except:
        pass
    if verbose:
        print "SET multi", d


# interactive use
if ( len(sys.argv) > 2 ):
  op = sys.argv[1]
  k = sys.argv[2]
  if op == 'get' :
    print mc_get(k)
  elif op == 'set' :
    v = sys.argv[3]
    if ( len(sys.argv) == 5 ):
      t = sys.argv[4]
      mc_set(k, v, t)
    else:
      mc_set(k, v)
  else:
    print usage

