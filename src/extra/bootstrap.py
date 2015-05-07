#!/usr/bin/env python
# vim: set fileencoding=utf-8 :

#############################################################################
#    Copyright 2013  by Antonio Gomez and Miguel Cardenas                   #
#                                                                           #
#   Licensed under the Apache License, Version 2.0 (the "License");         #
#   you may not use this file except in compliance with the License.        #
#   You may obtain a copy of the License at                                 #
#                                                                           #
#       http://www.apache.org/licenses/LICENSE-2.0                          #
#                                                                           #
#   Unless required by applicable law or agreed to in writing, software     #
#   distributed under the License is distributed on an "AS IS" BASIS,       #
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.#
#   See the License for the specific language governing permissions and     #
#   limitations under the License.                                          #
#############################################################################

__author__ = ' AUTHORS:     Antonio Gomez (antonio.gomez@csiro.au)'


__version__ = '0.1 - 06-12-2013'

"""
HISTORY
    Version 0.1 (06-12-2013): Creation of the file.
"""

"""
To run this file just type in python -i bootstrap.py finished.queue
"""

import sys
import os
import os.path
import commands
import getopt
import logging

sys.path.append('../')
from SolutionFusion import SolutionFusion
import Utils as util


def init():
    # create logger with 'dab_mpi'
    util.logger = logging.getLogger('bootstrap')
    util.logger.setLevel(logging.DEBUG)

    # create file handler which logs even debug messages

    fh = logging.FileHandler('bootstrap.log')
    fh.setLevel(logging.DEBUG)
    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.WARNING)
    # create formatter and add it to the handlers
    formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    # add the handlers to the logger
    util.logger.addHandler(fh)
    util.logger.addHandler(ch)
    util.rank = 0

    
def create_bootstrap_folder (index):
    folderName = "bootstrap/"+str(index)
    if not os.path.exists(folderName):
        os.makedirs(folderName)


def create_script_file():
    fout = open("send_bootstrap",'w')
    fout.write ("#!/bin/bash\n")
    fout.write ("#PBS -N bootstrap\n")
    fout.write ("#PBS -e bootstrap.err\n")
    fout.write ("#PBS -o bootstrap.out\n")
    fout.write ("#PBS -m e\n")
    fout.write ("#PBS -M antonio.gomez@csiro.au\n")
    fout.write ("#PBS -l nodes=1:ppn=1\n")
    fout.write ("#PBS -l walltime=1:30:00\n")
    fout.write ("#PBS -l vmem=10GB\n")
    fout.write ("#PBS -V\n")
    fout.write ("cd $PBS_O_WORKDIR\n")
    fout.write ("python remote_bootstrap.py input.tj0")
    fout.close()
    
def main(argv):
    try:
        inputfile = "../finished.queue"
        xmlFile = "../../data/param_config_pressure.xml"

        try:
            opts, args = getopt.getopt(sys.argv[1:], "hi:x:v:", ["help", "ifile", "xfile", "verbose"])
        except getopt.GetoptError, err:
            print str(err)
            return
        for o, val in opts:
            if o in ("-i", "--ifile"):
                inputfile = val
            elif o in ("-x", "--xfile"):
                xmlFile = val
            else:
                assert False, "unhandled option"
    
        solutionBase = SolutionFusion(xmlFile)

        init()
        i = 0
        f = open(inputfile,'r')
        if not os.path.exists("bootstrap"):
            os.makedirs("bootstrap")
        savedPath = os.getcwd()
        
        create_script_file()
        
        for line in f.readlines():
            solTuple = line.split ('#')
            solValue = float (solTuple[1])
            if (solValue<0.0):
                continue
            util.logger.info ("Processing solution " + str(i+1) + " with value " + str(solValue))
            create_bootstrap_folder(i)
            sol = solTuple [0]
            parameters = sol.split(',')
            params = []
            for p in parameters:
                params.append (float (p.split(':')[1]))
            solutionBase.setParametersValues (params)
            solutionBase.getData().create_input_file("bootstrap/"+str(i)+"/input.tj0")
            os.chdir(savedPath+"/bootstrap/"+str(i))
            commands.getoutput ("ln -s " + savedPath + "/remote_bootstrap.py remote_bootstrap.py")
            commands.getoutput ("ln -s " + savedPath + "/send_bootstrap send_bootstrap")

            util.logger.info ("Submitting job")
            commands.getoutput("qsub send_bootstrap")
            os.chdir(savedPath)
            i+=1
        f.close()
    

    except Exception, e:
        print("bootstrap " + str(sys.exc_traceback.tb_lineno)+ " " +str(e))

if __name__ == "__main__":
    main(sys.argv[1:])
