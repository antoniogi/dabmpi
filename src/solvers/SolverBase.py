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

from abc import ABC, abstractmethod
from core.comms import GlobalComms
from core.runtime import GlobalRuntime
from solution.SolutionsQueue import SolutionsQueue


class SolverBase(ABC):

    def __init__(self, runtime: GlobalRuntime, comms: GlobalComms):
        self._runtime = runtime
        self._comms = comms
        self._finishedSolutions = SolutionsQueue(runtime, "finished.queue", True, True)
        self._pendingSolutions = SolutionsQueue(runtime, "pending.queue", False)
        self._topSolutions = SolutionsQueue(runtime, "top.queue", False, True)
        return

    @abstractmethod
    def initialize(self):
        pass
    
    @abstractmethod
    def solve(self):
        pass

    @abstractmethod
    def finish(self):
        pass
