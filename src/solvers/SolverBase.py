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

__author__ = ' AUTHORS:     Antonio Gomez'


__version__ = ' REVISION:   2.0  -  28-05-2026'

"""
HISTORY
    Version 0.1 (12-04-2013):   Creation of the file.
    Version 1.0 (15-01-2014):   First stable version.
    Version 2.0 (28-05-2026):   Refactor to use GlobalRuntime and GlobalComms, and to define the lifecycle protocol for solvers.
"""

from abc import ABC, abstractmethod
from core.comms import GlobalComms
from core.runtime import GlobalRuntime
from solution.SolutionsQueue import SolutionsQueue


class SolverBase(ABC):
    """
    Abstract base class for all solver implementations.

    Defines the solver lifecycle (initialize, solve, finish) and
    provides common solution queues used for distributed execution.
    """
    def __init__(self, runtime: GlobalRuntime, comms: GlobalComms):
        self._runtime: GlobalRuntime = runtime
        self._comms: GlobalComms = comms

        self._finishedSolutions: SolutionsQueue = SolutionsQueue(
            runtime, comms, "finished.queue", writeToFile=True, isPriority=True
            )
        self._pendingSolutions: SolutionsQueue = SolutionsQueue(
            runtime, comms, "pending.queue", writeToFile=False
            )
        self._topSolutions: SolutionsQueue = SolutionsQueue(
            runtime, comms, "top.queue", writeToFile=False, isPriority=True
            )

    @abstractmethod
    def initialize(self) -> None:
        ...
    
    @abstractmethod
    def solve(self) -> None:
        ...

    @abstractmethod
    def finish(self) -> None:
        ...
