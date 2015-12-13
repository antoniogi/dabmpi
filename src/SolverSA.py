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
    Version 0.1 (12-04-2013):   Creation of the file.
    Version 1.0 (15-01-2014):   Fist stable version.
"""

"""
Class that implements the DAB solver. It has to:
  - Create the different bees.
  - Solve is the main method that actually implements the algorithm
  - Once the algorithm has finish, we have to call the finish method if
  there is something else to be done.
"""


import sys
import random
import shutil
import time

from mpi4py import MPI
from array import array


from SolverBase import SolverBase
from ProblemFusion import ProblemFusion
from ProblemNonSeparable import ProblemNonSeparable
from SolutionFusion import SolutionFusion
from SolutionNonSeparable import SolutionNonSeparable
import Utils as u
import ConfigParser
import SolutionsQueue as solQueue


class SolverSA(SolverBase):
    def readConfigFile(self, configfile):
        config = ConfigParser.ConfigParser()
        config.read(configfile)
        if (not config.has_section("SA")):
            u.logger.critical("SA section not specified in the ini file")
            sys.exit(-1)

    def __init__(self, problemType, infile, configfile):
        u.logger.info("SolverSA init")
        self.readConfigFile(configfile)
        u.starttime = time.time()
        u.comm = MPI.COMM_WORLD
        u.rank = u.comm.Get_rank()
        u.size = u.comm.Get_size()
        random.seed()
