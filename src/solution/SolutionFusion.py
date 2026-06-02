#!/usr/bin/env python
# vim: set fileencoding=utf-8 :


from data.VMECData import VMECData
from solution.SolutionBase import SolutionBase

# Range for polynomial derivative check
DERIVATIVE_CHECK_RANGE = range(-100, 100)


class SolutionFusion(SolutionBase):
    def __init__(self,runtime, comms):
        super().__init__(runtime, comms)
        self._data = VMECData(runtime, comms)
        self._data.initialize(runtime.input_file)

    def initialize(self, data):
        """Initialize with external data object."""
        self._data = data

    def prepare(self, filename) -> bool:
        """Create input file for VMEC."""
        return self._data.create_input_file(filename)

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
