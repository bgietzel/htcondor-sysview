#!/usr/bin/env python
#
# $Id$

from vars import *
from sv_util import *
from condor_util import *
from mc_util import *
import sys, os, re, time, string
import memcache
import json
import socket


legend_height = 350
#legend_height = 300

mc = None
verbose = 0
debug = 0
admin = False
sugar = False
glidein = False
wantjson = False
cave = False
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
    if x.startswith('-a'):
        admin = True
        URL=BASE_URL + "/mosaic.html"
        print "Admin version including job data"
    if x.startswith('-s'):
        sugar = True
        URL=BASE_URL + "/sugar.html"
        print "Only show active cpus"
    if x.startswith('-j'):
        wantjson = True
        print "write results to json file"
    if x.startswith('-c'):
        cave = True
        print "write files for cave"
    if x.startswith('-g'):
        glidein = True
        num_glidein_jobs = 0
        num_glidein_hosts = 0
        legend_height = 150
        columns = 120
        URL=BASE_URL + "/glidein.html"
        print "Only show glidein cpus"



print "CLUSTER_ID is %s " % CLUSTER_ID
print "URL is %s " % URL

main_timer = Timer("overall")

# Poor man's lock
p=os.popen('ps ax|grep mosaic_render.py|grep python|grep -v grep|wc -l')
n = int(p.read())
if n > 1:
    if verbose: print "another mosaic_render instance is running, exiting"
    sys.exit(1)
p.close()


def img(ostream, arg, width, height, left, top, name=None, text=None, link=None):
    img = None
    if type(arg) == str:
        img = arg
        dot_type = None
    elif type(arg) == tuple:
        if len(arg) == 4:
            r,g,b, dot_type = arg
        elif len(arg) == 3:
            r,g,b = arg
            dot_type = None
    else:
        print "???", arg
        return
        
    if text and (admin or glidein):
        ostream.write("<div id='%s.msg' class='xstooltip' style='left: %dpx; top:%dpx;'\n" % (name, left+16, top+16))
        ostream.write("<b>%s</b></br>" % name)
        for line in text:
            line = ' ' + line
            line = line.replace(' ', '&nbsp;') + '</br>'
            ostream.write(line)
        ostream.write("</div>\n")

    if img:
        ostream.write("<img src=%s width=%d height=%d style='position:absolute; left:%dpx; top:%dpx'" % (img, width, height, left, top))
    else:
        ostream.write("<div style='background-color:#%02x%02x%02x; width:%dpx; height:%dpx; position:absolute; left:%dpx; top:%dpx'" % (r,g,b, width, height, left, top))
    if name and (admin or glidein):
        ostream.write(" id='%s.div'\n" % name)
    if text and (admin or glidein):
        ostream.write(" onmouseover=\"xstooltip_show(\'%s.msg\', \'%s.div\', %d, %d)\"\n" % (name, name, left+16, top+16))
        ostream.write(" onmouseout=\"xstooltip_hide(\'%s.msg\');\"\n" % name)
        ostream.write(" onclick=\"xstooltip_click(\'%s.msg\', \'%s\');\"\n" % (name, link or ''))
    ostream.write("/>\n")

    if ( dot_type and (admin or glidein)): 
        ostream.write("<img src=../images/%s.png>" % dot_type)
    if not img:
        ostream.write("</div>")


