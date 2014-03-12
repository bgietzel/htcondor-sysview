#!/usr/bin/env python
#
# Remove old html files from disk

from vars import *
from sv_util import *
from mc_util import *
import sys, os, re, string
import memcache

mc = None
verbose = 0
debug = 0

for x in sys.argv:
    if x.startswith('-v'):
        verbose = x.count('v')
        print "verbose output enabled"
    if x.startswith('-d'):
        debug = x.count('d')
        print "debug output enabled"

print "CLUSTER_ID is %s " % CLUSTER_ID

nodes = []
jobs = []
keys = []
job_html_files = [] 

for CLUSTER_ID in CLUSTER_IDS:
    nodes_tmp = mc_get(CLUSTER_ID+'.nodes')
    nodes.extend(nodes_tmp)
    jobs.extend(mc_get(CLUSTER_ID+'.running_jobs'))
del nodes_tmp

for node in nodes:
    if debug: print "NODE is %s " % node
    keys.append(shortname(node)+".info")
node_info = mc_get_multi(keys)

for node in nodes:
    hostname = shortname(node)
    if debug: print "HOSTNAME is %s " % hostname
    ncpu, state, load, pool, msg = node_info.get(hostname + '.info')

    for slot in xrange(1, ncpu+1):

      job = mc_get("%s.%d" % (hostname, slot))

      if job:
          if verbose: print "HAVE JOB %s" % job

          job_html = '%s.html' % job
          job_html_files.append(job_html)

job_html_files.sort()

# if we don't find the job as active, remove the html file
for f in os.listdir('%s/jobinfo' % WEBDIR ):
  if ( filter(lambda x: f in x, job_html_files)):
    next
  else:
    job_html_path = '%s/jobinfo/%s' % (WEBDIR, f)
    print "FILE TO REMOVE IS %s" % job_html_path
    os.remove(job_html_path) 
