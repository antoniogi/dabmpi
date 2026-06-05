#!/usr/bin/env python
from typing import Any

from data.VMECProcess import VMECProcess
from problems.ProblemBase import ProblemBase


class ProblemFusion(ProblemBase):
    _vmec: VMECProcess

    def __init__(self, runtime: Any, comms: Any) -> None:
        try:
            super().__init__(runtime, comms)
            self._vmec = VMECProcess(runtime, comms)

        except Exception:
            self._runtime.logger.exception("ProblemFusion init failed")
            raise

    def create_input_file(self, solution) -> bool:
        try:
            return self._vmec.create_input_file(solution)
        except Exception:
            self._runtime.logger.exception("ProblemFusion: error creating input file")
            return False

    def execute_configuration(self):
        return self._vmec.execute_configuration()

    def extractSolution(self) -> tuple[float, float]:
        self._runtime.logger.debug("Extract solution fusion")
        return self._vmec.get_beta(), self._vmec.get_bgradbval()

    def solve(self, solution) -> None:
        try:
            self._runtime.logger.debug("Start solving Fusion problem")

            self.create_input_file(solution)
            solution.value = self.execute_configuration()

            self._runtime.logger.debug("Finished solving Fusion problem")

        except Exception:
            self._runtime.logger.exception("Error solving Problem Fusion")

    def finish(self) -> None:
        self._runtime.logger.debug("Finish Problem Fusion")