def mkpage(data, filename):

    global page_width
    
    N=len(data)
    rows = N/columns
    if N%columns:
        rows += 1
    o=open(filename + '.tmp', 'w')

    page_width=columns*(spacing+size) + size + 2*border_width

    o.write(
        """<html><head>
        <META HTTP-EQUIV="Refresh" CONTENT="300; URL=%s">
        <title>mosaic sysview</title>
        <style type="text/css">
        img {
            border-style: solid;
            border-width: 0px;
        }
        .xstooltip 
        {
            visibility: hidden; 
            position: absolute;
            background-color: yellow;
            top: 0;  
            z-index: 2;
            font: normal 8pt sans-serif; 
            padding: 3px; 
            border: solid 1px;
        }
        </style>
        <script type="text/javascript" src="xstooltip.js"></script>
        </head>
        <body bgcolor=black>""" % URL
        )


    o.write("""<div  style="position:relative; width:%dpx; left:50%%; margin-left:%dpx;">\n"""
            % (page_width, -page_width/2))


    # now adjust the y  
    img(o, grey, 
         2*border_width + columns*(size+spacing)+spacing,
         2*border_width + rows*(size+spacing)+spacing + 5,
         margin, margin + legend_height - 3 )

    img(o, black,
         columns*(size+spacing)+spacing,
         rows*(size+spacing)+spacing + legend_height,
         margin+border_width, margin+border_width)

    # grey line across top    
    img(o, grey, 
         2*border_width + columns*(size+spacing)+spacing,
         10,
         margin, 
         margin + legend_height - 3 )


    # bottom of last row
    if N % columns:
        x = margin + border_width + (size+spacing)*(N%columns) + spacing
        y = margin +  border_width + (size+spacing)*int(N/columns) + spacing + legend_height 

        w = (size + spacing) * (columns - N%columns)
        h = size + spacing + border_width
        img(o, grey, w, h, x, y)
        img(o, black, w, h,
             x+border_width, y+border_width)
     
    for y in xrange(rows):
        for x in xrange(columns):
            n=y*columns+x
            if n >= N:
                break

            # leave room for the legend at top
            name, (r,g,b), dot_type, text, link = data[n]

            # try changing bgcolor to yellow if glidein
            if glidein:
              img(o, yellow,
                size+2, size+2,
                margin+border_width+spacing+x*(size+spacing)-1,
                margin+border_width+spacing+y*(size+spacing) + legend_height + 1)

            img(o, (r,g,b,dot_type),
                size, size,
                margin+border_width+spacing+x*(size+spacing),
                margin+border_width+spacing+y*(size+spacing) + legend_height,
                name, text, link)

    ## Use oldest timestamp
    timestamp = min(map(lambda x: mc_get(x + ".time"), CLUSTER_IDS))
    t = time.strftime("%a %b %d %Y %H:%M:%S", time.localtime(timestamp))
    width=columns*(spacing+size) + size + 2*border_width
    x = 0
    y = rows*(spacing+size)+spacing + 2*border_width + margin

    # add eff icon for link to metrics pages
    eff_y = y 
    ename = WEBDIR + '/effcy.txt'
    efile = open(ename)
    effcy = int(float(efile.readline()))
    efile.close()

    if not glidein:
      effcy_png = WEBDIR + '/effcy.png'
      os.system("convert xc:black -resize %dx64! -fill \#0000ff -pointsize 60 -gravity West -draw \"text %d,0 '%s'\" %s "%(eff_width,eff_offset,effcy,effcy_png))
      print "Cluster efficiency is %s percent" % effcy 

    # draw the date as a png 
    label_png = WEBDIR + '/label.png'
    os.system("convert xc:black -resize %dx64! -fill \#00ff00 -pointsize 60 -gravity West -draw \"text %d,0 '%s'\" %s "%(width,offset,t,label_png))
  
    img(o, "label.png", width, height, x, y + legend_height)
    o.write("</div>\n<div>")
    elink = BASE_URL + '/jobinfo/userjobs7.html'
    if admin:
      img(o, "effcy.png", eff_width,eff_height, x + 700, y + height + legend_height, "effcy", "effcy", link = elink )
    elif not glidein:  
      img(o, "effcy.png", eff_width,eff_height, x + 700, y + height + legend_height, "effcy", "effcy", link = None )

    # write out legend at the top
    curr_height = 0 
    if not glidein:
      text = "Each square represents a core in the %s pool" % CLUSTER_ID
      my_png = "%s/text.png" % (WEBDIR)
      os.system("convert xc:black -resize %dx64! -fill \%s -pointsize 60 -gravity West -draw \"text %d,0 '%s'\" %s "%( eff_width * 12, "grey", eff_offset, text, my_png))
      img(o, "text.png", eff_width * 9, eff_height, margin + 250, curr_height )

    elif glidein: 
      text1 = "Glidein Pool"
      my_png = "%s/text1.png" % (WEBDIR)
      os.system("convert xc:black -resize %dx64! -fill \%s -pointsize 60 -gravity West -draw \"text %d,0 '%s'\" %s "%( eff_width * 12, "grey", eff_offset, text1, my_png))
      img(o, "text1.png", eff_width * 9, eff_height, margin + 250, curr_height )

    curr_height = curr_height + eff_height 

    slotdesc = {green: "busy", red: "down", dkgrey: "owner", pink: "offline", black: "idle", dkgreen: "backfill", yellow: "glidein", dkyellow: "unclaimed" }

    # remove all other slot info for glideins
    if glidein:
      
      num_glidein_jobs = slotdata[yellow]
      print "Of %s total glidein hosts, %s are busy" % (num_glidein_hosts, num_glidein_jobs)
      slotdata.clear()
      num_glidein_idle = int(num_glidein_hosts) - int(num_glidein_jobs)
      slotdata[yellow] = num_glidein_jobs
      # use a diff color for idle glidein nodes as not to confuse regular idle jobs
      slotdata[dkyellow] = num_glidein_idle
    else: 
      del slotdata[yellow]
      del slotdata[dkyellow]

    # render each legend item as a png and display it.
    for color in slotdata.keys():
     if sugar and color == green or not sugar:
      count=str(slotdata[color])
      if debug: print "count is %s" % count
      status = slotdesc[color]
      count_text = "%s %s" % (count, status)
      color_reduced = reduce(lambda rst, d: rst * 10 + d, color)
      if debug: print "color_reduced is %s" % color_reduced
      if (color_reduced == 0): # make black into gray color so it shows up on black bg
        color_reduced = "190190190"; 
        color = (124, 124, 124)
      my_png_name = "%s.png" % (color_reduced)
      if debug: print "my_png_name is %s" % my_png_name 
      my_png = "%s/%s.png" % (WEBDIR, color_reduced)
      if debug: print "my_png is %s" % my_png 
      my_color = '#%02x%02x%02x' % (color)
      if debug: print "my_color is %s" % my_color

      os.system("convert xc:black -resize %dx64! -fill \%s -pointsize 50 -gravity West -draw \"text %d,0 '%s'\" %s "%( eff_width * 4, my_color, 50, count_text, my_png))
      img(o, my_png_name, eff_width * 4, 50, margin + 600, curr_height  )
      o.write("</div>\n<div>")
      curr_height = curr_height + 50

    o.write("</div>\n")
    o.write("</body></html>\n")
    o.close()
    os.rename(filename + '.tmp', filename)


