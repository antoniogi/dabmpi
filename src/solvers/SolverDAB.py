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

import traceback

from mpi4py import MPI
import sys
import math
import random
import shutil
import time
from datetime import datetime
from core.enums import ProblemType, SolutionType, ObjectiveType, CommModelType
from array import array
from solvers.SolverBase import SolverBase
from problems.ProblemCristina import ProblemCristina
from problems.ProblemFusion import ProblemFusion
from problems.ProblemNonSeparable import ProblemNonSeparable
from solution.SolutionBase import SolutionBase
from solution.SolutionCristina import SolutionCristina
from solution.SolutionFusion import SolutionFusion
from solution.SolutionNonSeparable import SolutionNonSeparable
from solution.SolutionsQueue import SolutionsQueue
import configparser
from core.runtime import GlobalRuntime
from core.comms import GlobalComms
from core.enums import Tags
from core.matrix import Matrix
from data.Parameter import ParamType

_author_ = ' AUTHORS:     Antonio Gomez (antonio.gomez@csiro.au)'


_version_ = ' REVISION:   1.0  -  15-01-2014'

EXTRA_LOG=100

"""
HISTORY
    Version 0.1 (12-04-2013):   Creation of the file.
    Version 1.0 (15-01-2014):   Fist stable version.
"""

"""
Class that implements the DAB solver. It has to:
  - Create the different bees.
  - Solve is the main method that actually implements the algorithm
  - Once the algorithm has finish, we have to call the finish method if
  there is something else to be done.
"""


"""
Base class for bees
"""

"""
Still pending: when we have evaluated a solution, we have to find the bee
that created that solution and set the value for that solution in the bee
"""


class BeeBase ():
    def __init__(self, runtime: GlobalRuntime, comms: GlobalComms, matrix: Matrix):
        random.seed()
        self._problem = None
        self._bestLocalSolution: SolutionBase = None
        self._bestGlobalSolution: SolutionBase = None
        self._bestLocalInitialised = False
        #Number of iterations since the local solution
        #was created
        self._itersinceLastUpdate = 0
        self._runtime = runtime
        self._comms = comms
        self._max_attempts = 1000

        if self._runtime.problem_type == ProblemType.FUSION:
            self._problem = ProblemFusion(self._runtime, self._comms)
            self._solution = SolutionFusion(self._runtime, self._comms)
            self._bestLocalSolution = SolutionFusion(self._runtime, self._comms)
            self._bestGlobalSolution = SolutionFusion(self._runtime, self._comms)
        elif self._runtime.problem_type == ProblemType.NONSEPARABLE:
            self._problem = ProblemNonSeparable(self._runtime, self._comms)
            self._bestLocalSolution = SolutionNonSeparable(self._runtime, self._comms)
            self._bestGlobalSolution = SolutionNonSeparable(self._runtime, self._comms)
        elif self._runtime.problem_type == ProblemType.CRISTINA:
            self._problem = ProblemCristina(self._runtime, self._comms)
            self._bestLocalSolution = SolutionCristina(self._runtime, self._comms)
            self._bestGlobalSolution = SolutionCristina(self._runtime, self._comms)

        if self._runtime.objective == ObjectiveType.MAXIMIZE:
            self._bestLocalSolution.setValue(-math.inf)
            self._bestGlobalSolution.setValue(-math.inf)
        else:
            self._bestLocalSolution.setValue(math.inf)
            self._bestGlobalSolution.setValue(math.inf)

        self._matrix = matrix
        self._runtime.logger.info(f"Problem initialized (type {self._runtime.problem_type})")
        self._runtime.logger.info(f"Solution initialized (type {self._runtime.problem_type})")
        self._runtime.logger.info(f"Best local solution initialized {self._bestLocalSolution}")
        self._runtime.logger.info(f"Best global solution initialized {self._bestGlobalSolution}")
        return

    def getIter(self):
        return self._itersinceLastUpdate

    def setIter(self, val):
        self._itersinceLastUpdate = val

    def getBestLocalSolution(self):
        return self._bestLocalSolution

    def bestLocalInitialised(self):
        return self._bestLocalInitialised

    def createNewCandidate(
            self, 
            pendingSolutions: SolutionsQueue,
            finishedSolutions: SolutionsQueue,
            matrix: Matrix,
            topSolutions: SolutionsQueue,
            totalSumGoodSolutions: float
        ):
        self._runtime.logger.error('Solver DAB. Create new candidate base')
        raise NotImplementedError("Abstract bee (calling create\
                                   new candidate)")

    def is_new(self, solution, pending_solutions: SolutionsQueue, finished_solutions: SolutionsQueue) -> bool:
        try:
            #if pending_solutions is None or finished_solutions is None:
            #    return True
            pending = pending_solutions.get_all_solutions()
            finished = finished_solutions.get_all_solutions()
            return solution not in pending and solution not in finished
            #pending = set(pending_solutions.get_all_solutions())
            #finished = set(finished_solutions.get_all_solutions())
            #return solution not in pending and solution not in finished
        except:
            self._runtime.logger.exception("Error checking if solution is new")
            raise


    """
    Creates a new random solution
    Extracts the parameters that can be modified, and generates a new
    value for each parameter considering the min and max values of that
    parameter
    """
    def createRandomSolution(self, pendingSolutions, finishedSolutions):
        self._runtime.logger.info('Create a new random solution')
        solution = None
        params = []

        try:
            for _ in range(self._max_attempts):
                solution = self.getBestLocalSolution()
                params = solution.getParameters()

                self._runtime.logger.debug(
                    f'number of parameters: {len(params)}'
                )

                for param in params:
                    ptype = param.get_type()
                    new_value = None

                    if ptype is ParamType.STRING:
                        continue

                    elif ptype is ParamType.FLOAT:
                        minVal, maxVal = sorted((
                            param.get_min_value(),
                            param.get_max_value()
                        ))

                        if minVal == maxVal:
                            new_value = minVal
                        else:
                            gap = param.get_gap()

                            if gap == 0.0:
                                new_value = random.uniform(minVal, maxVal)
                            else:
                                new_value = self.randrange_float(minVal, maxVal, gap)

                    elif ptype is ParamType.BOOL:
                        new_value = random.choice((True, False))

                    elif ptype is ParamType.INT:
                        minVal, maxVal = sorted((
                            param.get_min_value(),
                            param.get_max_value()
                        ))

                        if minVal == maxVal:
                            new_value = minVal
                        else:
                            new_value = random.randint(minVal, maxVal)

                    else:
                        raise ValueError(f"Unsupported parameter type: {ptype}")

                    param.set_value(new_value)
                if self.is_new(solution, pendingSolutions, finishedSolutions):
                    break
            else:
               raise RuntimeError(f"Failed to generate a new unique solution after {self._max_attempts} attempts")

        except:
            self._runtime.logger.exception("Error creating random solution")
            raise

        solution.setParameters(params)
        solution.print()

        return solution

    """
    This function is used to check the value of the best local solution. This
    will be used to decide whether an employed bee becomes a scout
    """
    def getBestLocalValue(self):
        return self._bestLocalSolution.getValue()

    """
    Allows to modify the best local solution. When a scout generates a new
    a new solution after one solution has been abandoned, it replaces the
    best local solution of the employed by this new solution
    """
    def setSolution(self, solution):
        self._bestLocalSolution = solution
        self._bestLocalInitialised = True

    """
    This function allows to create a random number between start and
    stop, using a step of step
    for example, we can call it like randrange_float (2.5, 4.0, 0.5) and
    it will generate random numbers in the set 2.5, 3, 3.5, 4.0
    """
    def randrange_float(self, start, stop, step):
        if start>stop:
            start, stop = stop, start
        if start==stop:
            return start
        return random.randint(0, int(abs((stop - start) / step))) * step + start
