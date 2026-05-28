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
    def __init__(self, runtime: GlobalRuntime, comms: GlobalComms, solutions_file: str, writeToFile: bool, isPriority: bool=False):
        try:
            self._queue = []
            self._filename = solutions_file
            self._solType = runtime.solution_type
            self._isPriority = isPriority
            self._infile = runtime.input_file
            self._writeToFile = writeToFile
            self._maxSize = math.inf
            self._runtime = runtime
            self._comms = comms
            if self._solType == SolutionType.FUSION:
                self._solutionBase = SolutionFusion(self._runtime, self._comms)
                self._runtime.logger.info("QUEUE: Initialised fusion queue (" +
                                self._filename + ")" + self._infile)
            elif self._solType == SolutionType.CRISTINA:
                self._solutionBase = SolutionCristina(self._runtime, self._comms)
                self._runtime.logger.info("QUEUE: Initialised Cristina queue (" +
                                self._filename + ")" + self._infile)
            else:
                self._solutionBase = SolutionNonSeparable(self._runtime, self._comms)
                self._runtime.logger.info("QUEUE: Initialised non separable queue (" +
                                self._filename + ")" + self._infile)
            self._numParams = self._solutionBase.getNumberofParams()
            if os.path.exists(self._filename):
                self.LoadQueue()
        except Exception as e:
            self._runtime.logger.error("QUEUE (" + str(sys.exc_info()[2].tb_lineno) +
                                "). " + str(e))

    def __del__(self):
        if self._filename == "top.queue":
            self.writeAllSolutions()

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

    def PutSolution(self, solution, value, agent_idx, sources=3):
        if solution is None:
            self._runtime.logger.warning("QUEUE. Solution is None. " +
                                str(self._filename))
            return
        parameters = solution.getParameters()
        sol = ""
        try:
            if self._numParams != len(parameters):
                self._runtime.logger.warning("QUEUE. Invalid number of parameters (" +
                                    str(len(parameters)) + " instead of " +
                                    str(self._numParams) + ")")
                return
            for param in parameters:
                idx = param.get_index()
                val = param.get_value()
                sol = sol + str(idx) + ":" + str(val) + ","
            sol = sol.rstrip(',')
            sol_tuple = sol, value, agent_idx
            if not self._isPriority:
                if self.qSize() < self._maxSize:
                    self._queue.append(sol_tuple)
            else:
                inserted = False
                origins = set()
                for i in range(len(self._queue)):
                    origins.add(self._queue[i][2])
                    if self._runtime.objective == ObjectiveType.MAXIMIZE:
                        if (float(self._queue[i][1]) > value and
                            float(self._queue[i][1]) >= 0.0):
                            continue
                    if self._runtime.objective == ObjectiveType.MINIMIZE:
                        if (float(self._queue[i][1]) < value and
                            float(self._queue[i][1]) >= 0.0):
                            continue
                    if (i > self._maxSize / 10 and len(origins) <= 1 and
                        agent_idx in origins):
                        break
                    self._queue.insert(i, sol_tuple)
                    inserted = True
                    break
                if (not inserted and len(origins) < sources):
                    if agent_idx not in origins:
                        if self.qSize() > 0:
                            for i in range(self.qSize() - 1, 0):
                                if self._queue[2] in origins:
                                    self._queue.pop(i)
                                    break
                        self._queue.append(sol_tuple)
                if self.qSize() > self._maxSize:
                    self._queue.pop()
        except Exception as e:
            self._runtime.logger.error("QUEUE (" + str(sys.exc_info()[2].tb_lineno) +
                            "). " + str(e))
        if not self._writeToFile:
            return
        try:
            with open(self._filename, 'a') as f:
                f.write(sol + "#" + str(value) + '#' + str(agent_idx) + '\n')
        except Exception as e:
            self._runtime.logger.error("QUEUE (" + str(sys.exc_info()[2].tb_lineno) +
                            "). " + str(e))

    """
    Loads a queue that it's contained in a text file
    """

    def LoadQueue(self):
        with open(self._filename, 'r') as f:
            for line in f.readlines():
                sol_tuple = line.split('#')
                if not self._isPriority:
                    self._queue.append(sol_tuple)
                else:
                    value = float(sol_tuple[1])
                    inserted = False
                    for i in range(len(self._queue)):
                        if float(self._queue[i][1]) < value:
                            continue
                        self._queue.insert(i - 1, sol_tuple)
                        inserted = True
                        break
                    if not inserted:
                        self._queue.append(sol_tuple)

    """
    Returns the queue
    """

    def getAllSolutions(self):
        return self._queue

    """
    Empties the queue and writes all it's content in a text file
    """

    def writeAllSolutions(self):
        with open(self._filename, 'w') as f:
            try:
                while True:
                    if self.qSize() == 0:
                        break
                    solutionTuple = self.GetSolutionTuple(True)
                    parameters = solutionTuple[0].getParameters()
                    sol = ""
                    if self._numParams != len(parameters):
                        self._runtime.logger.warning("QUEUE. Invalid number of params (" +
                                                    str(len(parameters)) + " instead of " +
                                                    str(self._numParams) + ")")
                        return
                    for param in parameters:
                        idx = param.get_index()
                        val = param.get_value()
                        sol = sol + str(idx) + ":" + str(val) + ","
                    sol = sol.rstrip(',')
                    f.write(sol + "#" + str(solutionTuple[1]) + '#' +
                            str(solutionTuple[2]) + '\n')
            except Exception as e:
                self._runtime.logger.error("QUEUE (" + str(sys.exc_info()[2].tb_lineno) +
                                "). " + str(e))

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
    if remove is true, it behaves as a regular queue, where the front of the
    queue is removed. If false, it just checks the front of the queue, but
    doesn't remove anything
    """

    def GetSolutionTuple(self, remove=True):
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

    def GetSolutionList(self, remove=True):
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
    def GetTotalSolutionsValues(self):
        total_sum = 0.0
        for i in range(self.qSize()):
            sol_tuple = self._queue[i]
            if float(sol_tuple[1])==0.0:
                total_sum += math.inf
            else:
                total_sum += 1.0 / float(sol_tuple[1])
        return total_sum

    """
    In a priority list, it returns the solution so that the sum of the values
    of all the previous solutions and the current solution is larger than value
    """

    def GetTupleOnPriorityByValue(self, value):
        temp_sum = 0.0
        total_val = self.GetTotalSolutionsValues()
        for i in range(self.qSize()):
            if self._runtime.objective == ObjectiveType.MINIMIZE:
                if float(self._queue[i][1])==0.0:
                    temp_sum += math.inf
                else:
                    temp_sum += float(1.0 / float(self._queue[i][1]))
            else:
                temp_sum += float(self._queue[i][1])
            self._runtime.logger.debug("TempSum: " + str(temp_sum) + "/" +
                                        str(self._queue[i][1]))
            if temp_sum > value:
                #split to get each idx:val
                parameters = self._queue[i][0].split(',')
                params = []
                #iterate through the elements in the list
                for p in parameters:
                    params.append(float(p.split(':')[1]))

                #this method expects a list of parameters
                self._runtime.logger.info("Queue. Returning solution in position " +
                                 str(i) + " / " + str(temp_sum) + " / " +
                                 str(value) + " / " + str(self.qSize()) +
                                 " / " + str(total_val))
                self._solutionBase.setParametersValues(params)
                return (self._solutionBase, float(self._queue[i][1]),
                        int(self._queue[i][2]))
        self._runtime.logger.info("Queue. Returning None. " + str(value) +
                         "/" + str(total_val) + "/" + str(temp_sum))
        return None, None, None
