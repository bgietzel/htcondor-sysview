#!/bin/sh
# $Id: writeppm.sh,v 1.9 2009/08/04 17:24:12 cgw Exp $

o=.$1
i=0
while read r g b a; do
    color[i]="$r $g $b"
    analy[i]="$a"
    ((i++))
done 
N=$i

echo P6 > $o
columns=64
rows=$((N / columns))
((N % columns)) && ((++rows))
line_width=1
border_width=2
square_size=5

width=$((columns*square_size + (columns+1)*line_width + 2*border_width))
height=$((rows*square_size + (rows+1)*line_width + 2*border_width))
echo $width >> $o
echo $height >> $o
echo 255 >> $o

border_color="128 128 128"
line_color="0 0 0"

pixel () {
    printf \\\\0%o\\\\0%o\\\\0%o $1 $2 $3
}

##
## New more efficient approach
##
##
hborder=
p=$(pixel $border_color)
for (( x=0; x<width; ++x)); do
    hborder=${hborder}${p}
done
hline=
l=$(pixel $line_color)
for (( x=0; x<width-(2*border_width); ++x)); do
    hline=${hline}${l}
done
vborder=''
for (( x=0; x<border_width; ++x)); do
    vborder=${vborder}${p}
done
vline=''
for (( x=0; x<line_width; ++x )); do
    vline=${vline}${l}
done

#Blat out the top border
for ((y=0; y<border_width; ++y )); do
    echo -n -e $hborder  >> $o
done


full_rows=$((N / columns))
for ((row=0,i=0; row<full_rows; ++row)); do
    # Horizontal separator from previous row or border
    for (( y=0; y<line_width; ++y )); do
	echo -n -e ${vborder}${hline}${vborder}  >> $o
    done    
    # Compose a row of colored pixels
    pixels=''
    for (( j=0; j<columns; ++j,++i )); do
	p=$(pixel ${color[i]})
	for (( x=0; x<square_size; ++x )); do
	    pixels=${pixels}${p}
	done
	pixels=${pixels}${vline}
    done
    # Print square_size duplicates of the same pixel line
    for (( y=0; y<square_size; ++y )); do
	echo -n -e ${vborder}${vline}${pixels}${vborder}  >> $o
#	echo -n -e ${vborder}${hline}${vborder} 
    done
done


# Horizontal separator from previous row or border
for (( y=0; y<line_width; ++y )); do
    echo -n -e ${vborder}${hline}${vborder} >> $o
done    
# Finish off that tricky last line
n_left=$(( N - i))
if (( n_left > 0 )) ; then
    n_empty=$(( columns * rows - N ))
    pixels=''
    for (( ; i<N; ++i )); do
	p=$(pixel ${color[i]})
	for (( x=0; x<square_size; ++x )); do
	    pixels=${pixels}${p}
	done
	pixels=${pixels}${vline}
    done

    black_area_width=$((n_empty*(square_size+line_width) ))
    border_empty=''
    black_area=''
    p=$(pixel $border_color)
    b=$(pixel 0 0 0)
    for ((x=0; x<black_area_width; ++x )); do
	border_empty=${border_empty}${p}
	black_area=${black_area}${b}
    done
    border_empty=${border_empty}${vborder}
    
    for ((y=0; y<border_width; ++y )); do
	echo -n -e ${vborder}${vline}${pixels}${border_empty} >> $o
    done
    
    for (( ; y<square_size; ++y )); do
	echo -n -e ${vborder}${vline}${pixels}${vborder}${black_area} >> $o
    done
    
    bottom_line_width=$((n_left*(square_size+line_width)+line_width))
    bottom_line=''
    for (( x=0; x<bottom_line_width; ++x )); do
	bottom_line=${bottom_line}${b}
    done
    
    for (( y=0; y<line_width; ++y )); do
	echo -n -e ${vborder}${bottom_line}${vborder}${black_area} >> $o
    done
else
    bottom_line_width=$((columns*(square_size+line_width)+2*line_width))
    bottom_line=''
    for (( x=0; x<bottom_line_width; ++x )); do
	bottom_line=${bottom_line}${b}
    done
    for (( y=0; y<line_width; ++y )); do
	echo -n -e ${vborder}${bottom_line}${vborder} >> $o
    done
fi

# Compose the bottom border
bottom_border_width=$((bottom_line_width+2*border_width))
bottom_border=''
p=$(pixel $border_color)
for (( x=0; x<bottom_border_width; ++x )); do
    bottom_border=${bottom_border}${p}
done

for (( y=0; y<border_width; ++y )); do
    echo -n -e ${bottom_border}${black_area} >> $o
done

# add annotations
script=''
for (( i=0; i<N; ++i )); do
    a=${analy[i]}
    if [ -n "$a" ] ; then
	row=$(( i / columns ))
	column=$(( i % columns ))
	x=$(( column * (square_size+line_width) + border_width + 3))
	y=$(( row * (square_size+line_width) + border_width + 3))
	if [[ $a == 'a' ]] ; then
	    script="$script -draw \"circle "$x,$y,$((x-1)),$((y))"\""
	elif [[ $a == 's' ]]; then
	    (( x -= 3 ))
	    (( y += 3 ))
	    script="$script -draw \"text $x,$y s\""
	elif [[ $a == 'x' ]]; then
	    (( x -= 3 ))
	    (( y += 3 ))
	    script="$script -draw \"text $x,$y x\""
	elif [[ $a == 'o' ]]; then
	    (( x -= 3 ))
	    (( y += 3 ))
	    script="$script -draw \"text $x,$y o\""
	elif [[ $a == 'i' ]]; then
	    (( x -= 1 ))
	    (( y += 3 ))
	    script="$script -draw \"text $x,$y i\""
	elif [[ $a == 'e' ]]; then
	    (( x -= 3 ))
	    (( y += 3 ))
	    script="$script -draw \"text $x,$y e\""

	fi
    fi
done

echo $script > /tmp/dbg

if [ -n "script" ]; then
    eval convert $script $o $1
else
    mv $o $1
fi