"""
Employed bees
"""

class Employed (BeeBase):
    def __init__(self, runtime, comms, matrix, change, useMatrix):
        runtime.logger.info("Creating employed bee")
        super().__init__(runtime, comms, matrix)
        #list of neighbours of the current best local solution. This list is
        #used to create new solutions
        self._neighbours = []
        self._probEmployedChange = change
        self._useMatrix = useMatrix
        return

    def getSolutionBasedOnMatrix(self, solution):
        if not self._useMatrix:
            return solution
        values = self._matrix._repr_()
        with open("matrix.txt", 'w') as fileMat:
            fileMat.write(values)
        solutionCopy = solution
        try:
            parameters = solutionCopy.getParameters()
            numCols = self._matrix.getNumCols()
            for i in range(len(parameters)):
                sumRow = 0.0
                for j in range(numCols):
                    sumRow += self._matrix.getitem(i, j)
                if sumRow == numCols:
                    continue
                #randomly select a position in the row. The larger the value, the
                #higher the possibility for selecting a given row
                val = random.uniform(numCols, sumRow)
                tempSum = 0.0
                selectedPos = -1
                for j in range(numCols):
                    tempSum += self._matrix.getitem(i, j)
                    if tempSum >= val:
                        selectedPos = j
                        break
                if selectedPos == -1:
                    self._runtime.logger.warning("getSolutionBasedOnMatrix couldn't select a position. " + str(val) + " -- " + str(sumRow))
                value = float(parameters[i].get_min_value()) + float(selectedPos) * float(parameters[i].get_gap())
                parameters[i].set_value(value)
            solutionCopy.setParameters(parameters)
        except Exception as e:
            self._runtime.logger.error("SolverDAB (" + str(sys.exc_info()[2].tb_lineno) + "). " + str(e))
        return solutionCopy

    def createNewCandidate(
            self, 
            pendingSolutions,
            finishedSolutions,
            matrix,
            topSolutions,
            totalSumGoodSolutions
        ):
        solution = None

        try:
            # this is the one that has to use the probMatrix
            self._runtime.logger.info('create new candidate employed')

            if not self.bestLocalInitialised():
                solution = self.createRandomSolution(
                    pendingSolutions,
                    finishedSolutions
                )
                return solution, -1

            solution = self.getBestLocalSolution()

            if self._useMatrix:
                if random.randint(0, 10) == 0:
                    solution = self.getSolutionBasedOnMatrix(solution)
                    return solution, -1

            for _ in range(self._max_attempts):
                parameters = solution.getParameters()

                for param in parameters:
                    val = random.randint(0, self._probEmployedChange)

                    if val != 0:
                        continue

                    ptype = param.get_type()
                    new_value = None

                    if ptype is ParamType.STRING:
                        continue

                    elif ptype is ParamType.FLOAT:
                        currentVal = param.get_value()

                        gap = abs(param.get_gap())

                        minVal = currentVal - 10.0 * gap
                        maxVal = currentVal + 10.0 * gap

                        minVal = max(param.get_min_value(), minVal)
                        maxVal = min(param.get_max_value(), maxVal)

                        minVal, maxVal = sorted((minVal, maxVal))

                        if minVal == maxVal:
                            new_value = minVal
                        else:
                            if gap == 0.0:
                                new_value = random.uniform(minVal, maxVal)
                            else:
                                new_value = self.randrange_float(
                                    minVal,
                                    maxVal,
                                    param.get_gap()
                                )

                    elif ptype is ParamType.BOOL:
                        new_value = random.choice((True, False))

                    elif ptype is ParamType.INT:
                        currentVal = param.get_value()
                        gap = abs(param.get_gap())

                        if random.randint(0, 10) == 0:
                            minVal = currentVal - 10 * gap
                            maxVal = currentVal + 10 * gap
                        else:
                            minVal = currentVal - 5 * gap
                            maxVal = currentVal + 5 * gap

                        minVal = max(param.get_min_value(), minVal)
                        maxVal = min(param.get_max_value(), maxVal)

                        minVal, maxVal = sorted((minVal, maxVal))

                        if minVal == maxVal:
                            new_value = minVal
                        else:
                            new_value = random.randint(
                                int(minVal),
                                int(maxVal)
                            )

                    else:
                        raise ValueError(
                            f"Unsupported parameter type: {ptype}"
                        )

                    currentVal = param.get_value()

                    if new_value != currentVal:
                        param.set_value(new_value)

                solution.setParameters(parameters)

                if self.is_new(
                    solution,
                    pendingSolutions,
                    finishedSolutions
                ):
                    return solution, -1

            raise RuntimeError(
                f"Failed to generate a new unique solution "
                f"after {self._max_attempts} attempts"
            )

        except Exception as e:
            self._runtime.logger.exception(
                f"SolverDAB exception: {e}"
            )
            raise


