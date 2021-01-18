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
set grid

# Thick-ish dark green line
set style line 1 \
    linecolor rgb '#008040' \
    linetype 1 linewidth 3

# From this point onwards, details are likely to be per-run,
# i.e. generated on the fly.

set output "graph.png"
set yrange [10:90]
set datafile sep ','
plot "temperature_2021-01-18_192828.log" using 1:6 with lines linestyle 1

