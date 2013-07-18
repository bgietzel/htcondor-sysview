#!/usr/bin/env python
#
# $Id$

import os

# dir and url setup
BASEDIR=os.path.abspath(".")
WEBDIR=BASEDIR + "/html"
URL_DIR=os.path.split(BASEDIR)[-1]
BASE_URL='http://yourserver.org/' + URL_DIR
URL=BASE_URL + "/mosaic.html"
CONDOR_URL=BASE_URL + 'jobinfo/'

# clusters
CLUSTER_ID="TEST"
CLUSTER_IDS=["TEST"]

# Stats are associated with the first submitter
server_name="submit-1.yourdomain.org" # Stats are associated with the first submitter

server_names={"submit-1.yourdomain.org":"a","submit-2.yourdomain.org":"b"}

pool_names={"a":"poola", "b":"poolb"}

# UI preferences (based on pool size)
margin=10
size=14
spacing=2
border_width=8
columns=120

eff_offset = 30
eff_width = 120
eff_height = 60

# Colors
white = 255, 255, 255
grey = 128, 128, 128
black = 0, 0, 0
green = 0, 255, 0
dkgreen = 0, 128, 0 
pink = 255, 128, 128
red = 255, 0, 0

# fonts
height=64 
offset=350
pntsize = 60 

