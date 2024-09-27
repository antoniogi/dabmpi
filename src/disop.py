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


__version__ = ' REVISION:   1.0  -  15-01-2014'

"""
HISTORY
    Version 0.1 (12-04-2013): Creation of the file.
    Version 0.11(17-10-2013): Assign default values if there are problems
                              reading the command arguments.
    Version 1.0 (15-01-2014):   Fist stable version.
"""

"""
To run this file just type in mpirun -np X python disop.py
where X is the number of processes to be used
"""

from SolverDAB import SolverDAB
from SolverSA import SolverSA
from SolverBase import SolverBase
from Slave import Slave
import Utils as util
import logging
import sys
import os.path
from array import array
import configparser

import argparse

import textwrap
from mpi4py import MPI


def is_valid_file(parser, arg):
    if not os.path.exists(arg):
        parser.error("The file %s does not exist!" % arg)
    else:
        return arg


def init(cfile):
    # create logger with 'disop'
    util.logger = logging.getLogger('disop')
    util.logger.setLevel(logging.DEBUG)

    #default model    
    util.commModel = util.commModelType.MASTERSLAVE

    # create file handler which logs even debug messages

    #filenametime = strftime("%Y%m%d-%H%M%S", localtime())
    #fh = logging.FileHandler('disop-'+str(filenametime)+'.log')

    fh = logging.FileHandler('disop.log')
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
    logging.addLevelName(util.extraLog, "BEST")

    util.cfile = cfile
    config = configparser.ConfigParser()
    config.read(cfile)
    if (config.has_option("General", "commModel")):
        val = config.get("General", "commModel")
        if (val != None):
            if (val == "MASTERSLAVE"):
                util.commModel = util.commModelType.MASTERSLAVE
            else:
                util.commModel = util.commModelType.ALL2ALL
    if (config.has_option("Algorithm", "objective")):
        val = config.get("Algorithm", "objective")
        if (val != None):
            if (val == "max"):
                util.objective = util.objectiveType.MAXIMIZE
            else:
                util.objective = util.objectiveType.MINIMIZE


def main(argv):
    #default values
    try:
        inputfile = "../data/param_config.xml"
        configfile = "../data/DABConfigFile"
        probType = util.problemType.FUSION
        solverType = util.solverType.DAB
        #verbose = 4, prints debug messages. 3 prints info messages.
        #2 prints warnings, 1 prints only errors
        verboseLevel = 4

        #process the arguments if the argparse module has been found
        parser = argparse.ArgumentParser(prog='disop.py',
             formatter_class=argparse.RawDescriptionHelpFormatter,
             description='Distributed Solver for Global Optimization.',
             epilog=textwrap.dedent(__author__))

        parser.add_argument('-p', '--problem', required=True, type=str,
                            default='FUSION',
                            choices=['FUSION', 'NONSEPARABLE'],
                            help='Problem type')
        parser.add_argument('-v', '--verbose', required=False, type=int,
                            default=3, choices=[1, 2, 3, 4],
                            help='Verbosity')
        parser.add_argument('-s', '--solver', required=True, type=str,
                            default='DAB',
                            choices=['DAB', 'SA'],
                            help='Solver type')
        parser.add_argument('-i', '--ifile', required=True,
                            help='input parameters file (an XML file)',
                            type=lambda x: is_valid_file(parser, x))
        parser.add_argument('-c', '--cfile', required=True,
                            help='configuration INI file',
                            type=lambda x: is_valid_file(parser, x))
        parser.add_argument('--version', action='version',
                             version='%(prog)s ' + __version__)

        args = parser.parse_args()

        #extract the problem type
        if (args.problem == 'FUSION'):
            probType = util.problemType.FUSION
        if (args.problem == 'NONSEPARABLE'):
            probType = util.problemType.NONSEPARABLE

        #extract the solver type
        if (args.solver == 'DAB'):
            solverType = util.solverType.DAB
        if (args.solver == 'SA'):
            solverType = util.solverType.SA

        verboseLevel = args.verbose

        #input and config file
        inputfile = args.ifile
        configfile = args.cfile


        #init he configuration
        init(configfile)

        #init MPI
        rank = MPI.COMM_WORLD.Get_rank()
        comm = MPI.COMM_WORLD
        util.rank = rank
        util.comm = comm
        util.size = comm.Get_size()

        #set the verbosity level
        if (rank == 0):
            util.logger.info("Verbose level: " + str(verboseLevel))
        if (verboseLevel == 1):
            logging.disable(logging.WARNING)
        if (verboseLevel == 2):
            logging.disable(logging.INFO)
        if (verboseLevel == 3):
            logging.disable(logging.DEBUG)

        if (util.commModel == util.commModelType.MASTERSLAVE):
            if (rank == 0):
                #create master task
                util.logger.info("MASTER - BEGIN OF THE EXECUTION")
                #create the solver
                if (solverType == util.solverType.DAB):
                    solver = SolverDAB(probType, inputfile, configfile)
                elif (solverType == util.solverType.SA):
                    solver = SolverSA(probType, inputfile, configfile)
                else:
                    solver = SolverBase(probType, inputfile, configfile)
                #initialize the solver
                solver.initialize()
                #execute the solver
                solver.solve()
                util.logger.info("MASTER has finished solve")
                #clean everything
                solver.finish()
                util.logger.info("MASTER - END OF THE EXECUTION")
            else:
                #create slave task
                util.logger.info("SLAVE " + str(rank) +
                                 " - BEGIN OF THE EXECUTION")
                slave = Slave(comm, probType)
                slave.run(inputfile, configfile)
                slave.finish()
                util.logger.info("SLAVE " + str(rank) + " - END OF THE EXECUTION")
        else:
            util.logger.info("ALL2ALL - BEGIN OF THE EXECUTION")
            #create the solver
            if (solverType == util.solverType.DAB):
                solver = SolverDAB(probType, inputfile, configfile)
            elif (solverType == util.solverType.SA):
                solver = SolverSA(probType, inputfile, configfile)
            else:
                solver = SolverBase(probType, inputfile, configfile)
            #initialize the solver
            solver.initialize()
            #execute the solver
            solver.solve()
            util.logger.info("Rank " + str(rank) + " has finished solve")
            #clean everything
            solver.finish()
            util.logger.info("RANK " + str(rank) + " END OF THE EXECUTION")
            
        dump = array('i', [0]) * 1
        util.comm.Bcast(dump)
    except Exception as e:
        print("disop " + str(sys.exc_traceback.tb_lineno) + " " + str(e))

if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
