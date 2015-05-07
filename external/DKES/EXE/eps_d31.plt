set xrange [0:1]
set xlabel "(r/a)^2"
set ylabel "effective ripple, bootstrap coefficient"
set grid
p   "OUTPUT/results.cmul" u 1:3:4 w e lt 1 ps 5 title "eff. ripple"
rep "OUTPUT/results.av"   u 1:3:4 w yerrorl lt 1 notitle 
rep "OUTPUT/results.cmul" u 1:5:6 w e lt 3 ps 5 title "d31* coeff."
rep "OUTPUT/results.av"   u 1:5:6 w yerrorl lt 3 notitle 
pause -1 
