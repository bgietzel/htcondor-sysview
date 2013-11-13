#!/usr/bin/env python
#
# $Id: Exp $
#
# Loads information about nodes and jobs to memcache 

from vars import *
from sv_util import *
from condor_util import *
from mc_util import *
from icon_map import *
import sys, os, re, time, string
import memcache
from cStringIO import StringIO
import threading
import subprocess

mc = None
verbose = 0
debug = 0
print_times = False

for x in sys.argv:
    if x.startswith('-v'):
        verbose = x.count('v')
        print "verbose output enabled"
    if x.startswith('-d'):
        debug = x.count('d')
        print "debug output enabled"
    if x.startswith('-t'):
        print_times = True
        print "timing enabled"

print "CLUSTER_ID is %s " % CLUSTER_ID

if print_times:
        print time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.localtime())

# Poor man's lock
p=os.popen('ps ax|grep mosaic_backend_condor 2>/dev/null |grep python 2>/dev/null |grep -v grep 2>/dev/null |wc -l')
n = int(p.read())
if n > 1:
    print "another mosaic_backend_condor instance is running, exiting"
    sys.exit(1)
p.close()

main_timer = Timer("overall")

# set up job storage arrays for boinc
boinc_job_info = []
boinc_jobs = []
slurm_jobs = []

#### Run condor_nodes, get node info
nodes = []

timer = Timer('condor_nodes')
condor_nodes_cmd = './condor_nodes' 
if verbose: print condor_nodes_cmd
p = os.popen(condor_nodes_cmd)
lines = p.readlines()
status = p.close()
if status:
    print condor_nodes_cmd, "returns", status
for line in lines:
    hostname, np = line.split()[:2]
    n = Node()
    n.np = int(np)
    n.hostname = shortname(hostname)
    n.state = 'down' 
    n.pool = 'default'
    n.note = "" 
    nodes.append(n)
nodes_by_name = dict([(n.hostname, n) for n in nodes])

timer.end()

# pslots look like:
# slot1@e091
# slot1_1@e091
# slot1_2@e091

timer = Timer("condor_status")

num_boinc_jobs = 0
boinc_slot = 0

