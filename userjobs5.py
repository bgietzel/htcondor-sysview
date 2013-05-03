#!/usr/bin/env python
#
# $Id: Exp $
#
#  Write out html user reports


from vars import *
from sv_util import *
from mc_util import *
import sys, os, re, time, string
import memcache


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


def write_header(ofile=sys.stdout):
    ofile.write("""<html><head><title>User/Job summary for %s</title></head>
<script src='sorttable.js'></script>
<style type="text/css">
th, td {
    padding: 3px !important;
    }

table.sortable thead {
    background-color:#eee;
    color:#666666;
    font-weight: bold;
    cursor: default;
    }
</style>

<body>
<h3>User/Job summary for %s</h3>
<h3>Generated on %s</h3>
The table is sortable.""" % ( CLUSTER_ID, CLUSTER_ID, time.ctime() ) )

def mask_eq(k1, k2, mask):
    return  ((mask&1 or k1[0]==k2[0])
             and (mask&2 or k1[1]==k2[1])
             and (mask&4 or k1[2]==k2[2]))

def merge_keys(keys, mask=0):
    groups = []
    keys = keys[:] # copy
    while keys:
        k1, keys = keys[0], keys[1:]
        group = [k1]
        for k2 in keys[:]:
            if mask_eq(k1, k2, mask):
                group.append(k2)
                keys.remove(k2)
        groups.append(group)
    return groups

def write_job_table(jobs, group, ofile=sys.stdout, merge_mask=0):
    fields = ["User", "Type", "Site", "HTCondor ID", "Walltime", "CPU time", "%Efficiency"]
    merge_user = merge_mask & 1
    merge_type = merge_mask & 2
    merge_site = merge_mask & 4
    ofile.write("<table class='sortable'><thead><tr>")
    for i, field in enumerate(fields):
        text = field
        if i < 3:
            merge_field = merge_mask & (1<<i)
            link = merge_mask^(1<<i) # or ''
        ofile.write("<th align='center'>%s</th>" % text)
    ofile.write("</tr></thead>")
    ofile.write("<tbody>")
    rows=[]
    for keys in group:
	  user, jobtype, site = keys
	  for job in jobs[keys]:
	     jobid = job[0]
             jobid = str(jobid)
             if (jobid != 'None'):

	       try:
			walltime = job[2][0] 
	       except TypeError, e:
			walltime=0
	       try:
			cputime = job[2][1]
	       except TypeError, e:
			cputime=0

	       if walltime:
		    effcy  = 100.0 * cputime / walltime
	       else:
		    effcy = 0
	       rows.append((-walltime, """<tr><td>%s</td>
<td>%s</td>
<td align='center'>%s</td>
<td align='right'><a href='%s%s.html'>%s</a></td>
<td sorttable_customkey='%s' align='right'>%s</td>
<td sorttable_customkey='%s' align='right'>%s</td>
<td align='right'>%.2f</td>
</tr>\n""" % (user, jobtype, site, CONDOR_URL, jobid, jobid, walltime, HMS(walltime), cputime, HMS(cputime), effcy)))
    rows.sort()
    for row in rows:
        ofile.write(row[1])
    ofile.write("</table>")

def write_table(jobs, ofile=sys.stdout, merge_mask=0):
    fields = ["User", "Type", "Site", "#Jobs", "Walltime", "CPU time", "%Efficiency"]
    merge_user = merge_mask & 1
    merge_type = merge_mask & 2
    merge_site = merge_mask & 4
    ofile.write("<table class='sortable'><thead><tr>")
    for i, field in enumerate(fields):
        text = field
        if i < 3:
            merge_field = merge_mask & (1<<i)
            link = merge_mask^(1<<i) # or ''
            if merge_field:
                text += '<a href=userjobs%s.html>(show)</a>' % link
            else:
                text += '<a href=userjobs%s.html>(hide)</a>' % link

                
        ofile.write("<th align='center'>%s</th>" % text)
    ofile.write("</tr></thead>")
    ofile.write("<tbody>")

    keys = jobs.keys()
    keys.sort()
    groups = merge_keys(keys, merge_mask)
    rows = []
    for group in groups:
        data = []
        for key in group:
            user, jobtype, site = key
            if debug: print "USER %s, JOBTYPE %s, SITE %s" % (user, jobtype, site)
            #if user is None:
            #    continue
            data += jobs[key]
        if merge_user:
            user = ""
        if merge_type:
            jobtype = ""
        if merge_site:
            site = ""
        njobs = len(data)
        #job_index_filename= '_'.join([ strip_chars(k) for k in key]) + ".html"

        # TODO find out why these files are not named correctly.
        job_index_filename=strip_chars("%s_%s_%s.html" % ( user, jobtype,site))
	ji_file = open("jobinfo/" + job_index_filename, 'w') 
        write_header(ji_file)
	#write_job_table(data, key, ji_file, merge_mask)
        write_job_table(jobs, group, ji_file, merge_mask)
        write_footer(ji_file)
	ji_file.close()
        walltime = sum([x[2][0] for x in data if x[2] is not None])
        cputime = sum([x[2][1] for x in data if x[2] is not None])
        if walltime:
            effcy  = 100.0 * cputime / walltime
        else:
            effcy = 0
        rows.append((-walltime, """<tr><td>%s</td>
<td>%s</td>
<td align='center'>%s</td>
<td align='right'><a href='.%s'>%d</a></td>
<td sorttable_customkey='%s' align='right'>%s</td>
<td sorttable_customkey='%s' align='right'>%s</td>
<td align='right'>%.2f</td>
</tr>\n""" % (user, jobtype, site, job_index_filename, njobs, walltime, HMS(walltime), cputime, HMS(cputime), effcy)))

    rows.sort()
    for row in rows:
        ofile.write(row[1])
    ofile.write("</table>")

    #for the eff
    ename = '%s/effcy.txt' % (WEBDIR)
    efile = open(ename, 'w') 
    efile.write("%s" % effcy)
    efile.close()

def write_footer(ofile=sys.stdout):
    ofile.write("</body></html>\n")

condor_ids = mc_get(CLUSTER_ID+".running_jobs")
if not condor_ids:
	sys.exit(1)

condor_ids.sort()


jobs = {}  # key is (user, type, site)

for condor_id in condor_ids:
    host = mc_get('%s.host' % condor_id)
    # Defaults
    user = 'Unknown'
    times = (0, 0)

    if host:
        if ( host.find('.') >= 0 ):
          site = host.split('.')[1]
        if site.lower().startswith("%s" % CLUSTER_ID):
          site = CLUSTER_ID.lower()
    else:
        site = '??'

    user = mc_get('%s.user' % condor_id)
    jobtype = None
    times = mc_get('%s.times' % condor_id)

    if verbose: print condor_id, user, site, jobtype, times
    key = (user, jobtype, site)
    if not jobs.has_key(key):
        jobs[key] = []
    jobs[key].append((condor_id, host, times))

for merge_mask in xrange(8):
    fname = 'userjobs%d.html' % merge_mask
    ofile = open("jobinfo/" + fname, 'w') # open as hidden file
    write_header(ofile)
    write_table(jobs, ofile, merge_mask)
    write_footer(ofile)
    ofile.close()
    os.rename("jobinfo/"+fname, "jobinfo/"+fname)
