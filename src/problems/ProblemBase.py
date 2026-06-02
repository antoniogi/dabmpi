#!/usr/bin/env python
# vim: set fileencoding=utf-8 :


from abc import ABC, abstractmethod

class ProblemBase(ABC):
    def __init__(self, runtime, comms):
        self._runtime = runtime
        self._comms = comms
        return

    @abstractmethod
    def solve(self, solution) -> None:
        pass

    @abstractmethod
    def extractSolution(self) -> tuple[float, float]:
        pass

    @abstractmethod
    def finish(self) -> None:
        pass