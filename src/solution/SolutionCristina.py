#!/usr/bin/env python


from data.CristinaData import CristinaData
from solution.SolutionBase import SolutionBase


class SolutionCristina(SolutionBase):
    def __init__(self, runtime, comms, data):
        SolutionBase.__init__(self, runtime, comms, data)
        # TODO: Implemement how data is initialized
        self._data = CristinaData(runtime)
        self._data.initialize(runtime.input_file)
        return

    def initialize(self, data):
        self._data = data
        return

    def prepare(self, filename) -> bool:
        return True

    def get_number_of_params(self):
        return self._data.num_parameters

    def get_max_number_of_values(self):
        return self._data.max_range

    def get_parameters(self):
        return self._data.parameters

    def get_parameters_values(self):
        return self._data.get_parameters_values()

    def set_parameters_values(self, buff):
        self._data.set_parameters_values(buff)

    def set_parameters(self, params):
        self._data.set_parameters(params)

    def getData(self):
        return self._data

    def print(self):
        self._data.print_data()
