#!/usr/bin/env python


from data.NonSeparableData import NonSeparableData
from solution.SolutionBase import SolutionBase


class SolutionNonSeparable(SolutionBase):
    def __init__(self, runtime, comms):
        SolutionBase.__init__(self, runtime, comms)
        self._data = NonSeparableData(runtime)
        self._data.initialize(runtime.input_file)
        return

    def getParametersValues(self):
        return self._data.getValsOfParameters()

    def setParametersValues(self, buff):
        self._data.setValsOfParameters(buff)

    def getParameters(self):
        return self._data.getParameters()

    def setParameters(self, params):
        self._data.setParameters(params)

    def initialize(self, data):
        self._data = data

    def getNumberofParams(self):
        return self._data.getNumParams()

    def getMaxNumberofValues(self):
        return self._data.getMaxRange()

    def prepare(self, filename) -> bool:
        return True

    def print(self):
        pass
