#!/usr/bin/env python

import argparse
import configparser
import logging
import sys
import time
from array import array
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as package_version
from pathlib import Path

from mpi4py import MPI

from core.comms import GlobalComms
from core.enums import CommModelType, ObjectiveType, ProblemType, SolverType
from core.logging import LoggerConfig
from core.runtime import GlobalRuntime
from runtime.EvaluationWorker import EvaluationWorker
from solvers.SolverDAB import SolverDAB
from solvers.SolverSA import SolverSA

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


def create_solver(runtime, comms):
    """Factory function to create the appropriate solver instance."""
    try:
        solver_class = SOLVER_MAP[runtime.solver_type]
    except KeyError as e:
        raise ValueError(
            f"Invalid solver type: {runtime.solver_type}"
        ) from e
    return solver_class(runtime, comms)


# This function checks if the file exists
def is_valid_file(parser, arg) -> str:
    path = Path(arg)
    if not path.is_file():
        parser.error(f"File does not exist: {arg}")
    return str(path)




def get_package_version():
    try:
        return package_version('dabmpi')
    except PackageNotFoundError:
        return 'unknown'

def parse_arguments(argv=None) -> argparse.Namespace:
    """Parse command-line arguments and return the namespace."""
    parser = argparse.ArgumentParser(
        prog='disop.py',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='Distributed Solver for Global Optimization.',
        epilog='Distributed Solver for Global Optimization.'
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
        '-m', '--mock',
        action='store_true',
        required=False,
        default=False,
        help='Run in mock mode without executing actual problem evaluations'
    )
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s ' + get_package_version()
    )

    return parser.parse_args(argv)


def configure_runtime(runtime: GlobalRuntime, args) -> None:
    """Apply parsed CLI values to runtime and initialize config."""
    problem_type = PROBLEM_MAP[args.problem]
    solver_type = CLI_SOLVER_MAP[args.solver]

    bootstrap_runtime(args.cfile, runtime, args.verbose)

    runtime.problem_type = problem_type
    runtime.solver_type = solver_type
    runtime.config_file = args.cfile
    runtime.input_file = args.ifile
    runtime.max_execution_time = args.time
    runtime.mock = args.mock

    if runtime.logger is not None:
        runtime.logger.setLevel(LOG_LEVELS[args.verbose])


def create_mpi_comms() -> GlobalComms:
    """Create the MPI communicator wrapper used by the runtime."""
    comm = MPI.COMM_WORLD
    return GlobalComms(comm.Get_rank(), comm.Get_size(), comm)


def run_driver(runtime: GlobalRuntime, global_comms: GlobalComms) -> None:
    """Run the driver-side MPI execution path."""
    runtime.logger.info("DRIVER - BEGIN OF THE EXECUTION")
    solver = create_solver(runtime, global_comms)
    solver.initialize()
    solver.solve()
    runtime.logger.info("DRIVER has finished solve")
    solver.finish()
    runtime.logger.info("DRIVER - END OF THE EXECUTION")


def run_worker(runtime: GlobalRuntime, global_comms: GlobalComms) -> None:
    """Run the worker-side MPI execution path."""
    runtime.logger.info(f"WORKER {global_comms.rank} - BEGIN OF THE EXECUTION")
    worker = EvaluationWorker(runtime, global_comms)
    worker.run()
    worker.finish()
    runtime.logger.info(f"WORKER {global_comms.rank} - END OF THE EXECUTION")


def run_all2all(runtime: GlobalRuntime, global_comms: GlobalComms) -> None:
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
        configure_runtime(runtime, args)

        global_comms = create_mpi_comms()

        if global_comms.rank == 0:
            runtime.logger.info(f"Verbosity level: {args.verbose}")

        if runtime.comm_model == CommModelType.DRIVERWORKER:
            if global_comms.rank == 0:
                run_driver(runtime, global_comms)
            else:
                run_worker(runtime, global_comms)
        else:
            run_all2all(runtime, global_comms)

        dump = array('i', [0]) * 1
        global_comms.comm.Bcast(dump)
    except Exception:
        if getattr(runtime, "logger", None):
            runtime.logger.exception("Exception in main execution")
        else:
            print("Exception in main execution")
        raise

if __name__ == "__main__":
    runtime = GlobalRuntime()
    try:
        main(runtime)
    except Exception:
        if getattr(runtime, "logger", None):
            runtime.logger.exception("Fatal error in main execution")
        else:
            print("Fatal error in main execution")
        sys.exit(1)
