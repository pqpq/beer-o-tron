# Mash-o-matiC gnuplot script
# https://github.com/pqpq/beer-o-tron

# Command line parameters
# gnuplot -c graph.plt parameters...
# Parameter 1: output file name
# Parameter 2: Temperature axis min value
# Parameter 3: Temperature axis max value
# Parameter 4: Time axis start value
# Parameter 5: Temperature data file name
# Parameter 6: Profile data file name
# Parameter 7: State data file name

if (ARGC < 7) exit

OUTPUT=ARG1
LOW=ARG2
HI=ARG3
XSTART=ARG4
DATA=ARG5
PROFILE=ARG6
STATE=ARG7


# Fixed format & 'style' commands

set terminal png size 320,240

set key autotitle columnhead  # consume first row, since we 'unset key' later
unset key
set timefmt "%H:%M:%S"        # so it understands our time values
set xdata time
set xtics format ""           # turn off labels
set ytic 10
set ytics right offset 1,0    # right justify, close to axis
set grid

set y2range [0:5]
set y2tic 10
set y2tics format ""


set tmargin 1.25         # this just clears the status icons
set bmargin 0.5          # close to the edge
set lmargin 2.5          # space for 2 digits of temperature values
set rmargin 0.5          # close to the edge

# Style for the live temperature curve
set style line 1 \
    linecolor rgb '#000000' \
    linewidth 2

# Style for the uncompleted part of the profile
set style line 2 \
    linecolor rgb '#804000' \
    linewidth 2

# Style for the completed part of the profile
set style line 3 \
    linecolor rgb '#008040' \
    linewidth 3


# Output governed by command line parameters:

set output OUTPUT
set yrange [LOW:HI]
set xrange [XSTART:]
set xtics XSTART,60*10                # 10 minutes

set datafile sep ','
plot STATE using 1:3 with filledcurve above x1 lc "#ff9900" axes x1y2, \
     DATA using 1:2 with lines linestyle 1, \
     PROFILE using 1:2 with lines linestyle 2, \
     STATE using 1:2 with lines linestyle 3
