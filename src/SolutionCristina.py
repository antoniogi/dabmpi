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

from SolutionBase import SolutionBase
import Utils as u
from CristinaData import CristinaData


class SolutionCristina (SolutionBase):
    def __init__(self, infile):
        SolutionBase.__init__(self, infile)
        #TODO: Implemement how data is initialized
        self.__data = CristinaData()
        self.__data.initialize(infile)
        return

    def initialize(self, data):
        self.__data = data
        return

    def prepare(self, filename):
        return
#        self.__data.create_input_file(filename)

    def getNumberofParams(self):
        return self.__data.getNumParams()

    def getMaxNumberofValues(self):
        return self.__data.getMaxRange()

    def getParameters(self):
        return self.__data.getParameters()

    def getParametersValues(self):
        return self.__data.getValsOfParameters()

    def setParametersValues(self, buff):
        self.__data.setValsOfParameters(buff)

    def setParameters(self, params):
        self.__data.setParameters(params)

    def getData(self):
        return self.__data

    def print(self):
        self.__data.printData()