for pool_abbr, pool_name in pool_names.items():
  timer = Timer("condor_status")

  condor_status_cmd = "condor_status -long -pool %s" % (pool_name)  
  print condor_status_cmd
  p = os.popen(condor_status_cmd)
  lines = p.readlines()
  status = p.close()
  if status:
    print condor_status_cmd, "returns", status


  node = None
  nodestate = ''
  nodenote = ''
  loadavg = ''
  for line in lines:
    line = line.strip()
    if not line: # blank line denotes start of new node
        # Add node params to Node obj
        node = nodes_by_name.get(shortname(hostname))
        if node:
          setattr(node, 'state', nodestate)
          setattr(node, 'note', nodenote)
          setattr(node, 'pool', pool_abbr)
          setattr(node, 'LoadAvg', loadavg)
        else:
            print "Error: condor_status reports unknown node", hostname
 
        node = None
        hostname = ''
        nodestate = ''
        nodenote = ''
        loadavg = ''
        continue
    if not '=' in line:
        continue
    k, v = map(string.strip, line.split('=', 1))
    while v and v[0]=='"' and v[-1]=='"':
        v = v[1:-1] # strip quotes
    v = v.strip()
    try:
        v = float(v)
    except ValueError:
        try:
            v = int(v)
        except ValueError:
            pass

    if k == 'Machine':
        hostname = v

        if 'condor' in hostname: # condor_status reports on headnode, ignore it
            node = None
            continue
       
    elif k == 'NodeOnline' and v == 'true':
        nodestate = 'online'
    elif k == 'NodeOnline' and v == 'false':
        nodestate = 'offline'
    elif k == 'NodeOnlineReason':
        nodenote = v
    if  k == 'State' and v == 'Owner' and (pool_abbr == 'cs' or pool_abbr == 'cae'):
        nodestate = 'owner'

    # find the LoadAvg
    if ( k == 'TotalLoadAvg' ):
        loadavg = v

    # Now for pslots, rename the slots
    if k == 'Name':
      v = str(v)
      if ( v.find("slot1_") >= 0):
        v = ''.join(v.split('1_', 1))
      if ( v.find("slot3_") >= 0):
        v = ''.join(v.split('3_', 1))
      if ( v.find("slot5_") >= 0):
        v = ''.join(v.split('5_', 1))
      if debug: print 'SLOTNUMBER is %s' % v

      # boinc jobs get info from the execute machine not submitter
      if ( v.find("@") >= 0 ):
          try:
            vslot = v.split()[0].split('@')[0]
            if debug: print "vslot is %s " % vslot
          except KeyError, e:
            if verbose: print "slotid NOTFOUND"

      if ( vslot.find("slot1_") >= 0 or vslot.find("slot3_") >= 0 or vslot.find("slot5_") >= 0 ):
        boinc_slot = int(vslot[6:])
      elif ( vslot.find("slot") >= 0):
        boinc_slot = int(vslot[4:])
      else:
        boinc_slot = int(0)
      if debug: print 'boinc slot number is %d' % boinc_slot

    # now set for boinc
    if ( (k == 'RemoteOwner' and v.startswith("boinc") ) or (k == 'RemoteUser' and v.startswith("EinsteinAtHome") ) ):
      # create a fake job for boinc as these jobs show up on the execute side only, no submitter
      job = Job()
      job.user = "boinc"
      job.type="backfill"
      job.job_id = ".%d" %  (num_boinc_jobs)
      job.walltime = 1
      job.cputime = 1
      if debug: print "BOINC JOB ID %s" % job.job_id

      key = "%s.%d" % (shortname(hostname), boinc_slot)
      mc_set(key, job.job_id)
      boinc_jobs.append(job)
      num_boinc_jobs += 1

    # Default all slots to owner state, and slots with jobs will overwrite this
    if ( k == 'slot1_State' and v.startswith("Owner")  ):
      nodestate = 'owner'
      
  
  timer.end()

# SLURM
num_slurm_jobs = 0
slurm_status_cmd = '/usr/bin/sinfo -h -p pre -o "%n.chtc.wisc.edu %1t"'

proc = subprocess.Popen(["%s" % slurm_status_cmd], stdout=subprocess.PIPE, shell=True)
(out, err) = proc.communicate()

slurm_arr = []
slurm_arr = out.split('\n')

# if the host is running a slurm job, create a fake job for it.
for line in slurm_arr:
  if (" " in line):
    k, v = line.split(' ')

    if v.startswith('a'):
      job = Job()
      job.user = "slurm"
      job.type="slurm"
      job.walltime = 1
      job.cputime = 1
      if debug: print "SLURM JOB ID %s" % job.job_id

      n = nodes_by_name.get(shortname(k))
      setattr(n, 'state', 'online')

      # slurm jobs take the whole machine over, so insert a slurm job for each cpu
      nslots = n.np

      for slurm_cpu in xrange(nslots+1):
        job.job_id = "%d." %  (num_slurm_jobs)
 
        key = "%s.%d" % (shortname(k), slurm_cpu)
        mc_set(key, job.job_id)
        slurm_jobs.append(job)
        num_slurm_jobs += 1

print "NUM BOINC JOBS: %s " % num_boinc_jobs
print "NUM SLURM JOBS: %s " % num_slurm_jobs

# hosts are online by default
node_names = nodes_by_name.keys()
node_names.sort()

## Check if any nodes have been manually offlined
manualstatus=mc_get_multi([ shortname(h)+".manualstatus" for h in node_names ])
for n in nodes:
    try:
	ms=manualstatus[shortname(n.hostname)+".manualstatus"]
    except KeyError, e:
        continue
    if  manualstatus[shortname(n.hostname)+".manualstatus"] == 'offline':
        setattr(n, 'state', 'offline')
        setattr(n, 'note', mc_get(shortname(n.hostname)+".manualreason"))


timer = Timer("set node info")

mc_set(CLUSTER_ID+".nodes", node_names, 0)


