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

import Utils as u
import math
import sys

from ProblemBase import ProblemBase

#this will need to be done
#from SolutionNonSeparable import SolutionNonSeparable


class ProblemNonSeparable(ProblemBase):

    def initialize(self):
        u.logger.info("Initialize Problem NonSeparable")

    #this implements Rosenbrock's Function
    def solve(self, solution):
        try:
            parameters = solution.getParametersValues()
            val = 0.0
            for i in range(0, len(parameters) - 1):
                val += (100 * (math.pow((math.pow(parameters[i], 2) -
                              parameters[i + 1]), 2)) +
                              math.pow(parameters[i] + 1, 2))
            solution.setValue(val)
            u.logger.debug("Solve Problem NonSeparable")
        except Exception, e:
            u.logger.error("ProblemNonSeparable (" +
                            str(sys.exc_traceback.tb_lineno) +
                            "). " + str(e))

    def finish(self):
        u.logger.info("Finish Problem NonSeparable")