"""
Scout bees
"""


class Scout (BeeBase):
    def __init__(self, runtime, comms, matrix):
        runtime.logger.info("Creating scout bee")
        super().__init__(runtime, comms, matrix)
        return

    """
    Creates a new random solution
    Extracts the parameters that can be modified, and generates a new
    value for each parameter considering the min and max values of that
    parameter
    """
    def createNewCandidate(
            self, 
            pendingSolutions: SolutionsQueue,
            finishedSolutions: SolutionsQueue,
            matrix: Matrix,
            topSolutions: SolutionsQueue,
            totalSumGoodSolutions: float
        ):
        solution = None
        try:
            self._runtime.logger.info('create new candidate scout')
            solution = self.createRandomSolution(pendingSolutions, finishedSolutions)
            return solution, -1
        except Exception as e:
            self._runtime.logger.exception(f"SolverDAB exception on line {e.__traceback__.tb_lineno}: {str(e)}")
            raise


"""
Onlooker bees
"""
class Onlooker (BeeBase):
    def __init__(self, runtime: GlobalRuntime, comms: GlobalComms, matrix: Matrix, modFactor, probChange):
        runtime.logger.info("Creating onlooker bee")
        super().__init__(runtime, comms, matrix)
        self._modFactor = modFactor
        #BeeBase._init_(self, runtime)
        self._probOnlookerChange = probChange
        return

    def createNewCandidate(
        self,
        pendingSolutions: SolutionsQueue,
        finishedSolutions: SolutionsQueue,
        matrix: Matrix,
        topSolutions: SolutionsQueue,
        totalSumGoodSolutions: float
    ):
        self._runtime.logger.info('create new candidate onlooker')

        val = random.uniform(0.0, totalSumGoodSolutions)

        solutionTuple = topSolutions.get_tuple_on_priority_by_value(val)
        solution = solutionTuple[0]

        if solution is None:
            self._runtime.logger.debug(
                "Onlooker. Couldn't select a solution "
                "from the list of finished solutions"
            )
            return None, -1

        beeIdx = solutionTuple[2]

        try:
            for _ in range(self._max_attempts):

                for param in solution.getParameters():
                    val = random.randint(0, self._probOnlookerChange)

                    if val != 0:
                        continue

                    ptype = param.get_type()
                    new_value = None

                    if ptype is ParamType.STRING:
                        continue

                    elif ptype is ParamType.FLOAT:
                        minVal = param.get_min_value()
                        maxVal = param.get_max_value()

                        currentVal = param.get_value()

                        minNewVal = (
                            currentVal - self._modFactor * currentVal
                        )
                        maxNewVal = (
                            currentVal + self._modFactor * currentVal
                        )

                        minVal = max(minVal, minNewVal)
                        maxVal = min(maxVal, maxNewVal)

                        minVal, maxVal = sorted((minVal, maxVal))

                        if minVal == maxVal:
                            new_value = minVal

                        else:
                            gap = param.get_gap()

                            if not gap:
                                new_value = random.uniform(
                                    minVal,
                                    maxVal
                                )
                            else:
                                new_value = self.randrange_float(
                                    minVal,
                                    maxVal,
                                    gap
                                )

                    elif ptype is ParamType.BOOL:
                        new_value = random.choice((True, False))

                    elif ptype is ParamType.INT:
                        minVal = param.get_min_value()
                        maxVal = param.get_max_value()

                        currentVal = param.get_value()

                        gap = abs(param.get_gap())

                        minNewVal = int(currentVal - 2 * gap)
                        maxNewVal = int(currentVal + 2 * gap)

                        if minNewVal != currentVal:
                            minVal = max(minVal, minNewVal)

                        if maxNewVal != currentVal:
                            maxVal = min(maxVal, maxNewVal)

                        if minVal == maxVal:
                            minVal = maxVal - 1

                        minVal, maxVal = sorted((minVal, maxVal))

                        new_value = random.randint(
                            int(minVal),
                            int(maxVal)
                        )
                        if minVal == maxVal == currentVal:
                            continue # Prevents infinite loop in case the only possible value is the current one
                        while new_value == currentVal:
                            new_value = random.randint(
                                int(minVal),
                                int(maxVal)
                            )

                    else:
                        raise ValueError(
                            f"Unsupported parameter type: {ptype}"
                        )

                    if new_value != param.get_value():
                        param.set_value(new_value)

                if self.is_new(
                    solution,
                    pendingSolutions,
                    finishedSolutions
                ):
                    self._runtime.logger.debug(
                        "Onlooker. Selected a solution "
                        "from the list of finished solutions"
                    )

                    self._runtime.logger.debug(
                        "Top solutions queue size %d",
                        topSolutions.qSize()
                    )

                    return solution, beeIdx

            raise RuntimeError(
                f"Failed to generate a new unique solution "
                f"after {self._max_attempts} attempts"
            )

        except Exception as e:
            self._runtime.logger.exception(
                f"SolverDAB exception: {e}"
            )

        return None, None

"""
Solver DAB main class
"""