def mkjson(data, filename):
  with open(filename, 'w') as outfile:
    json.dump(data, outfile)
    #name, (r,g,b), dot_type, text, link = data[n]


# write out text file  
def mkjsonfile(data, filename):

  o = open(filename, 'w')

  for msd in data:
    n = msd['name']
    c = msd['children']

    n = longname(n)
    #glidein.16805@some.host.edu
    if (n.find("glidein") >= 0):
      n = n.split('@')[1]

    if debug: print "host is %s" % n
    addr = "0.0.0.0"
    if ( n != "test"):
      try: 
        addr = socket.gethostbyname(n)
   
      except socket.gaierror, e:
        addr = "0.0.0.0"
    
    if debug: print "addr is %s" % addr

    for j in c:
      if (j['user'] == ""): 
        j['user'] = "X"
      s = " %s %s %s %s %s " % (j['name'], j['user'], j['rr'], j['gg'], j['bb'])
      o.write(n)
      o.write(s)
      o.write(addr)
      o.write("\n")
  o.close()


# write out file for nodes
def mknodefile(data, filename):

  o = open(filename, 'w')

  for node in nodes:
    n = shortname(node)
    np, state, load, pool, msg = node_info.get(n + '.info')

    if ( state == ""):
      state = "online"
 
    n = longname(node)
    #glidein.16805@some.host.edu
    if (n.find("glidein") >= 0):
      n = n.split('@')[1]

    if debug: print "host is %s" % n

    addr = "0.0.0.0"
    if ( n != "test"):
      try: 
        addr = socket.gethostbyname(n)
      except socket.gaierror, e:
        addr = "0.0.0.0"
    
    if debug: print "addr is %s" % addr

    stats = "%s %s %s %s %s " % (n, np, state, load, pool)
    o.write(stats)
    o.write(addr)
    o.write("\n")
  o.close()

