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
__version__ = ' REVISION:   2.0  -  25-05-2026'

"""
HISTORY
    Version 0.1 (12-04-2013): Creation of the file.
    Version 0.11(17-10-2013): Assign default values if there are problems
                              reading the command arguments.
    Version 1.0 (15-01-2014): First stable version.

To run this file just type in mpirun -np X python disop.py
where X is the number of processes to be used
"""

PROBLEM_MAP = {
    'FUSION': util.problem_type.FUSION,
    'CRISTINA': util.problem_type.CRISTINA,
    'NONSEPARABLE': util.problem_type.NONSEPARABLE
}

SOLVER_MAP = {
    'DAB': util.solver_type.DAB,
    'SA': util.solver_type.SA
}

# Configuration file constants
CONFIG_SECTION_GENERAL = "General"
CONFIG_SECTION_ALGORITHM = "Algorithm"
CONFIG_KEY_COMM_MODEL = "commModel"
CONFIG_KEY_OBJECTIVE = "objective"


def create_solver(solver_type, problem_type, inputfile, configfile):
    """Factory function to create the appropriate solver instance."""
    solver_class = SOLVER_MAP.get(solver_type, SolverBase)
    return solver_class(problem_type, inputfile, configfile)


# This function checks if the file exists
def is_valid_file(parser, arg):
    if not os.path.exists(arg):
        parser.error(f"The file {arg} does not exist!")
        return None
    return arg

def init(cfile):
    """
    Initialize the global configuration and logging system.
    
    Args:
        cfile (str): Path to the INI configuration file
        
    Raises:
        FileNotFoundError: If configuration file doesn't exist
        configparser.Error: If configuration file is malformed
    """
    # Setup logging
    util.logger = logging.getLogger('disop')
    util.logger.setLevel(logging.DEBUG)
    
    # File handler
    fh = logging.FileHandler('disop.log')
    fh.setLevel(logging.DEBUG)
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.WARNING)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    
    util.logger.addHandler(fh)
    util.logger.addHandler(ch)
    logging.addLevelName(util.extraLog, "BEST")
    
    # Set defaults
    util.commModel = util.commModelType.DRIVERWORKER
    util.objective = util.objectiveType.MINIMIZE  # Add default
    util.cfile = cfile
    
    # Load configuration
    try:
        config = configparser.ConfigParser()
        config.read(cfile)
        
        # Parse communication model
        if config.has_option(CONFIG_SECTION_GENERAL, CONFIG_KEY_COMM_MODEL):
            val = config.get(CONFIG_SECTION_GENERAL, CONFIG_KEY_COMM_MODEL)
            if val and val.upper() == "DRIVERWORKER":
                util.commModel = util.commModelType.DRIVERWORKER
            elif val:
                util.commModel = util.commModelType.ALL2ALL
        
        # Parse objective
        if config.has_option(CONFIG_SECTION_ALGORITHM, CONFIG_KEY_OBJECTIVE):
            val = config.get(CONFIG_SECTION_ALGORITHM, CONFIG_KEY_OBJECTIVE)
            if val and val.lower() == "max":
                util.objective = util.objectiveType.MAXIMIZE
            elif val:
                util.objective = util.objectiveType.MINIMIZE
                
    except FileNotFoundError:
        util.logger.warning(
            f"Configuration file not found: {cfile}. "
            "Using defaults."
        )
    except configparser.Error as e:
        util.logger.warning(f"Error parsing configuration file: {e}. Using defaults.")

# Main function
def main():
    try:
        parser = argparse.ArgumentParser(
            prog='disop.py',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            description='Distributed Solver for Global Optimization.',
            epilog=textwrap.dedent(__author__))

        parser.add_argument(
            '-p', '--problem',
            required=True,
            type=str,
            choices=list(PROBLEM_MAP.keys()),
            help='Problem type')
        parser.add_argument(
            '-v', '--verbose',
            required=False,
            type=int,
            default=3,
            choices=[1, 2, 3],
            help='Verbosity level')
        parser.add_argument(
            '-s', '--solver',
            required=True,
            type=str,
            choices=list(SOLVER_MAP.keys()),
            help='Solver type')
        parser.add_argument(
            '-i', '--ifile',
            required=True,
            help='input parameters file (an XML file)',
            type=lambda x: is_valid_file(parser, x))
        parser.add_argument(
            '-c', '--cfile',
            required=True,
            help='configuration INI file',
            type=lambda x: is_valid_file(parser, x))
        parser.add_argument(
            '--version',
            action='version',
            version='%(prog)s ' + __version__)

        args = parser.parse_args()

        # Extract types using map dictionaries
        problem_type = PROBLEM_MAP[args.problem]
        solver_type = SOLVER_MAP[args.solver]
        inputfile = args.ifile
        configfile = args.cfile

        # Initialize configuration
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
                solver = create_solver(solver_type, problem_type, inputfile, configfile)
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
            solver = create_solver(solver_type, problem_type, inputfile, configfile)
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
