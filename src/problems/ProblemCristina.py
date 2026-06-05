#!/usr/bin/env python


import random

from problems.ProblemBase import ProblemBase


class ProblemCristina(ProblemBase):
    def __init__(self, runtime, comms):
        super().__init__(runtime, comms)

    def solve(self, solution) -> None:
        if self._runtime.mock:
            solution.value = random.randint(0, 1000000)
        raise NotImplementedError("Solver not implemented")

    def extractSolution(self) -> tuple[float, float]:
        raise NotImplementedError("Extract solution abstract problem")

    def finish(self) -> None:
        raise NotImplementedError("Finish abstract problem")
