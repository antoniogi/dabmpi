#PBS -l nodes=1:ppn=1
#PBS -l walltime=50:00:00

cd $PBS_O_WORKDIR
mpirun -np 1 -machinefile ${PBS_NODEFILE} ../EXE/xdkes_100 ddkes2.data
../EXE/calcula_ripple.x
