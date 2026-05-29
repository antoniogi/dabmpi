#!/usr/bin/env python
# vim: set fileencoding=utf-8 :

#############################################################################
#    Copyright 2013  by Antonio Gomez and Miguel Cardenas                   #
#                                                                           #
#   Licensed under the Apache License, Version 2.0 (the "License");         #
#   you may not use this file except in compliance with the License.        #
#   You may obtain a copy of the License at                                 #
#                                                                           #
#       http://www.apache.org/licenses/LICENSE-2.0                          #
#                                                                           #
#   Unless required by applicable law or agreed to in writing, software     #
#   distributed under the License is distributed on an "AS IS" BASIS,       #
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.#
#   See the License for the specific language governing permissions and     #
#   limitations under the License.                                          #
#############################################################################

import sys
import os

from solution.SolutionFusion import SolutionFusion
from solution.SolutionCristina import SolutionCristina
from solution.SolutionNonSeparable import SolutionNonSeparable
from data.Parameter import Parameter
from core.runtime import GlobalRuntime
from core.comms import GlobalComms
from core.enums import SolutionType, ObjectiveType
import math


__author__ = ' AUTHORS:     Antonio Gomez (antonio.gomez@csiro.au)'

__version__ = ' REVISION:   1.0  -  15-01-2014'