def mkslotfile(data, filename):

  o = open(filename, 'w')

  for msd in data:
    n = msd['name']
    c = msd['children']

    if debug: print "slothost is %s" % n

    for j in c:
      if (j['user'] == ""): 
        j['user'] = "X"
      s = " %s %s %s %s " % (j['name'], j['user'], j['c'], j['w'])
      o.write(n)
      o.write(s)
      o.write("\n")

def hsl2rgb(h,s,l):
##  http://en.wikipedia.org/wiki/HSL_and_HSV#Conversion_from_HSL_to_RGB
    if l < 0.5:
        q = l * (1+s)
    else:
        q = l + s - (l*s)
    p = 2*l - q
    hk = h/360.0
    t = [(hk + 1/.3) % 1 , hk % 1, (hk - 1/3.)%1]
    r = []
    for tc in t:
        if tc < 1/6.:
            c = p + (q-p)*6*tc
        elif 1/6. <= tc < 1/2.:
            c = q
        elif 1/2. <= tc < 2/3.:
            c = p + ((q-p)*6*((2/3.) - tc))
        else:
            c = p
        r.append(c)
    r = map(lambda x: int(x*255), r)
    return r

def rgb(wsecs, csecs):
    if wsecs==csecs==0:
        return 128,128,128 # No info # ???
    if wsecs >= 604800: # a week old!
        return 0, 0, 255# very blue
    if wsecs < 60:  # New jobs are white
        return white
    eff = float(csecs)/wsecs
    ## hsl coding
    green = 120.0
    blue = 220.0

    if wsecs > 600:
        h = blue + eff*(green-blue)
    else:
        h = green
    s = 1
    t = min( wsecs/7200.0, 1)  # hours
    l = 0.6 - 0.4*t
    return hsl2rgb(h, s, l)


def cmp_node(a,b): 
    if a.startswith('test') and b.startswith('prod'):
        return -1
    if a.startswith('prod') and b.startswith('test'):
        return 1
    return cmp(a,b)


nodes = []
jobs = []

timer = Timer("get node and job list")
for CLUSTER_ID in CLUSTER_IDS:
    nodes_tmp = mc_get(CLUSTER_ID+'.nodes')
    #nodes_tmp.sort(cmp_node)
    nodes.extend(nodes_tmp)
    jobs.extend(mc_get(CLUSTER_ID+'.running_jobs'))

del nodes_tmp

timer.end()

if debug: 
  for jj in jobs:
    print "THISJOB %s" % jj
 
timer = Timer("get node info")
keys = []
for node in nodes:
    if debug: print "NODE is %s " % node
    keys.append(shortname(node)+".info")
node_info = mc_get_multi(keys)
timer.end()

timer = Timer("get job info")
job_times = mc_get_multi(["%s.times"%j for j in jobs])
job_prev_times = mc_get_multi(["%s.prev_times"%j for j in jobs])
job_users = mc_get_multi(["%s.user"%j for j in jobs])

