#!/usr/bin/env python
# vim: set fileencoding=utf-8 :


from data.CristinaData import CristinaData
from solution.SolutionBase import SolutionBase


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
