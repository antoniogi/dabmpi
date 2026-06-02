#!/usr/bin/env python
# vim: set fileencoding=utf-8 :


import random

from problems.ProblemBase import ProblemBase


class ProblemCristina(ProblemBase):
    def __init__(self, runtime, comms):
        super().__init__(runtime, comms)

    def solve(self, solution) -> None:
        val = random.randint(0, 1000000)
        solution.setValue(val)

    def extractSolution(self) -> tuple[float, float]:
        raise NotImplementedError("Extract solution abstract problem")

    def finish(self) -> None:
        raise NotImplementedError("Finish abstract problem")
