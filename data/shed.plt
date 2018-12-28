set terminal png #size 1000, 1000
#set style data lines
set timefmt "%d/%m/%Y_%H:%M:%S"
set xdata time
set xlabel "Time"
set format x "%H:%M"
set ylabel "Temperature °C"
set title "Shed Temperature"
set grid
set output "graph.png"
unset key
plot "temperature.txt" using 1:5

