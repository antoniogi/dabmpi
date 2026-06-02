#!/usr/bin/env python
# vim: set fileencoding=utf-8 :


from abc import ABC, abstractmethod
from core.comms import GlobalComms
from core.runtime import GlobalRuntime
from solution.SolutionsQueue import SolutionsQueue


class SolverBase(ABC):
    """
    Abstract base class for all solver implementations.

    Defines the solver lifecycle (initialize, solve, finish) and
    provides common solution queues used for distributed execution.
    """
    def __init__(self, runtime: GlobalRuntime, comms: GlobalComms):
        self._runtime: GlobalRuntime = runtime
        self._comms: GlobalComms = comms

        self._finishedSolutions: SolutionsQueue = SolutionsQueue(
            runtime, comms, "finished.queue", writeToFile=True, isPriority=True
            )
        self._pendingSolutions: SolutionsQueue = SolutionsQueue(
            runtime, comms, "pending.queue", writeToFile=False
            )
        self._topSolutions: SolutionsQueue = SolutionsQueue(
            runtime, comms, "top.queue", writeToFile=False, isPriority=True
            )

    @abstractmethod
    def initialize(self) -> None:
        ...
    
    @abstractmethod
    def solve(self) -> None:
        ...

    @abstractmethod
    def finish(self) -> None:
        ...
