echo "s cmul epseff epseff_e d31 d31_e" > OUTPUT/results.av
echo "s cmul epseff epseff_e d31 d31_e" > OUTPUT/results.cmul
for dir in s_* 
do 
  s=`echo $dir|cut -f2 -d_|cut -f 1 -d/`   
  nlines=`wc -l $dir/results.dab|cut -f1 -d" "`
  for i in $(seq 2 $[$nlines-1])
  do
    line=`head -$i $dir/results.dab|tail -1`
    echo $s $line >> OUTPUT/results.cmul
  done
  line=`tail -1 $dir/results.dab`
  echo $s $line >> OUTPUT/results.av
done

for dir in s_*
do
  s=`echo $dir|cut -f2 -d_|cut -f 1 -d/`
  nlines=`wc -l $dir/results.data|cut -f1 -d" "`
  for i in $(seq 2 $[$nlines-1])
  do
    line=`head -$i $dir/results.data|tail -1`
    echo $s $line >> OUTPUT/results.cmul
  done
  line=`tail -1 $dir/results.data`
  echo $s $line >> OUTPUT/results.av
done


tar cfz OUTPUT/log.tar.gz *.dat *.dab s_* && rm -r *.dat s_*

perl -p -i -e s/0/0./ OUTPUT/results.*
#gnuplot EXE/eps_d31.plt
