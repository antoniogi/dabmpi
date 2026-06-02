#!/usr/bin/env python
# vim: set fileencoding=utf-8 :

"""
Class that implements the DAB solver. It has to:
  - Create the different bees.
  - Solve is the main method that actually implements the algorithm
  - Once the algorithm has finish, we have to call the finish method if
  there is something else to be done.
"""

import sys
import random
import configparser
from solvers.SolverBase import SolverBase

class SolverSA (SolverBase):
    def readConfigFile(self, runtime):
        config = configparser.ConfigParser()
        config.read(runtime.config_file)
        if (not config.has_section("SA")):
            runtime.logger.critical("SA section not specified in the ini file")
            sys.exit(-1)

    def __init__(self, problem_type, infile, runtime):
        runtime.logger.info("SolverSA init")
        self.readConfigFile(runtime)
        random.seed()
