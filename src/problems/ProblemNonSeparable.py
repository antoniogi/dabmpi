#!/usr/bin/env python
# vim: set fileencoding=utf-8 :


import math
import traceback

from problems.ProblemBase import ProblemBase

class ProblemNonSeparable(ProblemBase):

    def __init__(self, runtime, comms):
        super().__init__(runtime, comms)

    #this implements Rosenbrock's Function
    def solve(self, solution) -> None:
        try:
            parameters = solution.getParametersValues()
            val = 0.0
            for i in range(0, len(parameters) - 1):
                val += (100 * (math.pow((math.pow(parameters[i], 2) -
                              parameters[i + 1]), 2)) +
                              math.pow(parameters[i] + 1, 2))
            solution.setValue(val)
            self._runtime.logger.debug("Solve Problem NonSeparable")
        except Exception as e:
            tb = traceback.extract_tb(e.__traceback__)
            line = tb[-1].lineno

            self._runtime.logger.error(
                f"ProblemNonSeparable ({line}) {e}"
            )

    def extractSolution(self) -> tuple[float, float]:
        raise NotImplementedError("Extract solution abstract problem")

    def finish(self) -> None:
        self._runtime.logger.info("Finish Problem NonSeparable")