job_mem = mc_get_multi(["%s.mem"%j for j in jobs])
job_types = mc_get_multi(["%s.type"%j for j in jobs])
timer.end()

# For each square:
# name, (rgb), dot_type, comment, url
data = []

keys = []
for node in nodes:
    name = shortname(node)
    if debug: print "NAME is %s " % name
    np, state, load, pool, msg = node_info.get(name + '.info')

    # glidein jobs all report as slot1 se we need to find the slot later from the hostname
    for slot in xrange(1, np+1):
        keys.append("%s.%d" % (name, slot))

timer = Timer("get job slot info")
slot_info = mc_get_multi(keys)
timer.end()

timer = Timer("munge data")
keys = []

# set up node status counts for legend
slotdata = {green: 0, red: 0, pink:0, dkgrey: 0, black: 0, dkgreen: 0, yellow: 0, dkyellow: 0}

myhost = "test"
myslots = []

pool_list = sorted(pool_names.keys())
pool_list.append('default')
for pool_abbr in pool_list: 
  if verbose: print "pool_abbr is %s" % pool_abbr
  for node in nodes:
    hostname = shortname(node)
    if debug: print "HOSTNAME is %s " % hostname
    ncpu, state, load, pool, msg = node_info.get(hostname + '.info')

    # for down hosts, try to assign the host to a pool if it has none ie. default
    if (pool == 'default'):
      p = hostname.split("_")[1]
      if p in pool_list:
        pool = p 

    # non-glidein hosts 
    if (pool != 'glidein' and pool != 'glidein2' and pool_abbr == pool and glidein == False): 
      for slot in xrange(1, ncpu+1):
        if debug: print "slot is %d " % slot

        color = black
        wsecs = csecs = 0
        dot_type = ''
        link = None

        text = []
        slotname = "%s/%s" % (hostname, slot)
        job = slot_info.get("%s.%d" % (hostname, int(slot)))

        if job:
            if verbose:
              print "HAVE JOB %s" % job

            wsecs, csecs = job_times.get("%s.times"%job, (0,0))
            prev_wsecs, prev_csecs = job_prev_times.get("%s.prev_times"%job, (0,0))
            rss, vm = job_mem.get("%s.mem"%job, ('0','0'))
            walltime = cputime = "???" # display string
            if verbose: print "WALLTIME %s " % walltime
           
            dot_type = job_types.get('%s.type' % job)

            if wsecs and prev_wsecs:
                wsecs -= prev_wsecs
            if csecs and prev_csecs:
                csecs -= prev_csecs
 
            if wsecs < 0:
                wsecs=0.01
            if csecs < 0:
                csecs=0

            if admin:
              link = 'jobinfo/%s.html' % job

            if state not in ('free', 'job-exclusive'):
                text.append(state)
            if vm and rss:
                text += ['rss %s vm %s' %(rss, vm)]
            if prev_wsecs:
                walltime = "%s (-%s)" % (HMS(wsecs), HMS(prev_wsecs))
            else:
                walltime = HMS(wsecs)
            if prev_csecs:
                cputime = "%s (-%s)" % (HMS(csecs), HMS(prev_csecs))
            else:
                cputime = HMS(csecs)
            text += ['wall time %s'%walltime, 'cpu time %s'%cputime]
            if wsecs == 0:
                wsecs = 1
            effcy = 100.0 * csecs / wsecs
            if walltime != '???' and cputime != '???':
                text.append('cpu efficiency  %.1f%%' %effcy)

            color = rgb(wsecs, csecs)
            if verbose: print "COLOR %s %s %s " % (color, wsecs, csecs)
            slotdata[green] += 1

            # is this a boinc job?
            if ( job.startswith(".")):
              if debug: print "Backfill job %s" % job
              dot_type = 'b'
              color = rgb(7200, 7200)
              effcy = 100
              slotdata[dkgreen] += 1
         
            # is this a slurm job?
            if ( job.endswith(".")):
              if debug: print "slurm job %s" % job
              dot_type = 's'
              color = rgb(7200, 7200)
              effcy = 100
              slotdata[dkgreen] += 1

            if debug: print "dot_type is %s" % dot_type
 
        else:
            wsecs = csecs = 0
            if (admin):
              link = 'job_info/UNAVAILABLE'
            text.append(state)

        if 'offline' in state:
            color = pink
            slotdata[pink] += 1
        elif 'down' in state:
            color = red
            slotdata[red] += 1
        elif 'owner' in state and not job:
            color = dkgrey
            slotdata[dkgrey] += 1
        if msg and 'ERROR' in msg:
            color = red
            slotdata[red] += 1

        if verbose:
            print 'host=', hostname, 'slot=', slot, 'job=', job, dot_type, wsecs, csecs, color

        if load is not None:
            try:
                load = float(load)
                text.insert(0, 'load %.02g' % load)
            except ValueError:
                text.insert(0, 'load %s' % load)

        if job:
            user = job_users.get('%s.user'%job, None)
            if verbose: print "USER is %s " % user
            if user:
                if user.endswith("@somedomain.org"):
                    user = user.split('@')[0]
                text.insert(0, "<b>user: %s</b>" % user)
                
        if msg:
            if color == red:
                color = pink
            if 'maintenance' in msg.lower():
                color = grey
            text.append("note: " + msg)

        # only publish active cpus for sugar mode
        if sugar:
          if color not in (black, red):
            data.append((slotname, color, dot_type, text, link))
        elif wantjson:
            # create the correct json hierarchy
            # if we have a different host, write out previous array
            if ( hostname.find(myhost) < 0 and len(myhost) > 0): 
              print "%s %s" % (hostname, myhost)
              myslotdata = {'name': longname(myhost), 'children': myslots}
              data.append( myslotdata) 
              myslots = []
              myhost = hostname

            # store the current job/slot info
            # set sizeto 0 if name is null to ensure the slot isn't rendered ?
            myslotinfo = {"name": slot, "size": 10, "user": dot_type, "rr": color[0], "gg": color[1], "bb":color[2]}
            myslots.append(myslotinfo)

        elif cave:
            if ( hostname.find(myhost) < 0 and len(myhost) > 0): 
              myslotdata = {'name': longname(myhost), 'children': myslots}
              data.append( myslotdata) 
              myslots = []
              myhost = hostname
            # store the current job/slot info
            myslotinfo = {"name": slot, "size": 10, "user": dot_type, "c": csecs, "w": wsecs}
            myslots.append(myslotinfo)

        elif not glidein:
          data.append((slotname, color, dot_type, text, link))

        if verbose: print "slotname %s " % (slotname)    
        if verbose: print "color %d %d %d " % (color[0], color[1], color[2]) 
        if verbose: print "dot_type %s " %  dot_type      
        if verbose: print "text %s " % text      
        if verbose: print "link %s " % link      
        if (color == black):
          slotdata[black] += 1

    # ensure we have a glidein by looking at the hostname
    elif ( pool_abbr.startswith('glidein') and pool.startswith('glidein') and glidein):
      # glideins always run on slot1 so use glidein id as slot
      # eg. hostname is glidein_123@nb-somehost_someu_edu, jobid is 1.123, slot is 123
      if (hostname.find('glidein') >= 0):
        # some glidein hosts now have slot information included
        # slot8@glidein_55654@some.host.edu
        if ( hostname.count('@') == 2 ):
          host = hostname.split('@')[2]
          tmp = hostname.split('@')[1]
        else:
          host = hostname.split('@')[1]
          tmp = hostname.split('@')[0]

        slot = tmp.split('_')[1]

        num_glidein_hosts += 1

        if verbose: print "hostname is %s and slot is %s" % ( hostname, slot) 

        # find which CE the glidein host belongs to 
        domain = host.split("_")[-1]
        #ce = get_ce(domain) 

        color = black
        wsecs = csecs = 0
        dot_type = ''
        link = None

        text = []

        key = "%s.%d" % (shortname(hostname), int(slot))
        job = mc_get(key)

        if job:
          if verbose:
            print "HAVE GLIDEIN JOB %s" % job
 
          # TODO this code is duplicated from above, clean it up 
          wsecs, csecs = job_times.get("%s.times"%job, (0,0))
          prev_wsecs, prev_csecs = job_prev_times.get("%s.prev_times"%job, (0,0))
          rss, vm = job_mem.get("%s.mem"%job, ('0','0'))
          walltime = cputime = "???" # display string
          if verbose: print "WALLTIME %s " % walltime
          
          dot_type = job_types.get('%s.type' % job)

          if wsecs and prev_wsecs:
                wsecs -= prev_wsecs
          if csecs and prev_csecs:
                csecs -= prev_csecs
 
          if wsecs < 0:
                wsecs=0.01
          if csecs < 0:
                csecs=0

          link = 'jobinfo/%s.html' % job

          if state not in ('free', 'job-exclusive'):
                text.append(state)
          if vm and rss:
                text += ['rss %s vm %s' %(rss, vm)]
          if prev_wsecs:
                walltime = "%s (-%s)" % (HMS(wsecs), HMS(prev_wsecs))
          else:
                walltime = HMS(wsecs)
          if prev_csecs:
                cputime = "%s (-%s)" % (HMS(csecs), HMS(prev_csecs))
          else:
                cputime = HMS(csecs)
          text += ['wall time %s'%walltime, 'cpu time %s'%cputime]
          if wsecs == 0:
                wsecs = 1
          effcy = 100.0 * csecs / wsecs
          if walltime != '???' and cputime != '???':
                text.append('cpu efficiency  %.1f%%' %effcy)

          user = job_users.get('%s.user'%job, None)
          if verbose: print "USER is %s " % user
          if user:
              if user.endswith("@somedomain.org"):
                  user = user.split('@')[0]
              text.insert(0, "<b>user: %s</b>" % user)

          color = rgb(wsecs, csecs)
          slotdata[yellow] += 1

        else:
          wsecs = csecs = 0
          link = 'job_info/UNAVAILABLE'
          text.append(state)
          if (color == black):
            slotdata[black] += 1

        slotname = "%s/%s" % (host, slot)
        data.append((slotname, color, dot_type, text, link))

timer.end()

timer = Timer("mkpage")
if sugar:
  filename = WEBDIR + '/sugar.html'
elif admin:
  filename = WEBDIR + '/mosaic.html'
if wantjson:
  jsonfname = "/tmp/file.json"
  jsonfile = "/tmp/jsonfile"
  mkjson(data, jsonfname)
  mkjsonfile(data, jsonfile)
if cave:
  nodefile = "/tmp/nodefile"
  slotfile = "/tmp/slotfile"
  mknodefile(data, nodefile)
  mkslotfile(data, slotfile)
elif glidein:
  filename = WEBDIR + '/glidein.html'
else:
  filename = WEBDIR + '/sysview.html'

if not wantjson and not cave:
  mkpage(data, filename)
timer.end()

## XXX  TODO We should fold the generation of the small image into
## the above - but for now ...

if not wantjson and not cave:
    timer = Timer("generate small image")
    if verbose: print "mksysimage.sh"
    p=os.popen('./mksysimage.sh','w')

    for line in data:
        r,g,b = line[1]
        a = line[2]
        p.write('%s %s %s %s\n' % (r, g, b, a))
    status = p.close()
    if status:
        print 'writeppm returns', status
    timer.end()

main_timer.end()


