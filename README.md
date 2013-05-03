SYSVIEW README

htcondor-sysview is an efficiency monitor for HTCondor pools and jobs.

05.01.2013 1.13 release.
Originally written as Mosaic Sysview by Charles Waldman and Sarah Williams and Rob Gardner of MWT2.org. Modified by Rebekah Gietzel (bgietzel@cs.wisc.edu) to work with UW-Madison CHTC pool and HTCondor features including partitionable slots, multiple pools and submitters.  Packaged by Nate Yehle (nyehle@cs.wisc.edu)

This 1.13 release should work with most HTCondor pool configs including static and partionable slots.

The program draws the grid of cpus in HTCondor pools.  Each cpu (core) is one square on the grid.  Nodes produce squares based on the # of cpus listed in their names in the nodes.list file.  Jobs are displayed on a slot basis and map 1:1 by default.  When partitionable slots are used, each square represents a slot.  The color of each square indicates the status of that core and/or node.

Red squares are slots where sysview detects a htcondor startd is not running correctly.

Efficiency is computed as cputime/walltime of the job running on a slot.

Green squares are slots where efficient jobs are running.

Blue squares are slots where inefficient jobs are running.

Lighter green or blue squares are new jobs trending efficient or inefficient respectively.  As the jobs age and the cputime/walltime ratio stabilizes the colors darken.

Other multicolored squares are jobs using more than 100% efficiency, as in multicore jobs.  They are represented by only one square showing how one multicore job prevents other jobs from using the total number of slots.

Once you have a mosaic output using information about your cluster, try to drag the mouse across a slot on the mosaic.

Mouseover various squares shows slotname, user, online/down, rss/vm memory status, cpu time, and efficiency for the current job on the slot.  We use this as an easy way to spot down nodes or jobs which have low efficiency and are wasting slots.  Clicking a slot takes you to the full dump of condor_q -l for the job running on that core. 

