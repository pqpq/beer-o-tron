# Mash-o-matiC gnuplot script
# https://github.com/pqpq/beer-o-tron

# Command line parameters
# gnuplot -c graph.plt parameters...
# Parameter 1: output file name
# Parameter 2: Temperature axis min value
# Parameter 3: Temperature axis max value
# Parameter 4: Temperature data file name
# Parameter 5: Profile data file name

if (ARGC < 5) exit

OUTPUT=ARG1
LOW=ARG2
HI=ARG3
DATA=ARG4
PROFILE=ARG5


# Fixed format & 'style' commands

set terminal png size 320,240

set key autotitle columnhead  # consume first row, since we 'unset key' later
unset key
set timefmt "%H:%M:%S"        # so it understands our time values
set xdata time
set xtic auto
set xtics format ""           # turn off labels
set ytic 10
set ytics right offset 1,0    # right justify, close to axis
set grid

set tmargin 1.25         # this just clears the status icons
set bmargin 0.5          # close to the edge
set lmargin 2.5          # space for 2 digits of temperature values
set rmargin 0.5          # close to the edge

# Thick-ish dark green line
set style line 1 \
    linecolor rgb '#008040' \
    linewidth 2

set style line 2 \
    linecolor rgb '#800000' \
    linewidth 2


# Output governed by command line parameters:

set output OUTPUT
set yrange [LOW:HI]
set datafile sep ','
plot DATA using 1:2 with lines linestyle 1, \
     PROFILE using 1:2 with lines linestyle 2, \
     DATA using 1:3 with lines lw 1 lt 0 lc "#800000", \
     DATA using 1:4 with lines lw 1 lt 0 lc "#808000", \
     DATA using 1:5 with lines lw 1 lt 0 lc "#008080", \
     DATA using 1:6 with lines lw 1 lt 0 lc "#800080"