"""
HISTORY
    Version 0.1 (23-08-2013):   Creation of the file.
    Version 1.0 (15-01-2014):   Fist stable version.

This class implements a queue of solutions. It is used to create a queue of
solutions already evaluated and another queue of solutions that need to be
submitted.
The format of the elements in the queue is as follows:
    param_index:param_val, param_index:param_val,...,
    ,..., param_index:param_val - solutionVal
"""
class SolutionsQueue (object):
    def __init__(
        self,
        runtime: GlobalRuntime,
        comms: GlobalComms,
        solutions_file: str,
        writeToFile: bool,
        isPriority: bool = False,
    ):
        self._queue = []
        self._filename = solutions_file
        self._solType = runtime.solution_type
        self._isPriority = isPriority
        self._infile = runtime.input_file
        self._writeToFile = writeToFile
        self._maxSize = math.inf
        self._runtime = runtime
        self._comms = comms

        solution_map = {
            SolutionType.FUSION: (
                SolutionFusion,
                "Fusion",
            ),
            SolutionType.CRISTINA: (
                SolutionCristina,
                "Cristina",
            ),
            SolutionType.NONSEPARABLE: (
                SolutionNonSeparable,
                "Non-separable",
            )
        }

        solution_class, solution_name = solution_map.get(
            self._solType, (None, None)
        )

        try:
            self._solutionBase = solution_class(self._runtime, self._comms)

            self._runtime.logger.info(
                f"Queue: Initialized {solution_name} queue "
                f"({self._filename}) {self._infile}"
            )

            self._numParams = self._solutionBase.getNumberofParams()

            if os.path.exists(self._filename):
                self.load_queue()

        except Exception:
            self._runtime.logger.exception(
                "Queue: Error initializing queue"
            )
            raise

    def __del__(self):
        if self._filename == "top.queue":
            self.write_all_solutions()

    def setMaxSize(self, maxS):
        self._maxSize = maxS

    def qSize(self):
        return len(self._queue)

    """
    solution is a solution object
    value is the value of that solution (-1.0 if not evaluated)
    agent_idx is an integer used to specify the origin of this solution:
        if the queue stores solutions that need to be evaluated and we are
        using DAB, then agent_idx will identify the bee that created this
        solution
    """

    def put_solution(
        self,
        solution,
        value,
        agent_idx,
        sources: int = 3,
    ) -> None:
        if solution is None:
            self._runtime.logger.warning(
                f"QUEUE. Solution is None. {self._filename}"
            )
            return

        try:
            parameters = solution.getParameters()

            if len(parameters) != self._numParams:
                self._runtime.logger.warning(
                    "QUEUE. Invalid number of parameters "
                    f"({len(parameters)} instead of "
                    f"{self._numParams})"
                )
                return

            sol = ",".join(
                f"{param.get_index()}:{param.get_value()}"
                for param in parameters
            )

            sol_tuple = (sol, value, agent_idx)

            if not self._isPriority:
                if self.qSize() < self._maxSize:
                    self._queue.append(sol_tuple)

            else:
                inserted = False
                origins = set()

                for index, queued_tuple in enumerate(self._queue):
                    queued_value = float(queued_tuple[1])
                    queued_origin = queued_tuple[2]

                    origins.add(queued_origin)

                    if self._runtime.objective == ObjectiveType.MAXIMIZE:
                        if queued_value > value and queued_value >= 0.0:
                            continue

                    elif self._runtime.objective == ObjectiveType.MINIMIZE:
                        if queued_value < value and queued_value >= 0.0:
                            continue

                    if (
                        index > self._maxSize / 10
                        and len(origins) <= 1
                        and agent_idx in origins
                    ):
                        break

                    self._queue.insert(index, sol_tuple)
                    inserted = True
                    break

                if not inserted and len(origins) < sources:
                    if agent_idx not in origins:

                        if self.qSize() > 0:
                            for index in range(
                                self.qSize() - 1,
                                -1,
                                -1,
                            ):
                                if self._queue[index][2] in origins:
                                    self._queue.pop(index)
                                    break

                        self._queue.append(sol_tuple)

                if self.qSize() > self._maxSize:
                    self._queue.pop()

        except Exception:
            self._runtime.logger.exception(
                "QUEUE. Error adding solution"
            )
            raise

        if not self._writeToFile:
            return

        try:
            with open(self._filename, "a", encoding="utf-8") as file:
                file.write(
                    f"{sol}#{value}#{agent_idx}\n"
                )

        except Exception:
            self._runtime.logger.exception(
                "QUEUE. Error writing solution to file"
            )
            raise
    """
    Loads a queue that it's contained in a text file
    """

    def load_queue(self):
        with open(self._filename, 'r', encoding="utf-8") as file:
            for line in file:
                sol_tuple = line.strip().split('#')
                if not self._isPriority:
                    self._queue.append(sol_tuple)
                    continue

                value = float(sol_tuple[1])
                inserted = False
                for index, queued_item in enumerate(self._queue):
                    if float(queued_item[1]) >= value:
                        #TODO: check if is index-1 or index
                        self._queue.insert(index-1, sol_tuple)
                        inserted = True
                        break
                if not inserted:
                    self._queue.append(sol_tuple)

    """
    Returns the queue
    """

    def get_all_solutions(self):
        return self._queue

    """
    Empties the queue and writes all it's content in a text file
    """

    def write_all_solutions(self) -> None:
        try:
            with open(self._filename, "w", encoding="utf-8") as file:
                while self.qSize() > 0:
                    solution_tuple = self.get_solution_tuple(True)

                    parameters = solution_tuple[0].getParameters()

                    if len(parameters) != self._numParams:
                        self._runtime.logger.warning(
                            "QUEUE. Invalid number of params "
                            f"({len(parameters)} instead of "
                            f"{self._numParams})"
                        )
                        return

                    solution = ",".join(
                        f"{param.get_index()}:{param.get_value()}"
                        for param in parameters
                    )

                    file.write(
                        f"{solution}#"
                        f"{solution_tuple[1]}#"
                        f"{solution_tuple[2]}\n"
                    )

        except Exception:
            self._runtime.logger.exception(
                "QUEUE. Error writing solutions"
            )
            raise

    """
    Extracts a solution from the queue
    Returns a solution object, so the information in the queue needs to
    be extracted an converted into a solution object.
    For that, it just goes through the sequence idx:val,..., idx:val
    and creates a parameter (VMEC, or any other type) and assigns
    the index and value previously extracted. Once created, pass the
    parameter to the solution class that will put the updated value into its
    parameters

    if remove is true, it behaves as a regular queue, where the front of the
    queue is removed. If false, it just checks the front of the queue, but
    doesn't remove anything
    """
    """

    def GetSolution(self, remove=True):
        solution = None
        if len(self._queue) == 0:
            return solution
        solution = self._solutionBase
        if remove:
            sol_tuple = self._queue.pop(0)
        else:
            sol_tuple = self._queue[0]
        #split to get each idx:val
        parameters = sol_tuple[0].split(',')
        params = []
        #iterate through the elements in the list
        for p in parameters:
            param = Parameter()
            param.set_index(p.split(':')[0])
            param.set_type("double")
            param.set_value(p.split(':')[1])
            params.append(param)
        solution.setParameters(params)

        return solution
    """

    """
    if remove is true, it behaves as a regular queue, where the front of the
    queue is removed. If false, it just checks the front of the queue, but
    doesn't remove anything
    """

    def get_solution_tuple(self, remove=True):
        solution = None
        val = -1.0
        agent_idx = -1
        if self.qSize() == 0:
            return solution, val, agent_idx
        solution = self._solutionBase
        if remove:
            sol_tuple = self._queue.pop(0)
        else:
            sol_tuple = self._queue[0]

        val = sol_tuple[1]
        agent_idx = sol_tuple[2]
        #split to get each idx:val
        parameters = sol_tuple[0].split(',')
        params = []
        #iterate through the elements in the list
        for p in parameters:
            params.append(float(p.split(':')[1]))

        #this method expects a list of parameters
        self._solutionBase.setParametersValues(params)
        #self._solutionBase.setParameters (params)

        return self._solutionBase, float(val), int(agent_idx)

    """
    if remove is true, it behaves as a regular queue, where the front of the
    queue is removed. If false, it just checks the front of the queue, but
    doesn't remove anything
    """

    def get_solution_list(self, remove=True):
        solution = []
        val = -1.0
        agent_idx = -1
        try:
            if len(self._queue) == 0:
                return val, agent_idx, solution
            if remove:
                sol_tuple = self._queue.pop(0)
            else:
                sol_tuple = self._queue[0]

            val = float(sol_tuple[1])
            agent_idx = int(sol_tuple[2])
            #split to get each idx:val
            parameters = sol_tuple[0].split(',')
            #iterate through the elements in the list
            self._runtime.logger.debug("QUEUE. Number of parameters: " +
                              str(len(parameters)))
            for p in parameters:
                self._runtime.logger.debug("Appending: " + str(p.split(':')[1]))
                solution.append(float(p.split(':')[1]))
        except Exception as e:
            self._runtime.logger.error("QUEUE (" + str(sys.exc_info()[2].tb_lineno) +
                                "). " + str(e))
        return val, agent_idx, solution

    """
    Returns the sum of all the solutions values
    If minimizing, returns 1.0/total_sum
    """
    def get_total_solutions_values(self) -> float:
        total_sum = 0.0

        for sol_tuple in self._queue:
            value = float(sol_tuple[1])

            if value == 0.0:
                return math.inf
            else:
                total_sum += 1.0 / value

        return total_sum

    """
    In a priority list, it returns the solution so that the sum of the values
    of all the previous solutions and the current solution is larger than value
    """

    def get_tuple_on_priority_by_value(
        self,
        value: float,
    ):
        temp_sum = 0.0
        total_val = self.get_total_solutions_values()

        for index, sol_tuple in enumerate(self._queue):
            solution_str, score_str, generation_str = sol_tuple

            score = float(score_str)

            if self._runtime.objective == ObjectiveType.MINIMIZE:
                increment = math.inf if score == 0.0 else 1.0 / score
            else:
                increment = score

            temp_sum += increment

            self._runtime.logger.debug(
                f"TempSum: {temp_sum}/{score}"
            )

            if temp_sum > value:
                params = [
                    float(param.split(":")[1])
                    for param in solution_str.split(",")
                ]

                self._runtime.logger.info(
                    "Queue. Returning solution in position "
                    f"{index} / {temp_sum} / {value} / "
                    f"{self.qSize()} / {total_val}"
                )

                self._solutionBase.setParametersValues(params)

                return (
                    self._solutionBase,
                    score,
                    int(generation_str),
                )

        self._runtime.logger.info(
            f"Queue. Returning None. "
            f"{value}/{total_val}/{temp_sum}"
        )

        return None, None, None
