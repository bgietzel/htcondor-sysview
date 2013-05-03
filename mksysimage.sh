#!/bin/sh
#
# $Id: mksysimage.sh,v 1.12 2009/07/30 23:09:47 cgw Exp $

tmpdir=/tmp/mksysimage-tmp.$$.d/
mkdir -p $tmpdir
trap "rm -rf $tmpdir" exit
BASEDIR=`pwd`
WEBDIR=$BASEDIR/html

label_small=$(date +'%a %b %d %H:%M')
label_big=$(date +'%a %b %d %Y %H:%M')

cd $tmpdir
convert xc:black -resize 245x20!   -fill \#00ff00 -pointsize 15 -gravity West -draw "text 64,0 '$label_small'" label_small.ppm
convert xc:black -resize 660x64!   -fill \#00ff00 -pointsize 60 -gravity West -draw "text 24,0 '$label_big'" label_big.ppm


$BASEDIR/writeppm.sh frame_small.ppm 

pnmscale 4 < frame_small.ppm > frame_big.ppm
pnmcat -tb frame_small.ppm label_small.ppm > frame_labeled_small.ppm
pnmcat -tb frame_big.ppm label_big.ppm > frame_labeled_big.ppm
pnmtopng < frame_labeled_small.ppm  > $WEBDIR/sys.png   2> /dev/null
pnmtopng < frame_labeled_big.ppm  > sys_big.png 2> /dev/null

destdir=$BASEDIR/movie
mkdir -p $destdir
cp $WEBDIR/sys.png $BASEDIR/movie/$(date +'%s').png

