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
Objects of this class will represent an instance of the problem we want to
solve. In the case of fusion, it contains the information regarding one
stellarator's configuration.

The solve method will use the information to actually solve the instance
(i.e. call VMEC or any other code)
"""

from ProblemBase import ProblemBase
from VMECProcess import VMECProcess
import Utils as u
import sys


class ProblemFusion (ProblemBase):

    def __init__(self):
        try:
            ProblemBase.__init__(self)
            self.__vmec = VMECProcess(u.cfile)
        except Exception, e:
            print("ProblemFusion " + str(sys.exc_traceback.tb_lineno) +
                   " " + str(e))
        return

    """
    Creates a input.tj input file for vmec
    """

    def create_input_file(self, solution):
        try:
            if (not self.__vmec.create_input_file(solution)):
                return False
        except Exception, e:
            u.logger.error("ProblemFusion, when creating input file: " +
                            str(e))
            return False
        return True

    """
    Main method responsible for calling vmec and all of the other
    applications required based on the configuration specified by the user
    """

    def execute_configuration(self):
        return (self.__vmec.execute_configuration())

    def extractSolution(self):
        u.logger.debug("Extract solution fusion")
        """
        This function actually only needs to send back the values we need
        """
        return self.__beta, self.__bgradbval

    def solve(self, solution):
        self.create_input_file(solution)
        value = self.execute_configuration()
        solution.setValue(value)
        u.logger.debug("Solve Problem Fusion")

    def finish(self):
        u.logger.debug("Finish Problem Fusion")
