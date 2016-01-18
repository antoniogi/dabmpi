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
"""
import Utils as util


class SolutionBase (object):
    def __init__(self, infile):
        #initial value of the solution is the min value represented by a float
        if (util.objective == util.objectiveType.MINIMIZE):
            self.__value = util.infinity
        else:
            self.__value = -util.infinity
        self.__value = util.infinity #### REMOVE!!
        self.__isValid = True
        return

    def getValue(self):
        return self.__value

    def setValue(self, value):
        self.__value = value

    def getNumberofParams(self):
        return 0

    def getMaxNumberofValues(self):
        return 0

    def isValid(self):
        return self.__isValid

    def getParametersValues(self):
        raise NotImplementedError("getParametersValues abstract solution")

    def setParametersValues(self, buff):
        raise NotImplementedError("setParametersValues abstract solution")

    def getParameters(self):
        raise NotImplementedError("getParameters abstract solution")

    def setParameters(self, params):
        raise NotImplementedError("setParameters abstract solution")

    def initialize(self, data):
        raise NotImplementedError("initialize abstract solution")

    def prepare(self, filename):
        raise NotImplementedError("prepare abstract solution")
