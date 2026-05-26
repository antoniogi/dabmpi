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
from pathlib import Path
import time
from array import array
import configparser
import argparse
import traceback
from mpi4py import MPI
import math
import textwrap
from core.logging import LoggerConfig
from core.runtime import GlobalRuntime
from core.enums import ProblemType, SolverType, CommModelType, ObjectiveType
from core.comms import GlobalComms
from solvers.SolverDAB import SolverDAB
from solvers.SolverSA import SolverSA
from Worker import Worker


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
    'FUSION': ProblemType.FUSION,
    'CRISTINA': ProblemType.CRISTINA,
    'NONSEPARABLE': ProblemType.NONSEPARABLE
}

CLI_SOLVER_MAP = {
    "DAB": SolverType.DAB,
    "SA": SolverType.SA,
}

SOLVER_MAP = {
    SolverType.DAB: SolverDAB,
    SolverType.SA: SolverSA,
}

LOG_LEVELS = {
    1: logging.WARNING,
    2: logging.INFO,
    3: logging.DEBUG,
}

# Configuration file constants
CONFIG_SECTION_GENERAL = "General"
CONFIG_SECTION_ALGORITHM = "Algorithm"
CONFIG_KEY_COMM_MODEL = "commModel"
CONFIG_KEY_OBJECTIVE = "objective"

# Extra value for logging when a new solution has been found
EXTRA_LOG: int = 100

# Numerical infinity approximation
INFINITY: float = math.inf


def create_solver(runtime, comms):
    """Factory function to create the appropriate solver instance."""
    if runtime.solver_type not in SOLVER_MAP:
        raise ValueError(f"Invalid solver type: {runtime.solver_type}")
    solver_class = SOLVER_MAP[runtime.solver_type]
    return solver_class(runtime, comms)


# This function checks if the file exists
def is_valid_file(parser, arg):
    path = Path(arg)
    if not path.is_file():
        parser.error(f"File does not exist: {arg}")
    return str(path)


def init(cfile: str, runtime: GlobalRuntime, verbose: int) -> None:
    """
    Initialize the global configuration and logging system.
    
    Args:
        cfile (str): Path to the INI configuration file
        
    Raises:
        FileNotFoundError: If configuration file doesn't exist
        configparser.Error: If configuration file is malformed
    """
    logger = LoggerConfig.create_logger(
        log_file="disop.log",
        console_level=LOG_LEVELS[verbose]  # Map verbosity to log level
    )
    # Get runtime and update it
    runtime.logger = logger
    runtime.config_file = cfile
    runtime.start_time = time.time()
    runtime.validate()
    runtime.log_configuration()
    runtime.comm_model = CommModelType.DRIVERWORKER  # Set default communication model
    runtime.objective = ObjectiveType.MINIMIZE  # Set default objective
    
    # Load configuration
    try:
        config = configparser.ConfigParser()
        config.read(cfile)
        
        # Parse communication model
        if config.has_option(CONFIG_SECTION_GENERAL, CONFIG_KEY_COMM_MODEL):
            val = config.get(CONFIG_SECTION_GENERAL, CONFIG_KEY_COMM_MODEL)
            if val and val.upper() == "DRIVERWORKER":
                runtime.comm_model = CommModelType.DRIVERWORKER
            elif val:
                runtime.comm_model = CommModelType.ALL2ALL
        
        # Parse objective
        if config.has_option(CONFIG_SECTION_ALGORITHM, CONFIG_KEY_OBJECTIVE):
            val = config.get(CONFIG_SECTION_ALGORITHM, CONFIG_KEY_OBJECTIVE)
            if val and val.lower() == "max":
                runtime.objective = ObjectiveType.MAXIMIZE
            elif val:
                runtime.objective = ObjectiveType.MINIMIZE
                
    except FileNotFoundError:
        logger.warning(
            f"Configuration file not found: {cfile}. "
            "Using defaults."
        )
    except configparser.Error as e:
        logger.warning(f"Error parsing configuration file: {e}. Using defaults.")

# Main function
def main(runtime):
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
            choices=list(CLI_SOLVER_MAP.keys()),
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
            '-t', '--time',
            required=False,
            type=int,
            default=3600,
            help='max execution time (in seconds)')
        parser.add_argument(
            '--version',
            action='version',
            version='%(prog)s ' + __version__)

        args = parser.parse_args()

        # Extract types using map dictionaries
        problem_type = PROBLEM_MAP[args.problem]
        solver_type = CLI_SOLVER_MAP[args.solver]  # Get enum
        solver = SOLVER_MAP[solver_type]     # Get class
        inputfile = args.ifile
        configfile = args.cfile

        # Initialize configuration
        init(configfile, runtime, args.verbose)
        runtime.problem_type = problem_type  # Set problem type in runtime
        runtime.solver_type = solver_type  # Set solver type in runtime
        runtime.config_file = configfile  # Set config file in runtime
        runtime.input_file = inputfile  # Set input file in runtime
        runtime.max_execution_time = args.time  # Set max execution time in runtime

        #init MPI
        rank = MPI.COMM_WORLD.Get_rank()
        size = MPI.COMM_WORLD.Get_size()
        comm = MPI.COMM_WORLD
        global_comms = GlobalComms(rank, size, comm)

        #set the verbosity level
        if rank == 0:
            runtime.logger.info(f"Verbosity level: {args.verbose}")
        runtime.logger.setLevel(LOG_LEVELS[args.verbose])

        if runtime.comm_model == CommModelType.DRIVERWORKER:
            if rank == 0:
                #create driver task
                runtime.logger.info("DRIVER - BEGIN OF THE EXECUTION")
                #create the solver
                solver = create_solver(runtime, global_comms)
                #initialize the solver
                solver.initialize()
                #execute the solver
                solver.solve()
                runtime.logger.info("DRIVER has finished solve")
                #clean everything
                solver.finish()
                runtime.logger.info("DRIVER - END OF THE EXECUTION")
            else:
                #create worker task
                runtime.logger.info(f"WORKER {rank} - BEGIN OF THE EXECUTION")
                worker = Worker(comm, problem_type, runtime)
                worker.run(inputfile, configfile)
                worker.finish()
                runtime.logger.info(f"WORKER {rank} - END OF THE EXECUTION")
        else:
            runtime.logger.info("ALL2ALL - BEGIN OF THE EXECUTION")
            #create the solver
            solver = create_solver(runtime.solver_type, runtime.problem_type, runtime.input_file, runtime.config_file)
            #initialize the solver
            solver.initialize()
            #execute the solver
            solver.solve()
            runtime.logger.debug(f"Rank {rank} has finished solve")
            #clean everything
            solver.finish()
            runtime.logger.info(f"RANK {rank} - END OF THE EXECUTION")

        dump = array('i', [0]) * 1
        global_comms.comm.Bcast(dump)
    except Exception as e:
        # Extract the last frame of the traceback (where the error actually happened)
        tb = e.__traceback__
    
        # extract_tb returns a list of FrameSummary objects
        summary = traceback.extract_tb(tb)[-1]
    
        filename = summary.filename
        line_number = summary.lineno
        runtime.logger.error(f"Exception in file {filename} at line {line_number}: {e}")

if __name__ == "__main__":
    runtime = GlobalRuntime()
    try:
        main(runtime)
    except Exception as e:
        import traceback
        if runtime.logger:
            runtime.logger.error(f"Fatal error: {e}")
            runtime.logger.error(traceback.format_exc())
        else:
            print("Fatal error:", e)
        sys.exit(1)
