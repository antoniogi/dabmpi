#!/bin/bash
if [ $# -ne 3 ]; then
echo "Wrong parameter number"
echo $0 Surfaces_number Input_file_name Output_file_name
else
if [ -e $3 ]; then
	echo "A file with the same name already exists. It's going to be removed."
	rm -rf $3
fi
echo $1 > cmd
echo $2 >> cmd
echo $3 >> cmd
echo "1" >> cmd
echo "y" >> cmd
./wout2flx < cmd
rm cmd
fi