for n in nodes:
    # info = (n.np, n.Activity.lower(), n.LoadAvg or 0, n.note)
    info = (n.np, n.state, n.LoadAvg or 0, n.pool, n.note)
  
    if debug: print "SHORT HOSTNAME is %s" % (shortname(n.hostname))
    mc_set(shortname(n.hostname)+".info", info)

timer.end()

#### Run condor_q, get job info
jobs = []
qjobs = []
for server_name in server_names.keys():
    pool_name = pool_names[server_names[server_name]]
    timer = Timer("condor_q %s" % server_name) 
    condor_q_cmd = "condor_q -long -name %s -pool %s" % (server_name, pool_name)
    print condor_q_cmd
    p = os.popen(condor_q_cmd)
    lines = p.readlines()
    status = p.close()
    if status:
        print condor_q_cmd, 'returns', status
    timer.end()
    if debug: print "%s" % lines

    timer = Timer("parse job info %s" % server_name)
    job = None
    job_info = []
    sjobs=[]

    for line in lines[3:]: # Skip over headers
        line = line.strip()

        if ( string.find( line, "GlobalJobId") > 0):
          if debug: print "JOBID is %s " % line
        if debug: 
          print "FOUND LINE in QUEUE"
          print "%s" % line
        if not line: # End of stanza
            if job:
                job.parse_job_info(job_info)
                job = None
                job_info = []
                if debug: print "EXISTING JOB"
        else:
            if not job: # Start of new stanza
                job = Job()
                sjobs.append(job)
                if debug: print "NEW JOB"
            job_info.append(line)
            if debug: 
              print "FOUND JOBINFO"
              print "%s" % line
    get_cputimes(sjobs, server_name, pool_name)
    get_walltimes(sjobs, server_name, pool_name)

    # set user, jobtype
    get_condor_users(sjobs, server_name, pool_name)
    get_condor_jobtypes(sjobs, server_name, pool_name)

    # dynamic slots
    get_slot_numbers(sjobs, server_name, pool_name)

    # whole machine slots
    for j in sjobs:
      if (j.RequiresWholeMachine == 'true'):
        hname = shortname(j.RemoteHost) 

        slot, h = map(string.strip, hname.split('@', 1))
        h = hname.split('@')[1]
        if debug: print "WHOLE MACHINE is %s" % h
        np, state, load, pool, msg = mc_get(h + '.info')

        cputime = j.cputime/np   
        for i in xrange(np+1):
          j.cputime = cputime 
          key = "%s.%d" % (h, i)
          mc_set(key, j.job_id)

    jobs+=sjobs

    timer.end()


#### Running jobs only
qjobs = [j for j in jobs if j.JobStatus == 1]
jobs = [j for j in jobs if j.JobStatus == 2]
jobs += boinc_jobs
jobs += slurm_jobs
job_ids = [j.job_id for j in jobs]
job_ids.sort(key=float)

mc_set(CLUSTER_ID+".running_jobs", job_ids)

#### Set $host.$slot keys in memcache
timer = Timer("set host slot keys")
multi = {}
try:
    multi["%s.all.createdjobs" % shortname(server_name)] = "%s" % job_ids[-1]
    multi["%s.all.exitedjobs" % shortname(server_name)] = "%s" % ( float(job_ids[-1]) - len(job_ids))
except IndexError, e:
    pass

jobs_by_node_slot = {}
for job in jobs:
    try:
        slot, hostname = map(string.strip, job.RemoteHost.split('@'))
    except:
        continue
    hostname = shortname(hostname)
    if debug: print 'hostname is %s' % hostname
    if debug: print 'slot name is %s' % slot
    if ( slot.find("slot1_") >= 0 or slot.find("slot3_") >= 0 or slot.find("slot5_") >= 0 ):
      slot = int(slot[6:])
    elif ( slot.find("slot") >= 0):
      slot = int(slot[4:])
    else:
      slot = 0
    if debug: print 'slot number is %s' % slot

    # now set this in mc
    key = "%s.%d" % (shortname(hostname), slot)
    mc_set(key, job.job_id)


