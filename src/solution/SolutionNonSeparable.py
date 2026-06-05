#!/usr/bin/env python


from data.NonSeparableData import NonSeparableData
from solution.SolutionBase import SolutionBase


class SolutionNonSeparable(SolutionBase):
    def __init__(self, runtime, comms):
        SolutionBase.__init__(self, runtime, comms)
        self._data = NonSeparableData(runtime)
        self._data.initialize(runtime.input_file)
        return

    def get_parameters_values(self):
        return self._data.get_params_values()

    def set_parameters_values(self, buff):
        self._data.set_params_values(buff)

    def get_parameters(self):
        return self._data.params

    def set_parameters(self, params):
        self._data.params = params

    def initialize(self, data):
        self._data = data

    def get_number_of_params(self):
        return self._data.num_params

    def get_max_number_of_values(self):
        return self._data.max_range

    def prepare(self, filename) -> bool:
        return True

    def print(self):
        pass
