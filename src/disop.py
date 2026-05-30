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
from runtime.Worker import Worker


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


def parse_arguments(argv=None):
    """Parse command-line arguments and update runtime configuration."""
    parser = argparse.ArgumentParser(
        prog='disop.py',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='Distributed Solver for Global Optimization.',
        epilog=textwrap.dedent(__author__)
    )

    parser.add_argument(
        '-p', '--problem',
        required=True,
        type=str,
        choices=list(PROBLEM_MAP.keys()),
        help='Problem type'
    )
    parser.add_argument(
        '-v', '--verbose',
        required=False,
        type=int,
        default=2,
        choices=[1, 2, 3],
        help='Verbosity level'
    )
    parser.add_argument(
        '-s', '--solver',
        required=True,
        type=str,
        choices=list(CLI_SOLVER_MAP.keys()),
        help='Solver type'
    )
    parser.add_argument(
        '-i', '--ifile',
        required=True,
        help='input parameters file (an XML file)',
        type=lambda x: is_valid_file(parser, x)
    )
    parser.add_argument(
        '-c', '--cfile',
        required=True,
        help='configuration INI file',
        type=lambda x: is_valid_file(parser, x)
    )
    parser.add_argument(
        '-t', '--time',
        required=False,
        type=int,
        default=3600,
        help='max execution time (in seconds)'
    )
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s ' + __version__
    )

    return parser.parse_args(argv)


def configure_runtime(runtime: GlobalRuntime, args):
    """Apply parsed CLI values to runtime and initialize config."""
    problem_type = PROBLEM_MAP[args.problem]
    solver_type = CLI_SOLVER_MAP[args.solver]

    bootstrap_runtime(args.cfile, runtime, args.verbose)

    runtime.problem_type = problem_type
    runtime.solver_type = solver_type
    runtime.config_file = args.cfile
    runtime.input_file = args.ifile
    runtime.max_execution_time = args.time

    if runtime.logger is not None:
        runtime.logger.setLevel(LOG_LEVELS[args.verbose])

    return problem_type, solver_type


def create_mpi_comms():
    """Create the MPI communicator wrapper used by the runtime."""
    comm = MPI.COMM_WORLD
    return GlobalComms(comm.Get_rank(), comm.Get_size(), comm)


def run_driver(runtime: GlobalRuntime, global_comms: GlobalComms):
    """Run the driver-side MPI execution path."""
    runtime.logger.info("DRIVER - BEGIN OF THE EXECUTION")
    solver = create_solver(runtime, global_comms)
    solver.initialize()
    solver.solve()
    runtime.logger.info("DRIVER has finished solve")
    solver.finish()
    runtime.logger.info("DRIVER - END OF THE EXECUTION")


def run_worker(runtime: GlobalRuntime, global_comms: GlobalComms, inputfile: str, configfile: str):
    """Run the worker-side MPI execution path."""
    runtime.logger.info(f"WORKER {global_comms.rank} - BEGIN OF THE EXECUTION")
    worker = Worker(runtime, global_comms)
    worker.run()
    worker.finish()
    runtime.logger.info(f"WORKER {global_comms.rank} - END OF THE EXECUTION")


def run_all2all(runtime: GlobalRuntime, global_comms: GlobalComms):
    """Run the ALL2ALL execution path."""
    runtime.logger.info("ALL2ALL - BEGIN OF THE EXECUTION")
    solver = create_solver(runtime, global_comms)
    solver.initialize()
    solver.solve()
    runtime.logger.debug(f"Rank {global_comms.rank} has finished solve")
    solver.finish()
    runtime.logger.info(f"RANK {global_comms.rank} - END OF THE EXECUTION")


def bootstrap_runtime(cfile: str, runtime: GlobalRuntime, verbose: int) -> None:
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
def main(runtime, argv=None):
    args = parse_arguments(argv)
    try:
        problem_type, _ = configure_runtime(runtime, args)
        inputfile = args.ifile
        configfile = args.cfile

        global_comms = create_mpi_comms()

        if global_comms.rank == 0:
            runtime.logger.info(f"Verbosity level: {args.verbose}")

        if runtime.comm_model == CommModelType.DRIVERWORKER:
            if global_comms.rank == 0:
                run_driver(runtime, global_comms)
            else:
                run_worker(runtime, global_comms, inputfile, configfile)
        else:
            run_all2all(runtime, global_comms)

        dump = array('i', [0]) * 1
        global_comms.comm.Bcast(dump)
    except Exception as e:
        # Extract the last frame of the traceback (where the error actually happened)
        tb = e.__traceback__
        if tb is not None:
            summary = traceback.extract_tb(tb)[-1]
            filename = summary.filename
            line_number = summary.lineno
        else:
            filename = "unknown"
            line_number = 0

        if getattr(runtime, "logger", None):
            runtime.logger.error(f"Exception in file {filename} at line {line_number}: {e}")
        else:
            print(f"Exception in file {filename} at line {line_number}: {e}")

if __name__ == "__main__":
    runtime = GlobalRuntime()
    try:
        main(runtime)
    except Exception as e:
        runtime.logger.exception(f"Fatal error in main execution: {e}")
        """
        import traceback
        if getattr(runtime, "logger", None):
            runtime.logger.error(f"Fatal error: {e}")
            runtime.logger.error(traceback.format_exc())
        else:
            print("Fatal error:", e)
            traceback.print_exc()
        """
        sys.exit(1)
