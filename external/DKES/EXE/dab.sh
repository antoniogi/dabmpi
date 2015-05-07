# type 'source dab.sh'
# when the DKES runs are finished, type 'source EXE/recoge_res.sh'



threed1_file=INPUT/threed1.DAB_0.0      #NO CAMBIAR
wout_file=wout_DAB_0.0.txt        #NO CAMBIAR  
lista_file=INPUT/s.dab
cmul_file=INPUT/cmul.dab

grep Radius $threed1_file | head -2 | cut -f2 -d=| cut -f 1 -d"(" > temp.1
grep Radius $threed1_file | head -2 | cut -f1 -d= > temp.2
paste temp.1 temp.2 > radius.dat
rm temp.?

bzeta2=`cat $threed1_file | grep " 6.94E-01 "|cut -f21-22 -d" "`
#bzeta2=head -400 $threed1_file|cut -f11-12 -dE|cut -f 3 -d" "|tail -1`
bzeta=`awk -v bzeta2="$bzeta2" 'BEGIN{print (bzeta2 / 2)}'`     
echo $bzeta > bzeta.dat

nr=`wc -l $lista_file | cut -f 1 -d " "`

for ir in $(seq 1 $nr);
do
 dir=`grep s_ $lista_file | head -$ir | tail -1 | cut -f 1 -d "|"`
 jrad=`grep s_ $lista_file | head -$ir | tail -1 | cut -f 2 -d "|"`

 mkdir $dir
 cd $dir

 echo "100 100" > input.boz
 echo $wout_file >> input.boz
 echo $jrad >> input.boz
 cp -p ../INPUT/$wout_file .
 ../EXE/xbooz input.boz
  
 mv $wout_file wout.DAB.0.0.txt
 boozmn_file=boozmn.DAB.0.0.nc
 mv boozmn_* $boozmn_file
 name_boozmn=boozmn.DAB.0.0
 ../EXE/xdkes_100 $name_boozmn $jrad 1.0000 0.0000 T 5 100000

 mv input_dkes.* ddkes2.data
 rm -r wout* boozm* input* dkesout*
 cat ddkes2.data  | grep borbi\(0,0 |cut -f2 -d= > b00.dat
 echo $dir|cut -f2 -d_ > s.dat
 perl -p -i -e s/0/0./ s.dat 

 nrun=`head -1 ../$cmul_file|cut -f1 -d" "`
 cmul=`tail -1 ../$cmul_file|cut -f1 -d" "`
 perl -p -i -e s/"lalpha= \*\*\*"/"lalpha= 200"/  ddkes2.data
 perl -p -i -e s/"bzeta = \*\*\*\*\*\*\*"/"bzeta = $bzeta"/  ddkes2.data 
 perl -p -i -e s/"nrun = 1"/"nrun = $nrun"/  ddkes2.data
 perl -p -i -e s/"cmul =   0.1000E\+01"/"cmul =$cmul"/  ddkes2.data
 
../EXE/./xdkes_100 ddkes2.data
../EXE/./calcula_ripple.x
   
 cd ..
done

echo