key = "%s.%d" % (hostname, slot)
if debug: print "KEY is %s" % key
multi[key] = job.job_id
jobs_by_node_slot[(hostname, slot)] = job.job_id

mc_set_multi(multi)
timer.end()

# Set completed jobs with low TTL so they expire from memcachea
# TODO find correct TTL time and implement
timer = Timer("clear completed jobs")
for node in nodes:
    hostname = shortname(node.hostname)
    for slot in xrange(node.np+1):
        if (hostname, slot) not in jobs_by_node_slot:
            if debug: print "HS is %s %d " % (hostname, slot)
            key = "%s.%d" % (shortname(hostname), slot)
            #mc_set(key, job)
            #mc_set(key, job.job_id)
timer.end()


for job in jobs:
    u = job.user
    if not u:
        u = job.User
        if u:
            job.user = u

## Use "set_multi" method t access memcache (faster)
multi = {}

timer = Timer("create HTML")    
for job in jobs:
    job_id = job.job_id
    job.get_prev_times()
    fname = '%s.html' % job_id
    job_file = StringIO()
    job_file.write("<html><head><title>HTCondor job %s</title></head><body>\n" % job_id)
    user = job.user
    multi["%s.user"%job_id] = user
    _type = job.type

    job_file.write("<hr><pre>\n")

    if user:
        job_file.write("<b>User</b>: %s\n" % user)
    if _type:
        job_file.write("<b>Type</b>: %s\n" % _type)

    #### Reorder output to bring most relevant fields near top
    for i,line in enumerate(job.lines[:]):
        if line.startswith("GlobalJobId"):
            job_file.write("HTCondor Job Id: " + line.split('#')[1] + '\n')
            del job.lines[i]
            break
    job_file.write("<hr>\n")
    
    walltime = job.walltime
    cputime = job.cputime

    job_file.write("Walltime (from condor_q): %s\n" % sec_to_HMS(walltime))
    job_file.write("CPU time (from condor_q): %s\n" % sec_to_HMS(cputime))
    
    for field in ('RemoteWallClockTime',
                  'RemoteUserCpu', 'RemoteSysCpu',
                  'ResidentSetSize',
                  'x509UserProxyVOName',
                  'RemoteHost',
                  ):

        for i, line in enumerate(job.lines[:]):
            if line.startswith(field):
                job_file.write(line+'\n')
                del job.lines[i]
                break
            
    if job.prev_cpu or job.prev_walltime:
        job_file.write("<b>previous walltime for this pilot: %s</b>\n" % sec_to_HMS(job.prev_walltime))
        job_file.write("<b>previous CPU time for this pilot: %s</b>\n" % sec_to_HMS(job.prev_cpu))
        
    job_file.write("<hr>\n")

    for line in job.lines:
        job_file.write(line+'\n')
        
    job_file.write("</pre></body></html>")
    filedata = job_file.getvalue()
    multi[fname] = job_file.getvalue()
    job_file.close()

    # now write the html file
    o=open('jobinfo/' + fname, 'w')
    o.write(filedata)
    o.close()

    dot_type = ''
    user = job.user
    _type = job.type

    accounting_group=job.AccountingGroup
    queue = job.queue
    Owner = job.Owner
    Group = job.Group
    group = job.group
    dUser = job.User
 
    dot_type = find_dot_type(accounting_group, Owner, Group, group, dUser)

    multi["%s.type" % job_id] = dot_type
        
    wsecs = float(walltime)
    csecs = float(cputime)

    rss = job.ResidentSetSize or 0
    vm = job.ImageSize_RAW or 0
    rss = unitize(1024*rss)
    vm = unitize(1024*vm)
    multi["%s.mem" % job_id] = (rss, vm)
    multi["%s.times" % job_id] = (wsecs, csecs)
    multi["%s.host" % job_id] = job.RemoteHost

timer.end()


timer = Timer("set final keys")
mc_set_multi(multi)
mc_set("%s.time" % CLUSTER_ID, time.time())
timer.end()
main_timer.end()

sys.exit(0)
