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

import logging
import sys
import os.path
from array import array
import configparser
import argparse
from mpi4py import MPI
import textwrap
from SolverDAB import SolverDAB
from SolverSA import SolverSA
from SolverBase import SolverBase
from Worker import Worker
import Utils as util

__author__ = ' AUTHORS:     Antonio Gomez (antonio.gomez@csiro.au)'
__version__ = ' REVISION:   1.0  -  15-01-2014'

"""
HISTORY
    Version 0.1 (12-04-2013): Creation of the file.
    Version 0.11(17-10-2013): Assign default values if there are problems
                              reading the command arguments.
    Version 1.0 (15-01-2014):   Fist stable version.

To run this file just type in mpirun -np X python disop.py
where X is the number of processes to be used
"""


# This function checks if the file exists
def is_valid_file(parser, arg):
    if not os.path.exists(arg):
        parser.error(f"The file {arg} does not exist!")
        return None
    return arg

# This function initializes the configuration
def init(cfile):
    # create logger with 'disop'
    util.logger = logging.getLogger('disop')
    util.logger.setLevel(logging.DEBUG)

    #default model
    util.commModel = util.commModelType.DRIVERWORKER

    # create file handler which logs even debug messages
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
    if config.has_option("General", "commModel"):
        val = config.get("General", "commModel")
        if val is not None:
            if val == "DRIVERWORKER":
                util.commModel = util.commModelType.DRIVERWORKER
            else:
                util.commModel = util.commModelType.ALL2ALL
    if config.has_option("Algorithm", "objective"):
        val = config.get("Algorithm", "objective")
        if val is not None:
            if val == "max":
                util.objective = util.objectiveType.MAXIMIZE
            else:
                util.objective = util.objectiveType.MINIMIZE

# Main function
def main():
    try:
        inputfile = "../data/param_config.xml"
        configfile = "../data/DABConfigFile"
        problem_type = util.problem_type.FUSION
        solver_type = util.solver_type.DAB

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
                            default=3, choices=[1, 2, 3],
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
        if args.problem == 'FUSION':
            problem_type = util.problem_type.FUSION
        if args.problem == 'NONSEPARABLE':
            problem_type = util.problem_type.NONSEPARABLE

        #extract the solver type
        if args.solver == 'DAB':
            solver_type = util.solver_type.DAB
        if args.solver == 'SA':
            solver_type = util.solver_type.SA

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
        if rank == 0:
            util.logger.info(f"Verbosity level: {args.verbose}")
        if args.verbose == 1:
            logging.disable(logging.WARNING)
        elif args.verbose == 2:
            logging.disable(logging.INFO)
        else:
            logging.disable(logging.DEBUG)

        if util.commModel == util.commModelType.DRIVERWORKER:
            if rank == 0:
                #create driver task
                util.logger.info("DRIVER - BEGIN OF THE EXECUTION")
                #create the solver
                if solver_type == util.solver_type.DAB:
                    solver = SolverDAB(problem_type, inputfile, configfile)
                elif solver_type == util.solver_type.SA:
                    solver = SolverSA(problem_type, inputfile, configfile)
                else:
                    solver = SolverBase(problem_type, inputfile, configfile)
                #initialize the solver
                solver.initialize()
                #execute the solver
                solver.solve()
                util.logger.info("DRIVER has finished solve")
                #clean everything
                solver.finish()
                util.logger.info("DRIVER - END OF THE EXECUTION")
            else:
                #create worker task
                util.logger.info(f"WORKER {rank} - BEGIN OF THE EXECUTION")
                worker = Worker(comm, problem_type)
                worker.run(inputfile, configfile)
                worker.finish()
                util.logger.info(f"WORKER {rank} - END OF THE EXECUTION")
        else:
            util.logger.info("ALL2ALL - BEGIN OF THE EXECUTION")
            #create the solver
            if solver_type == util.solver_type.DAB:
                solver = SolverDAB(problem_type, inputfile, configfile)
            elif solver_type == util.solver_type.SA:
                solver = SolverSA(problem_type, inputfile, configfile)
            else:
                solver = SolverBase(problem_type, inputfile, configfile)
            #initialize the solver
            solver.initialize()
            #execute the solver
            solver.solve()
            util.logger.debug(f"Rank {rank} has finished solve")
            #clean everything
            solver.finish()
            util.logger.info(f"RANK {rank} - END OF THE EXECUTION")

        dump = array('i', [0]) * 1
        util.comm.Bcast(dump)
    except Exception as e:
        util.logger.error(f"Exception: {e}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
