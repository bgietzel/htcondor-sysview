#!/usr/bin/env python

# Init all nodes to online for initial install or after memcache restart

import memcache, sys
from vars import *
from mc_util import *

usage = '1) mc_init_nodes.py online all\n2) mc_init_nodes.py online <node>\n3) mc_init_nodes.py offline <node> <offlinereason>'


def onlineAll():
  condor_nodes_cmd = './condor_nodes' 
  p = os.popen(condor_nodes_cmd)
  lines = p.readlines()
  status = p.close()

  if status:
    print condor_nodes_cmd, "returns", status

  for line in lines:
    hostname, np = line.split()[:2]
    print "%s" % hostname
    mc_set( n+".manualstatus", "online", 0 )

def onlineNode(n):
    mc_set( n+".manualstatus", "online", 0 )
    mc_set( n+".manualreason", "", 1 )

def offlineNode(n,r): 
    print "Setting node %s to offline status: %s" % (n,r)
    mc_set( n+".manualstatus", "offline", "0" )
    mc_set( n+".manualreason", r, 0 )


# process the arguments
if len(sys.argv) > 2: 
  status = sys.argv[1]
  node = sys.argv[2]
  if status == 'online':
    if node == 'all':
      onlineAll()
    else:
      onlineNode(shortname(node))
  elif status == 'offline' and len(sys.argv) > 3:
    reason = sys.argv[3]
    offlineNode(shortname(node), reason)
else:
  print usage
