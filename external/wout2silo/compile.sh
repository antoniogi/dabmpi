export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/home/u5494/software/tools/hdf5/lib/
export HDF5LIB=/home/u5494/software/tools/hdf5/lib/
icc main.cpp -I/home/u5494/software/tools/hdf5/include -I/home/u5494/software/tools/silo/include/ -L$HDF5LIB -L/home/u5494/software/tools/silo/lib/ -o vmec2silodirecto -lhdf5 -lsiloh5 -lm /usr/lib64/libstdc++.so.5