class SolverDAB (SolverBase):
    def __init__(self, runtime: GlobalRuntime, comms: GlobalComms):
        super().__init__(runtime, comms)
        self._runtime.logger.info(f"Initializing solver {self.__class__.__name__}")

        """
        probMatrix stores the probability for each parameter, for each
        value, to be selected. Everytime a new feasible solution is found,
        we increase the probability of the current value of each parameter
        """
        self._useMatrix = False
        self._probMatrix:Matrix | None = None
        #default values
        self._nEmployed = 0
        self._nOnlooker = 0
        self._bees = []
        self._scout:BeeBase | None = None
        self._exectime = 0
        self._pendingSize = 10
        self._iterAbandoned = 10
        self._probEmployedChange = 4
        self._onlookerModFactor = 0.5
        self._probOnlookerChange = 50
        self._maxNumTopSolutions = 100
        
        try:
            origin = -1

            self._totalSumGoodSolutions = 0.0

            self._requestsEnd = []
            self._requestsInput = []
            self._requestSolution = []
            for i in range(self._comms.size):
                self._requestSolution.append(MPI.REQUEST_NULL)

            self._dump = array('i', [0]) * 1

            self._bestSolution: SolutionBase
            self._bestGlobalSolution: SolutionBase

            if self._runtime.problem_type == ProblemType.FUSION:
                self._problem = ProblemFusion(self._runtime, self._comms)
                self._bestSolution = SolutionFusion(self._runtime, self._comms)
                self._bestGlobalSolution = SolutionFusion(self._runtime, self._comms)
            elif self._runtime.problem_type == ProblemType.NONSEPARABLE:
                self._problem = ProblemNonSeparable(self._runtime, self._comms)
                self._bestSolution = SolutionNonSeparable(self._runtime, self._comms)
                self._bestGlobalSolution = SolutionNonSeparable(self._runtime, self._comms)
            elif self._runtime.problem_type == ProblemType.CRISTINA:
                self._problem = ProblemCristina(self._runtime, self._comms)
                self._bestSolution = SolutionCristina(self._runtime, self._comms)
                self._bestGlobalSolution = SolutionCristina(self._runtime, self._comms)
            else:
               raise ValueError(
                    f"Unknown problem type: {self._runtime.problem_type}"
                )
            self._numParams = self._bestSolution.getNumberofParams()
            
            #if top solutions is not empty, that means we have a best solution from the previous execution
            try:
                if self._topSolutions.qSize() != 0:
                    self._bestSolution, value, origin = self._topSolutions.get_solution_tuple(False)
                    self._bestSolution.setValue(value)
            except Exception as e:
                self._runtime.logger.exception(f"SolverDAB. {e}")

            if self._comms.rank == 0:
                #parse arguments from the ini file
                try:
                    config = configparser.ConfigParser()
                    config.read(self._runtime.config_file)

                    if not config.has_section("Bees"):
                        raise ValueError("Missing [Bees] section in configuration file")

                    self._nEmployed = config.getint("Bees", "nemployed", fallback=self._nEmployed)
                    self._nOnlooker = config.getint("Bees", "nonlooker", fallback=self._nOnlooker)
                    self._onlookerModFactor = config.getfloat(
                        "Bees",
                        "onlookerModFactor",
                        fallback=self._onlookerModFactor,
                    )
                    self._iterAbandoned = config.getint(
                        "Bees",
                        "iterationsAbandoned",
                        fallback=self._iterAbandoned,
                    )
                    self._probEmployedChange = config.getint(
                        "Bees",
                        "probEmployedChange",
                        fallback=self._probEmployedChange,
                    )
                    self._probOnlookerChange = config.getfloat(
                        "Bees",
                        "probOnlookerChange",
                        fallback=self._probOnlookerChange,
                    )
                    self._useMatrix = config.getboolean(
                        "Bees",
                        "useProbMatrix",
                        fallback=self._useMatrix,
                    )

                    self._exectime = config.getint(
                        "Algorithm",
                        "time",
                        fallback=self._exectime,
                    )

                    self._pendingSize = config.getint(
                        "Algorithm",
                        "pendingSize",
                        fallback=self._pendingSize,
                    )

                    self._maxNumTopSolutions = config.getint(
                        "Algorithm",
                        "eliteQueue",
                        fallback=self._maxNumTopSolutions,
                    )

                except Exception:
                    self._runtime.logger.exception(
                        "SolverDAB: Problem reading DAB configuration from ini file"
                    )
                    raise
                if self._useMatrix:
                    self._probMatrix = Matrix(self._bestSolution.getMaxNumberofValues() + 1,
                         self._bestSolution.getNumberofParams(), 1.0)

                self._topSolutions.setMaxSize(self._maxNumTopSolutions)
                """
                Create bees
                """
                idxBees = 0
                for i in range(self._nEmployed):
                    self._bees.insert(idxBees, Employed(self._runtime, self._comms, self._probMatrix, self._probEmployedChange, self._useMatrix))
                    idxBees += 1
                self._runtime.logger.debug("Created " + str(self._nEmployed) + " employed bees")

                for i in range(self._nOnlooker):
                    self._bees.insert(idxBees, Onlooker(self._runtime, self._comms, self._probMatrix, self._onlookerModFactor, self._probOnlookerChange))
                    idxBees += 1
                self._runtime.logger.debug("Created " + str(self._nOnlooker) + " onlooker bees")

                try:
                    if origin != -1:
                        self._bees[i].setSolution(self._bestSolution)
                except:
                    pass
                """
                Create only one scout. The scout creates a random solution, so
                it is just called when needed
                """
                self._scout = Scout(self._runtime, self._comms, self._probMatrix)
                self._runtime.logger.debug("Created 1 scout bee")
                self.print_configuration()
        except Exception as e:
            self._runtime.logger.error("SolverDAB " + str(sys.exc_info()[2].tb_lineno) + " " + str(e))
            raise

    def print_configuration(self):
        self._runtime.logger.info("SolverDAB configuration:")
        self._runtime.logger.info(f"Number of scout bees: 1")
        self._runtime.logger.info(f"Number of employed bees: {self._nEmployed}")
        self._runtime.logger.info(f"Number of onlooker bees: {self._nOnlooker}")
        self._runtime.logger.info(f"Onlooker modification factor: {self._onlookerModFactor}")
        self._runtime.logger.info(f"Iterations before abandoning a solution: {self._iterAbandoned}")
        self._runtime.logger.info(f"Probability of change for employed bees: {self._probEmployedChange}")
        self._runtime.logger.info(f"Probability of change for onlooker bees: {self._probOnlookerChange}")
        self._runtime.logger.info(f"Use probability matrix: {self._useMatrix}")
        self._runtime.logger.info(f"Execution time (seconds): {self._exectime}")
        self._runtime.logger.info(f"Pending solutions queue size: {self._pendingSize}")
        self._runtime.logger.info(f"Maximum number of top solutions stored: {self._maxNumTopSolutions}")


    """
    Initializer method (if needed)
    """

    def initialize(self):
        self._runtime.logger.info("Initializing DAB solver")
        try:
            if self._runtime.comm_model == CommModelType.DRIVERWORKER:
                #initialises the lists of requests
                for i in range(self._comms.size):
                    self._requestsEnd.append(MPI.REQUEST_NULL)
                    self._requestsInput.append(MPI.REQUEST_NULL)
                for i in range(self._comms.size):
                    if i == self._comms.rank:
                        continue
                    self._requestsEnd[i] = self._comms.comm.Irecv(self._dump, source=i, tag=Tags.ENDSIM)
                    self._requestsInput[i] = self._comms.comm.Irecv(self._dump, source=i, tag=Tags.REQINPUT)

                while (self._pendingSolutions.qSize() < self._pendingSize):
                    self._runtime.logger.info("Creating initial solutions. Pending queue size: " + str(self._pendingSolutions.qSize()))
                    self._pendingSolutions.put_solution(
                                    self._scout.createNewCandidate(self._pendingSolutions,
                                                                   self._finishedSolutions,
                                                                   self._probMatrix,
                                                                   self._topSolutions,
                                                                   self._totalSumGoodSolutions)[0], -1.0, -1)
            self._runtime.logger.debug('created initial set of solutions')
        except:
            self._runtime.logger.exception("SolverDAB exception during initialization")
            raise
    
    """
    This function checks if the size of the pending queue is correct. If smaller,
    it creates new solutions
    """

    def checkPendingSolutionsQueue(self):
        while (self._pendingSolutions.qSize() < self._pendingSize):
            try:
                for bee in range(len(self._bees)):
                    self._runtime.logger.debug("Bee " + str(bee) + " putting solution on pending queue")
                    newSolution, beeIdx = self._bees[bee].createNewCandidate(
                            self._pendingSolutions, self._finishedSolutions,
                            self._probMatrix, self._topSolutions,
                            self._totalSumGoodSolutions)
                    if bee < self._nEmployed:
                        beeIdx = bee
                    if newSolution is None:
                        newSolution = self._scout.createNewCandidate(
                            self._pendingSolutions,
                            self._finishedSolutions,
                            self._probMatrix,
                            self._topSolutions,
                            self._totalSumGoodSolutions)[0]
                        self._pendingSolutions.put_solution(newSolution, -1.0, -1)
                    else:
                        self._pendingSolutions.put_solution(newSolution, -1.0, beeIdx)

                #Check if there are abandoned solutions
                for bee in range(self._nEmployed):
                    if self._bees[bee].getIter() > self._iterAbandoned:
                        self._runtime.logger.info("Bee " + str(bee) + ". Abandoning food source")
                        solution = self._scout.createNewCandidate(
                            self._pendingSolutions,
                            self._finishedSolutions,
                            self._probMatrix,
                            self._topSolutions,
                            self._totalSumGoodSolutions)[0]
                        self._bees[bee].setIter(0)
                        self._bees[bee].setSolution(solution)
                        self._runtime.logger.debug("Scout bee putting solution on pending queue")
                        self._pendingSolutions.put_solution(solution, -1.0, bee)
            except Exception as e:
                self._runtime.logger.error("SolverDAB " + str(sys.exc_info()[2].tb_lineno) + " " + str(e))

    """
    This function checks if there are workers waiting for solutions to be evaluated.
    """

    def checkWaitingForSolutions(self):
        status = MPI.Status()
        flag = False
        iters = 0
        while (not flag and iters < 3):
            idx, flag = MPI.Request.Testany(self._requestsInput, status)
            iters += 1

        while (flag and idx >= 0):
            if status.tag == Tags.REQINPUT:
                destination = status.source
                try:
                    self._runtime.logger.debug('DRIVER. Worker ' + str(destination) + ' was waiting for a solution')
                    #Sends the front of the pending Solutions queue
                    solTuple = self._pendingSolutions.get_solution_list()
                    if self._pendingSolutions.qSize() == 0:
                        self.checkPendingSolutionsQueue()
                    while len(solTuple) < 3:
                        solTuple = self._pendingSolutions.get_solution_list()
                        if (self._pendingSolutions.qSize() < 1):
                            self._pendingSolutions.put_solution(self._scout.createNewCandidate(
                                self._pendingSolutions, self._finishedSolutions,
                                self._probMatrix,
                                self._topSolutions,
                                self._totalSumGoodSolutions)[0], -1.0, -1)

                    beeIdx = array('i', [0]) * 1
                    buff = array('f', [0]) * self._numParams
                    try:
                        beeIdx[0] = solTuple[1]
                        #buff = solTuple[0].getParametersValues()
                        for i in range(len(buff)):
                            buff[i] = float(solTuple[2][i])
                            self._runtime.logger.debug("Val param (" + str(i) + "): " + str(buff[i]))
                    except Exception as e:
                        self._runtime.logger.error("SolverDAB (" + str(sys.exc_info()[2].tb_lineno) +
                                "): " + str(e))
                        continue
                    #sends the parameters
                    self._comms.comm.Isend([buff, MPI.FLOAT], destination, Tags.RECVFROMDRIVER)
                    #sends the index of the bee that created the solution
                    self._comms.comm.Isend([beeIdx, MPI.INT], destination, Tags.RECVFROMDRIVER)
                    #adds a request for receiving the solution
                    req = self._comms.comm.Irecv([self._dump, MPI.INT], destination, Tags.REQSENDINPUT)
                    self._requestSolution[destination] = req
                    #adds a request for sending more input
                    req = self._comms.comm.Irecv(self._dump, source=destination, tag=Tags.REQINPUT)
                    self._requestsInput[destination] = req
                    self._runtime.logger.info("DRIVER. Solution sent to worker " + str(destination))
                except Exception as e:
                    self._runtime.logger.error("DRIVER. WaitingForSolutions (" +
                                    str(sys.exc_info()[2].tb_lineno) + "). " + str(e))

            idx, flag = MPI.Request.Testany(self._requestsInput, status)

    """
    This function checks if there are workers waiting to send solutions to the driver
    """

    def receiveSolutions(self):
        status = MPI.Status()
        sourceIdx, flag = MPI.Request.Testany(self._requestSolution, status)

        while (flag and sourceIdx >= 0):
            source = status.source
            if (source < 0 or source >= len(self._requestSolution)):
                self._runtime.logger.critical("DRIVER. Invalid source: " + str(source))
            self._requestSolution[source] = MPI.REQUEST_NULL
            self._runtime.logger.debug('DRIVER. Receiving solution (worker ' + str(source) + ')')
            isNewBest = False
            try:
                self._runtime.logger.debug("DRIVER. Buffer size: " + str(self._numParams))
                buff = array('f', [0]) * self._numParams
                solVal = array('f', [0]) * 1
                beeIdx = array('i', [0]) * 1
                origin = status.source
                self._comms.comm.Recv(buff, origin, Tags.COMMSOLUTION)
                self._comms.comm.Recv(solVal, origin, Tags.COMMSOLUTION)
                self._comms.comm.Recv(beeIdx, origin, Tags.COMMSOLUTION)
            except Exception as e:
                self._runtime.logger.error("DRIVER (comm). " + str(e) + " line: " +
                           str(sys.exc_info()[2].tb_lineno))
            try:
                self._runtime.logger.info("SOLVERDAB. Received solution with value " + str(solVal[0]) + " from bee " + str(beeIdx[0]))
                if (
                        not math.isfinite(float(solVal[0]))
                        or float(solVal[0]) <= 0.0
                        or float(solVal[0]) >= self._runtime.max_valid_solution_value / 100.0
                    ):
                        continue
                #Add the solution to the list of best solutions (the method will implement the
                #priority list)
                solutionTemp = None
                try:
                    if self._runtime.problem_type == ProblemType.FUSION:
                        solutionTemp = SolutionFusion(self._runtime, self._comms)
                    elif self._runtime.problem_type == ProblemType.NONSEPARABLE:
                        solutionTemp = SolutionNonSeparable(self._runtime, self._comms)
                    elif self._runtime.problem_type == ProblemType.CRISTINA:
                        solutionTemp = SolutionCristina(self._runtime, self._comms)

                    if solutionTemp is None:
                        self._runtime.logger.error(f"Solution is None after creation (type {self._runtime.problem_type})")
                    else:
                        solutionTemp.setParametersValues(buff)
                    if self._useMatrix:
                        for i in range(self._probMatrix.getNumRows()):
                            for j in range(self._probMatrix.getNumCols()):
                                val = self._probMatrix.getitem(i, j)
                                newVal = max(1.0, val - 0.01)
                                self._probMatrix.setitem(i, j, newVal)

                        parameters = solutionTemp.getParameters()
                        for i in range(len(parameters)):
                            idx = (parameters[i].get_value() - parameters[i].get_min_value())
                            idx = idx / parameters[i].get_gap()
                            idx = round(idx)
                            idx = int(idx)
                            val = self._probMatrix.getitem(i, idx)
                            self._probMatrix.setitem(i, idx, val + 0.5)
                except Exception as e:
                    self._runtime.logger.error("SolverDAB. " + str(e) + " line: " + str(sys.exc_info()[2].tb_lineno))
                self._topSolutions.put_solution(solutionTemp, solVal[0], beeIdx[0], self._nEmployed)
                self._totalSumGoodSolutions = self._topSolutions.get_total_solutions_values()

                if ((self._runtime.objective == ObjectiveType.MAXIMIZE and float(solVal[0]) > float(self._bestSolution.getValue())) or
                    (self._runtime.objective == ObjectiveType.MINIMIZE and float(solVal[0]) < float(self._bestSolution.getValue()))):

                    isNewBest = True
                    self._runtime.logger.log(EXTRA_LOG, "New best solution found. Value " + str(solVal[0]) +
                                    " -- old " + str(self._bestSolution.getValue()) + ". Bee " + str(beeIdx[0]))

                    self._bestSolution.setValue(solVal[0])

                    self._bestSolution.setParametersValues(buff)
                    if self._runtime.solution_type == SolutionType.FUSION:
                        filenametime = "0"
                        try:
                            filenametime = datetime.now().strftime('%Y-%m-%d-%H:%M:%S:%f')[:-3]
                        except:
                            pass
                        self._bestSolution.prepare("input.best." + filenametime)
                        shutil.copyfile(str(origin) + '/threed1.tj' + str(origin), 'threed1.best.' + filenametime)
                        shutil.copyfile(str(origin) + '/wout_tj' + str(origin) + ".txt", 'wout.best.' + filenametime)
                        try:
                            shutil.copyfile(str(origin) + '/OUTPUT/results.av', 'results.best.' + filenametime)
                        except:
                            pass
            except Exception as e:
                self._runtime.logger.error("DRIVER (comm). " + str(e) + " line: " + str(sys.exc_info()[2].tb_lineno))

            try:
                solutionTemp = None
                if self._runtime.problem_type is ProblemType.FUSION:
                    solutionTemp = SolutionFusion(self._runtime, self._comms)
                elif self._runtime.problem_type is ProblemType.NONSEPARABLE:
                    solutionTemp = SolutionNonSeparable(self._runtime, self._comms)
                elif self._runtime.problem_type is ProblemType.CRISTINA:
                    solutionTemp = SolutionCristina(self._runtime, self._comms)
                else:
                    raise ValueError(f"Unknown problem type: {self._runtime.problem_type}")

                if solutionTemp is None:
                    self._runtime.logger.exception(f"Solution is None after creation (type {self._runtime.problem_type})")
                    raise
                else:
                    solutionTemp.setParametersValues(buff)

                    self._finishedSolutions.put_solution(solutionTemp, solVal[0], beeIdx[0])
                    self._runtime.logger.info("DRIVER. Solution (value " + str(solVal[0]) +
                                  ") added to the list of finished solutions")
                    if (float(solVal[0]) >= 0.0 and float(solVal[0])<(math.inf/100.0)):
                        if isNewBest:
                            parameters = solutionTemp.getParameters()
                            if (self._useMatrix):
                                try:
                                    for i in range(self._probMatrix.getNumRows()):
                                        for j in range(self._probMatrix.getNumCols()):
                                            val = self._probMatrix.getitem(i, j)
                                            newVal = max(1.0, val - 0.5)
                                            self._probMatrix.setitem(i, j, newVal)
                                    for i in range(len(parameters)):
                                        idx = (parameters[i].get_value() - parameters[i].get_min_value())
                                        idx = idx / parameters[i].get_gap()
                                        idx = round(idx)
                                        idx = int(idx)
                                        val = self._probMatrix.getitem(i, idx)
                                        self._probMatrix.setitem(i, idx, val + 5.0)
                                except Exception as e:
                                    self._runtime.logger.warning("DRIVER (fill matrix). " + str(e) +
                                       " line: " + str(sys.exc_traceback.tb_lineno))
                        #Update the best local solution in the bees
                        reset = False
                        if (int(beeIdx[0]) >= 0 and int(beeIdx[0]) < len(self._bees)):
                            if (float(solVal[0]) >= 0.0):
                                if ((self._runtime.objective == ObjectiveType.MAXIMIZE and float(solVal[0]) > float(self._bees[beeIdx[0]].getBestLocalValue())) or
                                    (self._runtime.objective == ObjectiveType.MINIMIZE and float(solVal[0]) < float(self._bees[beeIdx[0]].getBestLocalValue()))):
                                    self._runtime.logger.info("Bee " + str(beeIdx[0]) + ". Resetting counter")
                                    self._bees[beeIdx[0]].setIter(0)
                                    solutionTemp.setValue(solVal[0])
                                    self._runtime.logger.info("Bee " + str(beeIdx[0]) + ". Best local " + str(self._bees[beeIdx[0]].getBestLocalValue()) + " new best " + str(solVal[0]))
                                    self._bees[beeIdx[0]].setSolution(solutionTemp)
                                    reset = True
                        if not reset:
                            self._bees[beeIdx[0]].setIter(self._bees[beeIdx[0]].getIter() + 1)
                            self._runtime.logger.info("Bee " + str(beeIdx[0]) + ". Current iterations " + str(self._bees[beeIdx[0]].getIter()))
            except Exception as e:
                self._runtime.logger.error("DRIVER (receiveSolutions). " + str(e) +
                                   " line: " + str(sys.exc_info()[2].tb_lineno))

            self._runtime.logger.info('DRIVER. Received solution (worker ' + str(source) + ')')
            sourceIdx, flag = MPI.Request.Testany(self._requestSolution, status)

    """
    Main method. Implements the algorithm
    """

    def solve(self):
        self._runtime.logger.info('DAB solver started')

        if self._runtime.comm_model == CommModelType.DRIVERWORKER:
            while (not self.check_finish()):
                try:
                    #check if it has to create solutions
                    self.checkPendingSolutionsQueue()
                    #check if there are worker processes waiting for input
                    self.checkWaitingForSolutions()
                    #check if it has to receive solutions
                    self.receiveSolutions()

                    elapsedTime = time.time() - self._runtime.start_time
                    self._runtime.logger.debug(
                        "DRIVER. Elapsed time %.2f - Remaining %.2f",
                        elapsedTime,
                        self._runtime.max_execution_time - elapsedTime,
                    )
                except Exception as e:
                    self._runtime.logger.exception(f"SolverDAB exception: {e}")
                    time.sleep(1)
        else:
            self.runDistributed()

    def runDistributed(self):
        if (self._runtime.problem_type == ProblemType.FUSION):
            self._problem = ProblemFusion(self._runtime, self._comms)
        elif (self._runtime.problem_type == ProblemType.NONSEPARABLE):
            self._problem = ProblemNonSeparable(self._runtime, self._comms)
        elif (self._runtime.problem_type == ProblemType.CRISTINA):
            self._problem = ProblemCristina(self._runtime, self._comms)

        numParams = self._bestSolution.getNumberofParams()
        buff = array('f', [0]) * numParams
        solValue = array('f', [0]) * 1

        while (not self.check_finish()):
            for bee in range(len(self._bees)):
                self._runtime.logger.debug("Bee " + str(bee) + " putting solution on pending queue")
                newSolution, beeIdx = self._bees[bee].createNewCandidate(
                            self._pendingSolutions,
                            self._finishedSolutions,
                            self._probMatrix,
                            self._topSolutions,
                            self._totalSumGoodSolutions
                            )
                if bee < self._nEmployed:
                    beeIdx = bee
                if newSolution is None:
                    newSolution = self._scout.createNewCandidate(
                        self._pendingSolutions,
                        self._finishedSolutions,
                        self._probMatrix,
                        self._topSolutions,
                        self._totalSumGoodSolutions)[0]
                self._problem.solve(newSolution)
                solutionValue = float(newSolution.getValue())

                if (
                    not math.isfinite(solutionValue)
                    or solutionValue <= 0.0
                    or solutionValue >= self._runtime.max_valid_solution_value
                ):
                    continue
                self._totalSumGoodSolutions = self._topSolutions.get_total_solutions_values()
                if ((self._runtime.objective == ObjectiveType.MAXIMIZE and float(solutionValue) > float(self._bestSolution.getValue())) or
                    (self._runtime.objective == ObjectiveType.MINIMIZE and float(solutionValue) < float(self._bestSolution.getValue()))):

                    self._runtime.logger.log(EXTRA_LOG, "New best solution found. Value " + str(newSolution) +
                                   " -- old " + str(self._bestSolution.getValue()) + ". Bee " + str(beeIdx))

                    self._bestSolution = newSolution

                    if ((self._runtime.objective == ObjectiveType.MAXIMIZE and float(solutionValue) > float(self._bestGlobalSolution.getValue())) or
                        (self._runtime.objective == ObjectiveType.MINIMIZE and float(solutionValue) < float(self._bestGlobalSolution.getValue()))):
                        self._bestGlobalSolution = self._bestSolution

                    buff = self._bestSolution.getParametersValues()
                    solValue[0] = solutionValue

                    if self._runtime.problem_type == ProblemType.FUSION:
                        filenametime = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]

                        self._bestSolution.prepare(f"input.best.{filenametime}")
                        shutil.copy2(
                            f"{beeIdx}/threed1.tj{beeIdx}",
                            f"threed1.best.{filenametime}",
                        )
                        shutil.copy2(
                            f"{beeIdx}/wout_tj{beeIdx}.txt",
                            f"wout.best.{filenametime}",
                        )
                        try:
                            shutil.copy2(
                                f"{beeIdx}/OUTPUT/results.av",
                                f"results.best.{filenametime}",
                            )
                        except OSError:
                            pass

            #Check if there are abandoned solutions
            for bee in range(self._nEmployed):
                if (self._bees[bee].getIter() > self._iterAbandoned):
                    self._runtime.logger.info("Bee " + str(bee) + ". Abandoning food source")
                    newSolution = self._scout.createNewCandidate(
                        self._pendingSolutions,
                        self._finishedSolutions,
                        self._probMatrix,
                        self._topSolutions,
                        self._totalSumGoodSolutions
                    )[0]
                    self._bees[bee].setIter(0)
                    self._bees[bee].setSolution(newSolution)
                    self._problem.solve(newSolution)
                    solutionValue = float(newSolution.getValue())

                    if (
                        not math.isfinite(solutionValue)
                        or solutionValue <= 0.0
                        or solutionValue >= self._runtime.max_valid_solution_value / 100.0
                    ):
                        continue

                    if ((self._runtime.objective == ObjectiveType.MAXIMIZE and
                        float(solutionValue) > float(self._bestSolution.getValue())) or
                        (self._runtime.objective == ObjectiveType.MINIMIZE and
                        float(solutionValue) < float(self._bestSolution.getValue()))):


                        self._runtime.logger.log(EXTRA_LOG, "New best solution found. Value " + str(newSolution) +
                                       " -- old " + str(self._bestSolution.getValue()) + ". Bee " + str(beeIdx))

                        self._bestSolution = newSolution

                        if ((self._runtime.objective == ObjectiveType.MAXIMIZE and float(solutionValue) > float(self._bestGlobalSolution.getValue())) or
                            (self._runtime.objective == ObjectiveType.MINIMIZE and float(solutionValue) < float(self._bestGlobalSolution.getValue()))):
                            self._bestGlobalSolution = self._bestSolution

                        buff = self._bestSolution.getParametersValues()
                        solValue[0] = solutionValue

                        if self._runtime.problem_type == ProblemType.FUSION:
                            filenametime = datetime.now().strftime('%Y-%m-%d-%H%M%S-%f')[:-3]

                            self._bestSolution.prepare("input.best." + filenametime)

                            shutil.copy2(
                                str(beeIdx) + '/threed1.tj' + str(beeIdx),
                                'threed1.best.' + filenametime,
                            )

                            shutil.copy2(
                                str(beeIdx) + '/wout_tj' + str(beeIdx) + ".txt",
                                'wout.best.' + filenametime,
                            )

                            try:
                                shutil.copy2(
                                    str(beeIdx) + '/OUTPUT/results.av',
                                    'results.best.' + filenametime,
                                )
                            except OSError:
                                pass
                    self._runtime.logger.debug("Scout bee putting solution on pending queue")
        return

    def check_finish(self):
        try:
            #first check if it's too early to finish
            elapsedTime = time.time() - self._runtime.start_time
            if elapsedTime + 300 < self._runtime.max_execution_time:
                return False
            all_null = all(
                request == MPI.REQUEST_NULL
                for request in self._requestsEnd
            )
            if (all_null):
                self._runtime.logger.info("SolverDAB[Driver]. All workers have finished")
                return True
            status = MPI.Status()
            idx, flag = MPI.Request.Testany(self._requestsEnd, status)
            if (flag and idx >= 0):
                source = status.source
                self._requestsEnd[source] = MPI.REQUEST_NULL
                self._runtime.logger.info(f'SolverDAB. Received a termination request from worker {source}')
            return False
        except Exception as e:
            self._runtime.logger.exception(f"SolverDAB exception: {e}")
            return True

    def finish(self):
        self._pendingSolutions.write_all_solutions()
        self._runtime.logger.info('DAB Driver finished')
