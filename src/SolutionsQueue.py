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

from SolutionFusion import SolutionFusion
from SolutionCristina import SolutionCristina
from SolutionNonSeparable import SolutionNonSeparable
import Utils as util
from Parameter import Parameter


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
    def __init__(self, filename, solution_type, infile, writeToFile,
                 isPriority=False):
        try:
            self.__queue = []
            self.__filename = filename
            self.__solType = solution_type
            self.__isPriority = isPriority
            self.__infile = infile
            self.__writeToFile = writeToFile
            self.__maxSize = util.infinity
            if self.__solType == util.solution_type.FUSION:
                self.__solutionBase = SolutionFusion(self.__infile)
                util.logger.info("QUEUE: Initialised fusion queue (" +
                                  filename + ")" + self.__infile)
            if self.__solType == util.solution_type.CRISTINA:
                self.__solutionBase = SolutionCristina(self.__infile)
                util.logger.info("QUEUE: Initialised Cristina queue (" +
                                  filename + ")" + self.__infile)
            else:
                self.__solutionBase = SolutionNonSeparable(self.__infile)
                util.logger.info("QUEUE: Initialised non separable queue (" +
                                  filename + ")" + self.__infile)
            self.__numParams = self.__solutionBase.getNumberofParams()
            if os.path.exists(self.__filename):
                self.LoadQueue()
        except Exception as e:
            util.logger.error("QUEUE (" + str(sys.exc_info()[2].tb_lineno) +
                                "). " + str(e))

    def __del__(self):
        if self.__filename == "top.queue":
            self.writeAllSolutions()

    def setMaxSize(self, maxS):
        self.__maxSize = maxS

    def qSize(self):
        return len(self.__queue)

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
            util.logger.warning("QUEUE. Solution is None. " +
                                str(self.__filename))
            return
        parameters = solution.getParameters()
        sol = ""
        try:
            if self.__numParams != len(parameters):
                util.logger.warning("QUEUE. Invalid number of parameters (" +
                                    str(len(parameters)) + " instead of " +
                                    str(self.__numParams) + ")")
                return
            for param in parameters:
                idx = param.get_index()
                val = param.get_value()
                sol = sol + str(idx) + ":" + str(val) + ","
            sol = sol.rstrip(',')
            sol_tuple = sol, value, agent_idx
            if not self.__isPriority:
                if self.qSize() < self.__maxSize:
                    self.__queue.append(sol_tuple)
            else:
                inserted = False
                origins = set()
                for i in range(len(self.__queue)):
                    origins.add(self.__queue[i][2])
                    if util.objective == util.objectiveType.MAXIMIZE:
                        if (self.__queue[i][1] > value and
                            self.__queue[i][1] >= 0.0):
                            continue
                    if util.objective == util.objectiveType.MINIMIZE:
                        if (self.__queue[i][1] < value and
                            self.__queue[i][1] >= 0.0):
                            continue
                    if (i > self.__maxSize / 10 and len(origins) <= 1 and
                        agent_idx in origins):
                        break
                    self.__queue.insert(i, sol_tuple)
                    inserted = True
                    break
                if (not inserted and len(origins) < sources):
                    if agent_idx not in origins:
                        if self.qSize() > 0:
                            for i in range(self.qSize() - 1, 0):
                                if self.__queue[2] in origins:
                                    self.__queue.pop(i)
                                    break
                        self.__queue.append(sol_tuple)
                if self.qSize() > self.__maxSize:
                    self.__queue.pop()
        except Exception as e:
            util.logger.error("QUEUE (" + str(sys.exc_info()[2].tb_lineno) +
                            "). " + str(e))
        if not self.__writeToFile:
            return
        try:
            with open(self.__filename, 'a') as f:
                f.write(sol + "#" + str(value) + '#' + str(agent_idx) + '\n')
        except Exception as e:
            util.logger.error("QUEUE (" + str(sys.exc_info()[2].tb_lineno) +
                            "). " + str(e))

    """
    Loads a queue that it's contained in a text file
    """

    def LoadQueue(self):
        with open(self.__filename, 'r') as f:
            for line in f.readlines():
                sol_tuple = line.split('#')
                if not self.__isPriority:
                    self.__queue.append(sol_tuple)
                else:
                    value = float(sol_tuple[1])
                    inserted = False
                    for i in range(len(self.__queue)):
                        if self.__queue[i][1] < value:
                            continue
                        self.__queue.insert(i - 1, sol_tuple)
                        inserted = True
                        break
                    if not inserted:
                        self.__queue.append(sol_tuple)

    """
    Returns the queue
    """

    def getAllSolutions(self):
        return self.__queue

    """
    Empties the queue and writes all it's content in a text file
    """

    def writeAllSolutions(self):
        with open(self.__filename, 'w') as f:
            try:
                while True:
                    if self.qSize() == 0:
                        break
                    solutionTuple = self.GetSolutionTuple(True)
                    parameters = solutionTuple[0].getParameters()
                    sol = ""
                    if self.__numParams != len(parameters):
                        util.logger.warning("QUEUE. Invalid number of params (" +
                                            str(len(parameters)) + " instead of " +
                                            str(self.__numParams) + ")")
                        return
                    for param in parameters:
                        idx = param.get_index()
                        val = param.get_value()
                        sol = sol + str(idx) + ":" + str(val) + ","
                    sol = sol.rstrip(',')
                    f.write(sol + "#" + str(solutionTuple[1]) + '#' +
                            str(solutionTuple[2]) + '\n')
            except Exception as e:
                util.logger.error("QUEUE (" + str(sys.exc_info()[2].tb_lineno) +
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
        if len(self.__queue) == 0:
            return solution
        solution = self.__solutionBase
        if remove:
            sol_tuple = self.__queue.pop(0)
        else:
            sol_tuple = self.__queue[0]
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
        solution = self.__solutionBase
        if remove:
            sol_tuple = self.__queue.pop(0)
        else:
            sol_tuple = self.__queue[0]

        val = sol_tuple[1]
        agent_idx = sol_tuple[2]
        #split to get each idx:val
        parameters = sol_tuple[0].split(',')
        params = []
        #iterate through the elements in the list
        for p in parameters:
            params.append(float(p.split(':')[1]))

        #this method expects a list of parameters
        self.__solutionBase.setParametersValues(params)
        #self.__solutionBase.setParameters (params)

        return self.__solutionBase, float(val), int(agent_idx)

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
            if len(self.__queue) == 0:
                return val, agent_idx, solution
            if remove:
                sol_tuple = self.__queue.pop(0)
            else:
                sol_tuple = self.__queue[0]

            val = float(sol_tuple[1])
            agent_idx = int(sol_tuple[2])
            #split to get each idx:val
            parameters = sol_tuple[0].split(',')
            #iterate through the elements in the list
            util.logger.debug("QUEUE. Number of parameters: " +
                              str(len(parameters)))
            for p in parameters:
                util.logger.debug("Appending: " + str(p.split(':')[1]))
                solution.append(float(p.split(':')[1]))
        except Exception as e:
            util.logger.error("QUEUE (" + str(sys.exc_info()[2].tb_lineno) +
                                "). " + str(e))
        return val, agent_idx, solution

    """
    Returns the sum of all the solutions values
    If minimizing, returns 1.0/total_sum
    """
    def GetTotalSolutionsValues(self):
        total_sum = 0.0
        for i in range(self.qSize()):
            sol_tuple = self.__queue[i]
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
            if util.objective == util.objectiveType.MINIMIZE:
                temp_sum += float(1.0 / self.__queue[i][1])
            else:
                temp_sum += float(self.__queue[i][1])
            util.logger.debug("TempSum: " + str(temp_sum) + "/" +
                               str(self.__queue[i][1]))
            if temp_sum > value:
                #split to get each idx:val
                parameters = self.__queue[i][0].split(',')
                params = []
                #iterate through the elements in the list
                for p in parameters:
                    params.append(float(p.split(':')[1]))

                #this method expects a list of parameters
                util.logger.info("Queue. Returning solution in position " +
                                 str(i) + " / " + str(temp_sum) + " / " +
                                 str(value) + " / " + str(self.qSize()) +
                                 " / " + str(total_val))
                self.__solutionBase.setParametersValues(params)
                return (self.__solutionBase, float(self.__queue[i][1]),
                        int(self.__queue[i][2]))
        util.logger.info("Queue. Returning None. " + str(value) +
                         "/" + str(total_val) + "/" + str(temp_sum))
        return None, None, None
