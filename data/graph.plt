# Mash-o-matiC gnuplot script
# https://github.com/pqpq/beer-o-tron

# Fixed format & 'style' commands

set terminal png size 320,240
#set style data lines
set key autotitle columnhead	# consume first row, since we 'unset key' later
unset key
set timefmt "%H:%M:%S"		# so it understands our time values
set xdata time
#set xlabel "Time"
#set format x "%H:%M"
#set ylabel "Temperature °C"
#set title "Shed Temperature"
set xtic auto                          # set xtics automatically
set xtics format ""		# turn off labels
#set ytic auto                          # set ytics automatically
set ytic 20
set ytics right offset 1,0
set grid

# set tmargin 1.75 # this clears the temperature readout nicely
set tmargin 1.25	# this just clears the status icons
set bmargin 0.5
set lmargin 2.5
set rmargin 0.5

# Thick-ish dark green line
set style line 1 \
    linecolor rgb '#008040' \
    linewidth 3

set style line 2 \
    linecolor rgb '#800000' \
    linewidth 2

# From this point onwards, details are likely to be per-run,
# i.e. generated on the fly.

set output "graph.png"
set yrange [10:90]
set datafile sep ','
plot "temperature_2021-01-18_192828.log" using 1:6 with lines linestyle 1, \
     "profile.txt" using 1:2 with lines linestyle 2, \
     "temperature_2021-01-18_192828.log" using 1:2 with lines lw 1 lt 0 lc "#800000", \
     "temperature_2021-01-18_192828.log" using 1:3 with lines lw 1 lt 0 lc "#808000", \
     "temperature_2021-01-18_192828.log" using 1:4 with lines lw 1 lt 0 lc "#008080", \
     "temperature_2021-01-18_192828.log" using 1:5 with lines lw 1 lt 0 lc "#800080"

