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

__version__ = ' REVISION:   2.0  -  23-05-2026'

"""
HISTORY
    Version 0.1 (17-04-2013):   Creation of the file.
    Version 1.0 (15-01-2014):   First stable version.
    Version 2.0 (23-05-2026):   Refactoring and modernization
"""

from solution.SolutionBase import SolutionBase
from VMECData import VMECData

# Range for polynomial derivative check
DERIVATIVE_CHECK_RANGE = range(-100, 100)


class SolutionFusion(SolutionBase):
    def __init__(self,runtime):
        super().__init__(runtime)
        self._data = VMECData(runtime)
        self._data.initialize(runtime.input_file)

    def initialize(self, data):
        """Initialize with external data object."""
        self._data = data

    def prepare(self, filename):
        """Create input file for VMEC."""
        self._data.create_input_file(filename)

    def get_number_of_params(self):
        """Return the number of parameters."""
        return self._data.getNumParams()

    def getMaxNumberofValues(self):
        """Return the maximum range of parameter values."""
        return self._data.getMaxRange()

    def getParameters(self):
        """Return the parameters."""
        return self._data.getParameters()

    def getParametersValues(self):
        """Return the current values of all parameters."""
        return self._data.getValsOfParameters()

    def setParametersValues(self, buff):
        """Set parameter values from a float array.
        
        Args:
            buff: Array of float values for parameters
        """
        self._runtime.logger.debug("SolutionFusion. Setting parameters")
        self._data.setValsOfParameters(buff)

    def setParameters(self, params):
        """Update parameters from a list of parameter objects.
        
        Args:
            params: List of parameter objects with at least index and value
        """
        for p in params:
            self._data.assign_parameter(p)

    def getData(self):
        """Return the underlying VMEC data object."""
        return self._data

    def checkPressureDerivative(self):
        """Check if pressure derivative is non-positive across range.
        
        Evaluates the derivative of a polynomial (coefficients in parameter
        values) at each point in the derivative check range. Returns True only
        if the derivative is <= 0 at all points.
        
        Returns:
            bool: True if derivative is non-positive everywhere, False otherwise
        """
        values = self.getParametersValues()
        for v in DERIVATIVE_CHECK_RANGE:
            derivative = 0.0
            for i in range(1, len(values)):
                derivative += pow(v, i - 1) * values[i] * i
            if derivative > 0.0:
                return False
        return True
    
    def print(self):
        pass

    def getNumberofParams(self):
        """Return the number of parameters."""
        return self._data.getNumParams()
