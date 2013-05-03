#!/usr/bin/env python
#
# $Id: util.py Exp $
#
# Util functions for htcondor

from vars import *
from sv_util import *
from mc_util import *

import  os, re, string


class Node:
    # Return empty string for any unset attributes
    def __getattr__(self, attr): 
        return self.__dict__.get(attr, '')
    # allow check of "if node"
    def __nonzero__(self):
        return True


class Job:
    # Return empty string for any unset attributes
    def __getattr__(self, attr): 
        return self.__dict__.get(attr, '')
    # Allow checks of "if job"
    def __nonzero__(self):
        return True
    def parse_job_info(self, lines):
        self.lines = lines
        for line in lines:
            line = line.strip()
            if not line:
                continue
            k, v = line.split('=', 1)
            k = k.replace('.', '_') # Can't have '.' in attr name
            k = k.strip()
            v = v.strip()
            # Strip extra quotes
            while v and v[0] == '"' and v[-1] == '"':
                v = v[1:-1]
            try:
                v = int(v)
            except ValueError:
                try:
                    v = float(v)
                except ValueError:
                    pass
            setattr(self, k, v)
        job_id = getattr(self,"GlobalJobId", None)
        self.job_id = None
        if job_id:
            try:
                self.job_id = job_id.split('#')[1]

            except:
                print "Cannot parse job id", job_id
            
    def get_prev_times(self):
        result = mc_get("%s.prev_times" % self.job_id)
        if result:
            self.prev_walltime, self.prev_cpu = result
            if not self.prev_walltime:
                self.prev_walltime = 0
            if not self.prev_cpu:
                self.prev_cpu = 0
        else:
            self.prev_walltime = self.prev_cpu = 0


def get_walltimes(jobs, server_name, pool_name, verbose=0):
    cmd = 'condor_q -name %s -pool %s -constraint "JobStatus==2"' % (server_name, pool_name)
    p = os.popen(cmd)
    lines = p.readlines()
    status = p.close()
    if status:
        if verbose:
            print status, lines
        return 0
    dict_walltimes = dict( [(line.split()[0],  HMS_to_sec(line.split()[4])) for line in lines if 'R' in line])
    for j in jobs:
        try:
            setattr(j, 'walltime', dict_walltimes[j.job_id])
        except KeyError, e:
            setattr(j, 'walltime', 0)


def get_cputimes(jobs, server_name, pool_name, verbose=0):
    cmd = 'condor_q -cputime -name %s -pool %s -constraint "JobStatus==2"' % (server_name, pool_name)
    p = os.popen(cmd)
    lines = p.readlines()
    status = p.close()
    if status:
        if verbose:
            print status, lines
        return 0
    dict_cputimes = dict( [ (line.split()[0],  HMS_to_sec(line.split()[4])) for line in lines if 'R' in line])
    for j in jobs:
        try:
            setattr(j, 'cputime', dict_cputimes[j.job_id])
        except KeyError, e:
            setattr(j, 'cputime', 0 )

def get_condor_users(jobs, server_name, pool_name, verbose=0):
    cmd = 'condor_q -name %s -pool %s -constraint "JobStatus==2"' % (server_name, pool_name)
    p = os.popen(cmd)
    lines = p.readlines()
    status = p.close()
    if status:
        if verbose:
            print status, lines
        return 0
    dict_condor_users = dict( [ (line.split()[0],  str(line.split()[1])) for line in lines if 'R' in line])
    for j in jobs:
        try:
            setattr(j, 'user', dict_condor_users[j.job_id])
        except KeyError, e:
            setattr(j, 'user', "nobody" )

def get_condor_jobtypes(jobs, server_name, pool_name, verbose=0):
    cmd = 'condor_q -name %s -pool %s -constraint "JobStatus==2"' % (server_name, pool_name)
    p = os.popen(cmd)
    lines = p.readlines()
    status = p.close()
    if status:
        if verbose:
            print status, lines
        return 0
    dict_condor_jobtypes = dict( [ (line.split()[0],  str(line.split()[1])) for line in lines if 'R' in line])
    for j in jobs:
        try:
            setattr(j, 'jobtype', dict_condor_jobtypes[j.job_id])
        except KeyError, e:
            setattr(j, 'jobtype', "nobody" )


def get_slot_numbers(jobs, server_name, pool_name, verbose=0):
    cmd = 'condor_status -f "%s " GlobalJobID -f "%s \n" Name'
    p = os.popen(cmd)
    lines = p.readlines()
    status = p.close()
    if status:
        if verbose:
            print status, lines
        return 0

    dict_condor_slotids = {};

    for l in lines:
      if ( l.find("undefined") == -1 and l.find("#") >= 0  and len(l.split()) == 2 ):
        if verbose: print "LINE is %s " % l 
        try:
          slotid = l.split()[1].split('@')[0]
          if verbose: print "slotid is %s " % slotid
        except KeyError, e:
          if verbose: print "slotid NOTFOUND"

        # accommodate nodes with 1 cpu and no slots defined
        try:
          longhost = l.split()[1]
          if (longhost.find("@") >= 1):
            host = l.split('@')[1]
          else:
            host = longhost
          if verbose: print "host is %s " % host
        except KeyError, e:
          if verbose: print "host NOTFOUND"

        try:
          key = l.split()[0].split('#')[1]
          if verbose: print "key is %s " % key
        except KeyError, e:
          if verbose: print "key NOTFOUND"

        # get the correct slotid
        if ( slotid.find("slot1_") >= 0 or slotid.find("slot3_") >= 0 or slotid.find("slot5_") >= 0 ):
          slotid = int(slotid[6:])
        elif ( slotid.find("slot") >= 0):
          slotid = int(slotid[4:])
        else:
          slotid = 0
        if verbose: print 'slotid is %s' % slotid

        # create RemoteHost with the correct slot id
        rh = 'slot' + str(slotid) + '@' + host
        if verbose: print "RemoteHost is %s " % rh 

        try:
          dict_condor_slotids[key] = rh;
        except KeyError, e:
          if verbose: print "cannot add slotid to dict" 

    for j in jobs:
          try:
            setattr(j, 'RemoteHost', dict_condor_slotids[j.job_id])
            if verbose: print "RemoteHost OK"
          except KeyError, e:
            if verbose: print "RemoteHost NOT GOOD"

