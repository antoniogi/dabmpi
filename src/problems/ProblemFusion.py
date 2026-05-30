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

from problems.ProblemBase import ProblemBase
from data.VMECProcess import VMECProcess

__author__ = ' AUTHORS:     Antonio Gomez (antonio.gomez@csiro.au)'


__version__ = ' REVISION:   2.0  -  29-05-2026'

"""
HISTORY
    Version 0.1 (12-04-2013):   Creation of the file.
    Version 1.0 (15-01-2014):   Fist stable version.
    Version 2.0 (29-05-2026):   Refactor to align with new architecture and coding standards.

Objects of this class will represent an instance of the problem we want to
solve. In the case of fusion, it contains the information regarding one
stellarator's configuration.

The solve method will use the information to actually solve the instance
(i.e. call VMEC or any other code)
"""


class ProblemFusion(ProblemBase):

    def __init__(self, runtime, comms):
        self._vmec: VMECProcess | None = None
        try:
            super().__init__(runtime, comms)
            self._vmec = VMECProcess(runtime, comms)

        except Exception:
            self._runtime.logger.exception("ProblemFusion init failed")
            raise

    def create_input_file(self, solution) -> bool:
        try:
            return self._vmec.create_input_file(solution)
        except Exception:
            self._runtime.logger.exception(
                "ProblemFusion: error creating input file"
            )
            return False

    def execute_configuration(self):
        return self._vmec.execute_configuration()

    def extractSolution(self) -> tuple[float, float]:
        self._runtime.logger.debug("Extract solution fusion")
        return self._vmec.get_beta(), self._vmec.get_bgradbval()

    def solve(self, solution) -> None:
        try:
            self._runtime.logger.debug("Start solving Fusion problem")

            self.create_input_file(solution)
            value = self.execute_configuration()

            solution.setValue(value)

            self._runtime.logger.debug("Finished solving Fusion problem")

        except Exception:
            self._runtime.logger.exception("Error solving Problem Fusion")

    def finish(self) -> None:
        self._runtime.logger.debug("Finish Problem Fusion")
