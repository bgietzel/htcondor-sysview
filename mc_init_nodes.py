#!/usr/bin/env python

# Init all nodes to online for initial install or after memcache restart

import memcache, sys
from vars import *
from sv_util import *
from mc_util import *

condor_nodes_cmd = './condor_nodes' 
p = os.popen(condor_nodes_cmd)
lines = p.readlines()
status = p.close()

if status:
    print condor_nodes_cmd, "returns", status

for line in lines:
    hostname, np = line.split()[:2]
    print "%s" % hostname
    mc_set( shortname(hostname)+".manualstatus", "online" )

