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
    Version 0.1 (17-04-2013):   Creation of the file.
    Version 1.0 (15-01-2014):   Fist stable version.
    Version 1.1 (15-11-2024):   Minor change
"""

from solution.SolutionBase import SolutionBase
from data.CristinaData import CristinaData


class SolutionCristina (SolutionBase):
    def __init__(self, runtime, comms):
        SolutionBase.__init__(self, runtime, comms)
        #TODO: Implemement how data is initialized
        self._data = CristinaData(runtime)
        self._data.initialize(runtime.input_file)
        return

    def initialize(self, data):
        self._data = data
        return

    def prepare(self, filename) -> bool:
        return True

    def getNumberofParams(self):
        return self._data.getNumParams()

    def getMaxNumberofValues(self):
        return self._data.getMaxRange()

    def getParameters(self):
        return self._data.getParameters()

    def getParametersValues(self):
        return self._data.getValsOfParameters()

    def setParametersValues(self, buff):
        self._data.setValsOfParameters(buff)

    def setParameters(self, params):
        self._data.setParameters(params)

    def getData(self):
        return self._data

    def print(self):
        self._data.printData()
