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

__author__ = ' AUTHORS:     Antonio Gomez (antonio.gomez@csiro.au)'


__version__ = ' REVISION:   1.0  -  15-01-2014'

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

from mpi4py import MPI

import sys
import random
import shutil
import time

from SolverBase import SolverBase
from ProblemFusion import ProblemFusion
from ProblemNonSeparable import ProblemNonSeparable
from SolutionFusion import SolutionFusion
from SolutionNonSeparable import SolutionNonSeparable
import Utils as u
import ConfigParser
import SolutionsQueue as solQueue

from array import array

"""
Base class for bees
"""

"""
Still pending: when we have evaluated a solution, we have to find the bee
that created that solution and set the value for that solution in the bee
"""


class BeeBase (object):
    def __init__(self, ProblemType, infile):
        random.seed()
        self.__solutionType = 0
        self.__problem = None
        self.__bestLocalSolution = None
        self.__bestLocalInitialised = False
        #Number of iterations since the local solution
        #was created
        self.__itersinceLastUpdate = 0

        if (ProblemType == u.problemType.FUSION):
            self.__problem = ProblemFusion()
            self.__solutionType = u.solutionType.FUSION
            self.__bestLocalSolution = SolutionFusion(infile)
            u.logger.info("Best local solution initialized " + str(self.__bestLocalSolution))
        elif (ProblemType == u.problemType.NONSEPARABLE):
            self.__problem = ProblemNonSeparable()
            self.__solutionType = u.solutionType.NONSEPARABLE
            self.__bestLocalSolution = SolutionNonSeparable(infile)
        if (u.objective == u.objectiveType.MAXIMIZE):
            self.__bestLocalSolution.setValue(-u.infinity)
        else:
            self.__bestLocalSolution.setValue(u.infinity)
        return

    def getIter(self):
        return self.__itersinceLastUpdate

    def setIter(self, val):
        self.__itersinceLastUpdate = val

    def getBestLocalSolution(self):
        return self.__bestLocalSolution

    def bestLocalInitialised(self):
        return self.__bestLocalInitialised

    def createNewCandidate(self, probMatrix, finishedSolutions):
        u.logger.error('Solver DAB. Create new candidate base')
        raise NotImplementedError("Abstract bee (calling create\
                                   new candidate)")

    """
    Creates a new random solution
    Extracts the parameters that can be modified, and generates a new
    value for each parameter considering the min and max values of that
    parameter
    """
    def createRandomSolution(self):
        u.logger.info('create new candidate scout')
        solution = self.getBestLocalSolution()
        params = solution.getParameters()
        u.logger.debug('number of parameters: ' + str(len(params)))
        for i in range(len(params)):
            ptype = params[i].get_type()
            newVal = None
            if (ptype == "double") or (ptype == "float"):
                minVal = params[i].get_min_value()
                maxVal = params[i].get_max_value()
                if (minVal == maxVal):
                    newVal = minVal
                else:
                    if (minVal > maxVal):
                        minVal, maxVal = maxVal, minVal
                    if (params[i].get_gap() == 0.0):
                        newVal = random.uniform(minVal, maxVal)
                    else:
                        newVal = self.randrange_float(minVal, maxVal, params[i].get_gap())
            elif (ptype == "bool"):
                val = random.randint(0, 1)
                newVal = (val == 0)
            else:
                minVal = params[i].get_min_value()
                maxVal = params[i].get_max_value()
                if (minVal == maxVal):
                    newVal = minVal
                else:
                    if (minVal > maxVal):
                        minVal, maxVal = maxVal, minVal
                    newVal = random.randint(minVal, maxVal)
            params[i].set_value(newVal)
        solution.setParameters(params)
        return solution

    """
    This function is used to check the value of the best local solution. This
    will be used to decide whether an employed bee becomes a scout
    """
    def getBestLocalValue(self):
        return self.__bestLocalSolution.getValue()

    """
    Allows to modify the best local solution. When a scout generates a new
    a new solution after one solution has been abandoned, it replaces the
    best local solution of the employed by this new solution
    """
    def setSolution(self, solution):
        self.__bestLocalSolution = solution
        self.__bestLocalInitialised = True

    """
    This function allows to create a random number between start and
    stop, using a step of step
    for example, we can call it like randrange_float (2.5, 4.0, 0.5) and
    it will generate random numbers in the set 2.5, 3, 3.5, 4.0
    """
    def randrange_float(self, start, stop, step):
        return random.randint(0, int((stop - start) / step)) * step + start
"""
Employed bees
"""


class Employed (BeeBase):
    def __init__(self, problemType, infile, change, useMatrix):
        BeeBase.__init__(self, problemType, infile)
        #list of neighbours of the current best local solution. This list is
        #used to create new solutions
        self.__neighbours = []
        self.__probEmployedChange = change
        self.__useMatrix = useMatrix
        return

    def getSolutionBasedOnMatrix(self, solution, probMatrix):
        if (not self.__useMatrix):
            return solution
        values = probMatrix.__repr__()
        fileMat = open("matrix.txt", 'w')
        fileMat.write(values)
        fileMat.close()
        solutionCopy = solution
        try:
            parameters = solutionCopy.getParameters()
            numCols = probMatrix.getNumCols()
            for i in range(len(parameters)):
                sumRow = 0.0
                for j in range(numCols):
                    sumRow += probMatrix.getitem(i, j)
                if (sumRow == numCols):
                    continue
                #randomly select a position in the row. The larger the value, the
                #higher the possibility for selecting a given row
                val = random.uniform(numCols, sumRow)
                tempSum = 0.0
                selectedPos = -1
                for j in range(numCols):
                    tempSum += probMatrix.getitem(i, j)
                    if (tempSum >= val):
                        selectedPos = j
                        break
                if (selectedPos == -1):
                    u.logger.warning("getSolutionBasedOnMatrix couldn't select a position. " + str(val) + " -- " + str(sumRow))
                value = float(parameters[i].get_min_value()) + float(selectedPos) * float(parameters[i].get_gap())
                parameters[i].set_value(value)
            solutionCopy.setParameters(parameters)
        except Exception, e:
            u.logger.error("SolverDAB (" + str(sys.exc_traceback.tb_lineno) + "). " + str(e))
        return solutionCopy

    def createNewCandidate(self, probMatrix, totalSumGoodSolutions, topSolutions=None):
        #this is the one that has to use the probMatrix
        u.logger.info('create new candidate employed')

        if (not self.bestLocalInitialised()):
            solution = self.createRandomSolution()
            return solution, -1

        solution = self.getBestLocalSolution()
        if (self.__useMatrix):
            if (random.randint(0, 10) == 0):
                solution = self.getSolutionBasedOnMatrix(solution, probMatrix)
                return solution, -1
        isNew = False
        while (not isNew):
            parameters = solution.getParameters()
            for i in range(len(parameters)):
                val = random.randint(0, self.__probEmployedChange)
                if (val != 0):
                    continue
                ptype = parameters[i].get_type()
                newVal = None
                if (ptype == "double") or (ptype == "float"):
                    #minVal = parameters[i].get_min_value()
                    #maxVal = parameters[i].get_max_value()
                    currentVal = parameters[i].get_value()
                    minVal = currentVal - 10.0 * parameters[i].get_gap()
                    maxVal = currentVal + 10.0 * parameters[i].get_gap()
                    minVal = max(parameters[i].get_min_value(), minVal)
                    maxVal = min(parameters[i].get_max_value(), maxVal)
                    if (minVal == maxVal):
                        newVal = minVal
                    else:
                        if (minVal > maxVal):
                            minVal, maxVal = maxVal, minVal
                        if (parameters[i].get_gap() == 0.0):
                            newVal = random.uniform(minVal, maxVal)
                        else:
                            newVal = self.randrange_float(minVal, maxVal, parameters[i].get_gap())
                elif (ptype == "bool"):
                    val = random.randint(0, 1)
                    newVal = (val == 0)
                else:
                    currentVal = parameters[i].get_value()
                    if (random.randint(0, 10) == 0):
                        minVal = currentVal - 10 * parameters[i].get_gap()
                        maxVal = currentVal + 10 * parameters[i].get_gap()
                    else:
                        minVal = currentVal - 5 * parameters[i].get_gap()
                        maxVal = currentVal + 5 * parameters[i].get_gap()
                    #minVal = p.get_min_value()
                    #maxVal = p.get_max_value()
                    minVal = max(parameters[i].get_min_value(), minVal)
                    maxVal = min(parameters[i].get_max_value(), maxVal)
                    if (minVal == maxVal):
                        newVal = minVal
                    else:
                        if (minVal > maxVal):
                            minVal, maxVal = maxVal, minVal
                        newVal = random.randint(minVal, maxVal)

                currentVal = parameters[i].get_value()
                if (newVal != currentVal):
                    isNew = True
                    parameters[i].set_value(newVal)
            solution.setParameters(parameters)
            parameters = solution.getParameters()
                #Here: go through the parameters of the solution and change those
                #parameters considering the min and max values of each parameter,
                #the probMatrix, and the self.__modFactor value
        return solution, -1

"""
Scout bees
"""


class Scout (BeeBase):
    def __init__(self, problemType, infile):
        BeeBase.__init__(self, problemType, infile)
        return

    """
    Creates a new random solution
    Extracts the parameters that can be modified, and generates a new
    value for each parameter considering the min and max values of that
    parameter
    """
    def createNewCandidate(self, probMatrix, topSolutions=None):
        u.logger.info('create new candidate scout')
        solution = self.createRandomSolution()
        return solution, -1
        """
        solution = self.getBestLocalSolution()
        params = solution.getParameters()
        u.logger.debug('number of parameters: ' + str(len(params)))
        for i in range(len(params)):
            ptype = params[i].get_type()
            newVal = None
            if (ptype == "double") or (ptype == "float"):
                minVal = params[i].get_min_value()
                maxVal = params[i].get_max_value()
                if (params[i].get_gap()==0.0):
                    newVal = random.uniform (minVal, maxVal)
                else:
                    newVal = self.randrange_float(minVal, maxVal, params[i].get_gap())
            elif (ptype == "bool"):
                val = random.randint (0,1)
                newVal = (val==0)
            else:
                minVal = params[i].get_min_value()
                maxVal = params[i].get_max_value()
                newVal = random.randint (minVal, maxVal)
            params[i].set_value(newVal)
        solution.setParameters(params)
        return solution, -1
        """

"""
Onlooker bees
"""


class Onlooker (BeeBase):
    def __init__(self, problemType, infile, modFactor, probChange):
        self.__modFactor = modFactor
        BeeBase.__init__(self, problemType, infile)
        self.__probOnlookerChange = probChange
        return

    def createNewCandidate(self, probMatrix, totalSumGoodSolutions, topSolutions):
        u.logger.info('create new candidate onlooker')
        val = random.uniform(0.0, totalSumGoodSolutions)
        solutionTuple = topSolutions.GetTupleOnPriorityByValue(val)
        solution = solutionTuple[0]

        if (solution is None):
            u.logger.debug("Onlooker. Couldn't select a solution from the list of finished solutions")
            return None, -1
        beeIdx = solutionTuple[2]
        isNew = False
        try:
            while(not isNew):
                for p in solution.getParameters():
                    val = random.randint(0, self.__probOnlookerChange)
                    if (val != 0):
                        continue
                    isNew = True
                    ptype = p.get_type()
                    newVal = None
                    if (ptype == "double") or (ptype == "float"):
                        minVal = p.get_min_value()
                        maxVal = p.get_max_value()
                        currentVal = p.get_value()
                        minNewVal = currentVal - self.__modFactor * currentVal
                        maxNewVal = currentVal + self.__modFactor * currentVal
                        minVal = max(minVal, minNewVal)
                        maxVal = min(maxVal, maxNewVal)
                        if (minVal > maxVal):
                            minVal, maxVal = maxVal, minVal
                        if (minVal == maxVal):
                            newVal = minVal
                        else:
                            if (not p.get_gap()):
                                newVal = random.uniform(minVal, maxVal)
                            else:
                                newVal = self.randrange_float(minVal, maxVal, p.get_gap())
                    elif (ptype == "bool"):
                        val = random.randint(0, 1)
                        newVal = (val == 0)
                    else:
                        minVal = p.get_min_value()
                        maxVal = p.get_max_value()
                        currentVal = p.get_value()
                        minNewVal = int(currentVal - 2 * p.get_gap())
                        maxNewVal = int(currentVal + 2 * p.get_gap())
                        if (minNewVal != currentVal):
                            minVal = max(minVal, minNewVal)
                        if (maxNewVal != currentVal):
                            maxVal = min(maxVal, maxNewVal)
                        if (minVal == maxVal):
                            minVal = maxVal - 1
                        if (minVal > maxVal):
                            minVal, maxVal = maxVal, minVal
                        newVal = random.randint(minVal, maxVal)
                        while (newVal == currentVal):
                            newVal = random.randint(minVal, maxVal)
                    p.set_value(newVal)
                    #Here: go through the parameters of the solution and change those
                    #parameters considering the min and max values of each parameter,
                    #the probMatrix, and the self.__modFactor value
            #except Exception, e:
            #    u.logger.error("SolverDAB " + str(sys.exc_traceback.tb_lineno)+ " " +str(e))
            u.logger.debug("Onlooker. Selected a solution from the list of finished solutions")
            u.logger.debug("Top solutions queue size " + str(topSolutions.qSize()))
            return solution, beeIdx
        except Exception, e:
            u.logger.error("SolverDAB (" + str(sys.exc_traceback.tb_lineno) +
                                  "). " + str(e))
        return None, None

"""
Solver DAB main class
"""


class SolverDAB (SolverBase):
    def __init__(self, problemType, infile, configfile):
        try:
            u.logger.info("SolverDAB init")
            u.starttime = time.time()
            u.comm = MPI.COMM_WORLD
            u.rank = u.comm.Get_rank()
            u.size = u.comm.Get_size()

            origin = -1

            self.__totalSumGoodSolutions = 0.0

            self.__requestsEnd = []
            self.__requestsInput = []
            self.__requestSolution = []
            self.__problemType = problemType
            self.__infile = infile
            for i in range(u.size):
                self.__requestSolution.append(MPI.REQUEST_NULL)

            self.__dump = array('i', [0]) * 1

            SolverBase.__init__(self, problemType, infile, configfile)
            self.__bestSolution = None
            self.__globalBestSolution = None

            if (self.__problemType == u.problemType.FUSION):
                self.__problem = ProblemFusion()
                self.__bestSolution = SolutionFusion(self.__infile)
                self.__globalBestSolution = SolutionFusion(self.__infile)
            elif (self.__problemType == u.problemType.NONSEPARABLE):
                self.__problem = ProblemNonSeparable()
                self.__bestSolution = SolutionNonSeparable(self.__infile)
                self.__globalBestSolution = SolutionNonSeparable(self.__infile)
            else:
                u.logger.critical("SolverDAB (" + str(sys.exc_traceback.tb_lineno) +
                                  "). Unknown problem type " + str(problemType))
                sys.exit(-1)
            self.__numParams = self.__bestSolution.getNumberofParams()

            """
            probMatrix stores the probability for each parameter, for each
            value, to be selected. Everytime a new feasible solution is found,
            we increase the probability of the current value of each parameter
            """
            self.__useMatrix = False
            self.__probMatrix = None

            #default values
            self.__nEmployed = 0
            self.__nOnlooker = 0
            self.__bees = []
            self.__scout = None
            self.__runtime = 0
            self.__pendingSize = 10
            self.__iterAbandoned = 10
            self.__probEmployedChange = 4
            self.__onlookerModFactor = 0.5
            self.__probOnlookerChange = 50
            self.__maxNumTopSolutions = 100

            self.__pendingSolutions = None
            self.__finishedSolutions = None
            self.__topSolutions = None

            if (problemType == u.problemType.FUSION):
                self.__finishedSolutions = solQueue.SolutionsQueue(
                                    "finished.queue", u.solutionType.FUSION, infile, True, True)
                self.__pendingSolutions = solQueue.SolutionsQueue(
                                    "pending.queue", u.solutionType.FUSION, infile, False)
                self.__topSolutions = solQueue.SolutionsQueue(
                                    "top.queue", u.solutionType.FUSION, infile, False, True)
            if (problemType == u.problemType.NONSEPARABLE):
                self.__finishedSolutions = solQueue.SolutionsQueue(
                                    "finishedNonSep.queue", u.solutionType.NONSEPARABLE, infile, True, True)
                self.__pendingSolutions = solQueue.SolutionsQueue(
                                    "pendingNonSep.queue", u.solutionType.NONSEPARABLE, infile, False)
                self.__topSolutions = solQueue.SolutionsQueue(
                                    "top.queue", u.solutionType.NONSEPARABLE, infile, False, True)
            #if top solutions is not empty, that means we have a best solution from the previous execution
            try:
                if (self.__topSolutions.qSize() != 0):
                    self.__bestSolution, value, origin = self.__topSolutions.GetSolutionTuple(False)
                    self.__bestSolution.setValue(value)
            except Exception, e:
                u.logger.warning("SolverDAB. " + str(e) + ". line " + str(sys.exc_traceback.tb_lineno))

            if (u.rank == 0):
                #parse arguments from the ini file
                try:
                    config = ConfigParser.ConfigParser()
                    config.read(configfile)
                    if (not config.has_section("Bees")):
                        u.logger.critical("Bees section not specified in the ini file")
                        sys.exit(-1)
                    if (config.has_option("Bees", "nemployed")):
                        val = config.get("Bees", "nemployed")
                        if (val != None):
                            self.__nEmployed = int(val)
                    if (config.has_option("Bees", "nonlooker")):
                        val = config.get("Bees", "nonlooker")
                        if (val != None):
                            self.__nOnlooker = int(val)
                    if (config.has_option("Bees", "onlookerModFactor")):
                        val = config.get("Bees", "onlookerModFactor")
                        if (val != None):
                            self.__onlookerModFactor = float(val)
                    if (config.has_option("Bees", "iterationsAbandoned")):
                        val = config.get("Bees", "iterationsAbandoned")
                        if (val != None):
                            self.__iterAbandoned = int(val)
                    if (config.has_option("Bees", "probEmployedChange")):
                        val = config.get("Bees", "probEmployedChange")
                        if (val != None):
                            self.__probEmployedChange = int(val)
                    if (config.has_option("Bees", "probOnlookerChange")):
                        val = config.get("Bees", "probOnlookerChange")
                        if (val != None):
                            self.__probOnlookerChange = float(val)
                    if (config.has_option("Bees", "useProbMatrix")):
                        val = config.getboolean("Bees", "useProbMatrix")
                        if (val != None):
                            self.__useMatrix = val

                    val = config.get("Algorithm", "time")
                    if (val != None):
                        self.__runtime = int(val)
                    val = config.get("Algorithm", "pendingSize")
                    if (val != None):
                        self.__pendingSize = int(val)
                    if (config.has_option("Algorithm", "eliteQueue")):
                        val = config.get("Algorithm", "eliteQueue")
                        if (val != None):
                            self.__maxNumTopSolutions = int(val)
                    if (config.has_option("Algorithm", "objective")):
                        val = config.get("Algorithm", "objective")
                        if (val != None):
                            if (val == "max"):
                                u.objective = u.objectiveType.MAXIMIZE
                            else:
                                u.objective = u.objectiveType.MINIMIZE
                except Exception, e:
                    u.logger.error("SolverDAB (" + str(sys.exc_traceback.tb_lineno) +
                                   "). Problem reading DAB configuration from the ini file. " +
                                   str(e))
                if (self.__useMatrix):
                    self.__probMatrix = u.Matrix(self.__bestSolution.getMaxNumberofValues() + 1,
                         self.__bestSolution.getNumberofParams(), 1.0)

                self.__topSolutions.setMaxSize(self.__maxNumTopSolutions)
                """
                Create bees
                """
                idxBees = 0
                for i in range(self.__nEmployed):
                    self.__bees.insert(idxBees, Employed(problemType, infile, self.__probEmployedChange, self.__useMatrix))
                    idxBees += 1
                u.logger.debug("Created " + str(self.__nEmployed) + " employed bees")

                for i in range(self.__nOnlooker):
                    self.__bees.insert(idxBees, Onlooker(problemType, infile,
                                            self.__onlookerModFactor, self.__probOnlookerChange))
                    idxBees += 1
                u.logger.debug("Created " + str(self.__nOnlooker) + " onlooker bees")

                try:
                    if (origin != -1):
                        self.__bees[i].setSolution(self.__bestSolution)
                except:
                    pass
                """
                Create only one scout. The scout creates a random solution, so
                it is just called when needed
                """
                self.__scout = Scout(problemType, infile)
                u.logger.debug("Created 1 scout bee")
        except Exception, e:
            u.logger.error("SolverDAB " + str(sys.exc_traceback.tb_lineno) + " " + str(e))

    """
    Initializer method (if needed)
    """

    def initialize(self):
        u.logger.info('DAB initializer')
        try:
            if (u.commModel == u.commModelType.MASTERSLAVE):
                #initialises the lists of requests
                for i in range(u.size):
                    self.__requestsEnd.append(MPI.REQUEST_NULL)
                    self.__requestsInput.append(MPI.REQUEST_NULL)
                for i in range(u.size):
                    if (i == u.rank):
                        continue
                    self.__requestsEnd[i] = u.comm.Irecv(self.__dump, source=i, tag=u.tags.ENDSIM)
                    self.__requestsInput[i] = u.comm.Irecv(self.__dump, source=i, tag=u.tags.REQINPUT)

                while (self.__pendingSolutions.qSize() < self.__pendingSize):
                    self.__pendingSolutions.PutSolution(
                                    self.__scout.createNewCandidate(self.__probMatrix)[0], -1.0, -1)
            u.logger.debug('created initial set of solutions')
        except Exception, e:
            u.logger.error("SolverDAB " + str(sys.exc_traceback.tb_lineno) + " " + str(e))

    """
    This function checks if the size of the pending queue is correct. If smaller,
    it creates new solutions
    """

    def checkPendingSolutionsQueue(self):
        while (self.__pendingSolutions.qSize() < self.__pendingSize):
            try:
                for bee in range(len(self.__bees)):
                    u.logger.debug("Bee " + str(bee) + " putting solution on pending queue")
                    newSolution, beeIdx = self.__bees[bee].createNewCandidate(
                            self.__probMatrix, self.__totalSumGoodSolutions, self.__topSolutions)
                    if (bee < self.__nEmployed):
                        beeIdx = bee
                    if (newSolution is None):
                        newSolution = self.__scout.createNewCandidate(self.__probMatrix)[0]
                        self.__pendingSolutions.PutSolution(newSolution, -1.0, -1)
                    else:
                        self.__pendingSolutions.PutSolution(newSolution, -1.0, beeIdx)

                #Check if there are abandoned solutions
                for bee in range(self.__nEmployed):
                    if (self.__bees[bee].getIter() > self.__iterAbandoned):
                        u.logger.info("Bee " + str(bee) + ". Abandoning food source")
                        solution = self.__scout.createNewCandidate(self.__probMatrix)[0]
                        self.__bees[bee].setIter(0)
                        self.__bees[bee].setSolution(solution)
                        u.logger.debug("Scout bee putting solution on pending queue")
                        self.__pendingSolutions.PutSolution(solution, -1.0, bee)
            except Exception, e:
                u.logger.error("SolverDAB " + str(sys.exc_traceback.tb_lineno) + " " + str(e))

    """
    This function checks if there are slaves waiting for solutions to be evaluated.
    """

    def checkWaitingForSolutions(self):
        status = MPI.Status()
        flag = False
        iters = 0
        while (not flag and iters < 3):
            idx, flag = MPI.Request.Testany(self.__requestsInput, status)
            iters += 1

        while (flag and idx >= 0):
            if (status.tag == u.tags.REQINPUT):
                destination = status.source
                try:
                    u.logger.debug('MASTER. Slave ' + str(destination) + ' was waiting for a solution')
                    #Sends the front of the pending Solutions queue
                    solTuple = self.__pendingSolutions.GetSolutionList()
                    if (self.__pendingSolutions.qSize() == 0):
                        self.checkPendingSolutionsQueue()
                    while (len(solTuple) < 3):
                        solTuple = self.__pendingSolutions.GetSolutionList()
                        if (self.__pendingSolutions.qSize() < 1):
                            self.__pendingSolutions.PutSolution(self.__scout.createNewCandidate(self.__probMatrix)[0], -1.0, -1)

                    beeIdx = array('i', [0]) * 1
                    buff = array('f', [0]) * self.__numParams
                    try:
                        beeIdx[0] = solTuple[1]
                        #buff = solTuple[0].getParametersValues()
                        for i in range(len(buff)):
                            buff[i] = float(solTuple[2][i])
                            u.logger.debug("Val param (" + str(i) + "): " + str(buff[i]))
                    except Exception, e:
                        u.logger.error("SolverDAB (" + str(sys.exc_traceback.tb_lineno) +
                                "): " + str(e))
                        continue
                    #sends the parameters
                    u.comm.Isend([buff, MPI.FLOAT], destination, u.tags.RECVFROMMASTER)
                    #sends the index of the bee that created the solution
                    u.comm.Isend([beeIdx, MPI.INT], destination, u.tags.RECVFROMMASTER)
                    #adds a request for receiving the solution
                    req = u.comm.Irecv([self.__dump, MPI.INT], destination, u.tags.REQSENDINPUT)
                    self.__requestSolution[destination] = req
                    #adds a request for sending more input
                    req = u.comm.Irecv(self.__dump, source=destination, tag=u.tags.REQINPUT)
                    self.__requestsInput[destination] = req
                    u.logger.info("MASTER. Solution sent to slave " + str(destination))
                except Exception, e:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    u.logger.error("MASTER. WaitingForSolutions (" +
                                    str(exc_tb.tb_lineno) + "). " + str(e))

            idx, flag = MPI.Request.Testany(self.__requestsInput, status)

    """
    This function checks if there are slaves waiting to send solutions to the master
    """

    def receiveSolutions(self):
        status = MPI.Status()
        sourceIdx, flag = MPI.Request.Testany(self.__requestSolution, status)
                
        while (flag and sourceIdx >= 0):
            source = status.source
            if (source < 0 or source >= len(self.__requestSolution)):
                u.logger.critical("MASTER. Invalid source: " + str(source))
            self.__requestSolution[source] = MPI.REQUEST_NULL
            u.logger.debug('MASTER. Receiving solution (slave ' + str(source) + ')')
            isNewBest = False
            try:
                u.logger.debug("MASTER. Buffer size: " + str(self.__numParams))
                buff = array('f', [0]) * self.__numParams
                solVal = array('f', [0]) * 1
                beeIdx = array('i', [0]) * 1
                origin = status.source
                u.comm.Recv(buff, origin, u.tags.COMMSOLUTION)
                u.comm.Recv(solVal, origin, u.tags.COMMSOLUTION)
                u.comm.Recv(beeIdx, origin, u.tags.COMMSOLUTION)
            except Exception, e:
                u.logger.error("MASTER (comm). " + str(e) + " line: " +
                           str(sys.exc_traceback.tb_lineno))
            try:
                if (float(solVal[0]) > 0.0 and float(solVal[0]) < u.infinity / 100):
                    #Add the solution to the list of best solutions (the method will implement the
                    #priority list)
                    solutionTemp = None
                    try:
                        if (self.__problemType == u.problemType.FUSION):
                            solutionTemp = SolutionFusion(self.__infile)
                        elif (self.__problemType == u.problemType.NONSEPARABLE):
                            solutionTemp = SolutionNonSeparable(self.__infile)

                        if (solutionTemp is None):
                            u.logger.error("Solution is None after creation (type " + str(self.__problemType) + ")")
                        else:
                            solutionTemp.setParametersValues(buff)
                        if (self.__useMatrix):
                            for i in range(self.__probMatrix.getNumRows()):
                                for j in range(self.__probMatrix.getNumCols()):
                                    val = self.__probMatrix.getitem(i, j)
                                    newVal = max(1.0, val - 0.01)
                                    self.__probMatrix.setitem(i, j, newVal)

                            parameters = solutionTemp.getParameters()
                            for i in range(len(parameters)):
                                idx = (parameters[i].get_value() - parameters[i].get_min_value())
                                idx = idx / parameters[i].get_gap()
                                idx = round(idx)
                                idx = int(idx)
                                val = self.__probMatrix.getitem(i, idx)
                                self.__probMatrix.setitem(i, idx, val + 0.5)
                    except Exception, e:
                        u.logger.error("SolverDAB. " + str(e) + " line: " + str(sys.exc_traceback.tb_lineno))
                    self.__topSolutions.PutSolution(solutionTemp, solVal[0], beeIdx[0], self.__nEmployed)
                    self.__totalSumGoodSolutions = self.__topSolutions.GetTotalSolutionsValues()
                    
                    if ((u.objective == u.objectiveType.MAXIMIZE and float(solVal[0]) > float(self.__bestSolution.getValue())) or
                        (u.objective == u.objectiveType.MINIMIZE and float(solVal[0]) < float(self.__bestSolution.getValue()))):
                        filenametime = "0"
                        try:
                            filenametime = time.strftime("%Y%m%d-%H%M%S", time.localtime())
                        except Exception, e:
                            u.logger.warning("MASTER. " + str(e) + " line: " + str(sys.exc_traceback.tb_lineno))

                        isNewBest = True
                        u.logger.log(u.extraLog, "New best solution found. Value " + str(solVal[0]) +
                                       " -- old " + str(self.__bestSolution.getValue()) + ". Bee " + str(beeIdx[0]))

                        self.__bestSolution.setValue(solVal[0])

                        self.__bestSolution.setParametersValues(buff)
                        if (self.__problemType == u.solutionType.FUSION):
                            self.__bestSolution.prepare("input.best." + filenametime)
                            shutil.copyfile(str(origin) + '/threed1.tj' + str(origin), 'threed1.best.' + filenametime)
                            shutil.copyfile(str(origin) + '/wout_tj' + str(origin) + ".txt", 'wout.best.' + filenametime)
                            try:
                                shutil.copyfile(str(origin) + '/OUTPUT/results.av', 'results.best.' + filenametime)
                            except:
                                pass
            except Exception, e:
                u.logger.error("MASTER (comm). " + str(e) + " line: " + str(sys.exc_traceback.tb_lineno))

            try:
                solutionTemp = None
                if (self.__problemType == u.problemType.FUSION):
                    solutionTemp = SolutionFusion(self.__infile)
                elif (self.__problemType == u.problemType.NONSEPARABLE):
                    solutionTemp = SolutionNonSeparable(self.__infile)

                if (solutionTemp is None):
                    u.logger.error("Solution is None after creation (type " + str(self.__problemType) + ")")
                else:
                    solutionTemp.setParametersValues(buff)

                    self.__finishedSolutions.PutSolution(solutionTemp, solVal[0], beeIdx[0])
                    u.logger.info("MASTER. Solution (value " + str(solVal[0]) +
                                  ") added to the list of finished solutions")
                    if (float(solVal[0]) > 0.0 and float(solVal[0])<(u.infinity/100.0)):
                        if (isNewBest):
                            parameters = solutionTemp.getParameters()
                            if (self.__useMatrix):
                                try:
                                    for i in range(self.__probMatrix.getNumRows()):
                                        for j in range(self.__probMatrix.getNumCols()):
                                            val = self.__probMatrix.getitem(i, j)
                                            newVal = max(1.0, val - 0.5)
                                            self.__probMatrix.setitem(i, j, newVal)
                                    for i in range(len(parameters)):
                                        idx = (parameters[i].get_value() - parameters[i].get_min_value())
                                        idx = idx / parameters[i].get_gap()
                                        idx = round(idx)
                                        idx = int(idx)
                                        val = self.__probMatrix.getitem(i, idx)
                                        self.__probMatrix.setitem(i, idx, val + 5.0)
                                except Exception, e:
                                    u.logger.warning("MASTER (fill matrix). " + str(e) +
                                       " line: " + str(sys.exc_traceback.tb_lineno))
                        #Update the best local solution in the bees
                        reset = False
                        if (int(beeIdx[0]) >= 0 and int(beeIdx[0]) < len(self.__bees)):
                            if (float(solVal[0]) >= 0.0):
                                if ((u.objective == u.objectiveType.MAXIMIZE and float(solVal[0]) > float(self.__bees[beeIdx[0]].getBestLocalValue())) or
                                    (u.objective == u.objectiveType.MINIMIZE and float(solVal[0]) < float(self.__bees[beeIdx[0]].getBestLocalValue()))):
                                    u.logger.info("Bee " + str(beeIdx[0]) + ". Resetting counter")
                                    self.__bees[beeIdx[0]].setIter(0)
                                    solutionTemp.setValue(solVal[0])
                                    u.logger.info("Bee " + str(beeIdx[0]) + ". Best local " + str(self.__bees[beeIdx[0]].getBestLocalValue()) + " new best " + str(solVal[0]))
                                    self.__bees[beeIdx[0]].setSolution(solutionTemp)
                                    reset = True
                        if not reset:
                            self.__bees[beeIdx[0]].setIter(self.__bees[beeIdx[0]].getIter() + 1)
                            u.logger.info("Bee " + str(beeIdx[0]) + ". Current iterations " + str(self.__bees[beeIdx[0]].getIter()))
            except Exception, e:
                u.logger.error("MASTER (receiveSolutions). " + str(e) +
                                   " line: " + str(sys.exc_traceback.tb_lineno))

            u.logger.info('MASTER. Received solution (slave ' + str(source) + ')')
            sourceIdx, flag = MPI.Request.Testany(self.__requestSolution, status)

    """
    Main method. Implements the algorithm
    """

    def solve(self):
        u.logger.info('DAB solver started')

        if (u.commModel == u.commModelType.MASTERSLAVE):
            while (not self.check_finish()):
                try:
                    #check if it has to create solutions
                    self.checkPendingSolutionsQueue()
                    #check if there are slave processes waiting for input
                    self.checkWaitingForSolutions()
                    #check if it has to receive solutions
                    self.receiveSolutions()

                    elapsedTime = time.time() - u.starttime
                    u.logger.debug("MASTER. Elapsed time " + str(elapsedTime) +
                                    " - Remaining " + str(self.__runtime - elapsedTime))
                except Exception, e:
                    u.logger.error("MASTER (solve). " + str(e) + " line: " +
                                   str(sys.exc_traceback.tb_lineno))
        else:
            self.runDistributed()

    def runDistributed(self):
        if (self.__problemType == u.problemType.FUSION):
            self.__problem = ProblemFusion()
        elif (self.__problemType == u.problemType.NONSEPARABLE):
            self.__problem = ProblemNonSeparable()

        numParams = self.__bestSolution.getNumberofParams()
        buff = array('f', [0]) * numParams
        solValue = array('f', [0]) * 1

        while (not self.check_finish()):
            for bee in range(len(self.__bees)):
                u.logger.debug("Bee " + str(bee) + " putting solution on pending queue")
                newSolution, beeIdx = self.__bees[bee].createNewCandidate(
                        self.__probMatrix, self.__totalSumGoodSolutions, self.__topSolutions)
                if (bee < self.__nEmployed):
                    beeIdx = bee
                if (newSolution is None):
                    newSolution = self.__scout.createNewCandidate(self.__probMatrix)[0]
                self.__problem.solve(newSolution)
                solutionValue = float(newSolution.getValue())

                if (solutionValue<=0.0 or solutionValue>u.infinity/100.0):
                    continue
                self.__totalSumGoodSolutions = self.__topSolutions.GetTotalSolutionsValues()
                if ((u.objective == u.objectiveType.MAXIMIZE and float(solutionValue) > float(self.__bestSolution.getValue())) or
                    (u.objective == u.objectiveType.MINIMIZE and float(solutionValue) < float(self.__bestSolution.getValue()))):
                    filenametime = "0"
                    try:
                        filenametime = time.strftime("%Y%m%d-%H%M%S", time.localtime())
                    except Exception, e:
                        u.logger.warning("MASTER. " + str(e) + " line: " + str(sys.exc_traceback.tb_lineno))

                    u.logger.log(u.extraLog, "New best solution found. Value " + str(newSolution) +
                                   " -- old " + str(self.__bestSolution.getValue()) + ". Bee " + str(beeIdx))

                    self.__bestSolution = newSolution

                    if ((u.objective == u.objectiveType.MAXIMIZE and float(solutionValue) > float(self.__bestGlobalSolution.getValue())) or
                        (u.objective == u.objectiveType.MINIMIZE and float(solutionValue) < float(self.__bestGlobalSolution.getValue()))):
                        self.__bestGlobalSolution = self.__bestSolution
                    
                    buff = self.__bestSolution.getParametersValues()
                    solValue[0] = solutionValue

                    """
                    for destination in range(u.size):
                        if (destination == u.rank):
                            continue
                        u.comm.Isend([buff, MPI.FLOAT], destination, u.tags.COMMSOLUTION)
                        u.comm.Isend([buff, MPI.FLOAT], destination, u.tags.COMMSOLUTION)
                    """

                    if (self.__problemType == u.solutionType.FUSION):
                        self.__bestSolution.prepare("input.best." + filenametime)
                        shutil.copyfile(str(beeIdx) + '/threed1.tj' + str(beeIdx), 'threed1.best.' + filenametime)
                        shutil.copyfile(str(beeIdx) + '/wout_tj' + str(beeIdx) + ".txt", 'wout.best.' + filenametime)
                        try:
                            shutil.copyfile(str(beeIdx) + '/OUTPUT/results.av', 'results.best.' + filenametime)
                        except:
                            pass

            #Check if there are abandoned solutions
            for bee in range(self.__nEmployed):
                if (self.__bees[bee].getIter() > self.__iterAbandoned):
                    u.logger.info("Bee " + str(bee) + ". Abandoning food source")
                    newSolution = self.__scout.createNewCandidate(self.__probMatrix)[0]
                    self.__bees[bee].setIter(0)
                    self.__bees[bee].setSolution(newSolution)
                    self.__problem.solve(newSolution)
                    solutionValue = float(newSolution.getValue())
                    
                    if (solutionValue<=0.0 or solutionValue >= u.infinity/100.0):
                        continue

                    if ((u.objective == u.objectiveType.MAXIMIZE and
                        float(solutionValue) > float(self.__bestSolution.getValue())) or
                        (u.objective == u.objectiveType.MINIMIZE and
                        float(solutionValue) < float(self.__bestSolution.getValue()))):

                        filenametime = "0"
                        try:
                            filenametime = time.strftime("%Y%m%d-%H%M%S", time.localtime())
                        except Exception, e:
                            u.logger.warning("MASTER. " + str(e) + " line: " + str(sys.exc_traceback.tb_lineno))

                        u.logger.log(u.extraLog, "New best solution found. Value " + str(newSolution) +
                                       " -- old " + str(self.__bestSolution.getValue()) + ". Bee " + str(beeIdx))

                        self.__bestSolution = newSolution

                        if ((u.objective == u.objectiveType.MAXIMIZE and float(solutionValue) > float(self.__bestGlobalSolution.getValue())) or
                            (u.objective == u.objectiveType.MINIMIZE and float(solutionValue) < float(self.__bestGlobalSolution.getValue()))):
                            self.__bestGlobalSolution = self.__bestSolution
                    
                        buff = self.__bestSolution.getParametersValues()
                        solValue[0] = solutionValue

                        """
                        for destination in range(u.size):
                            if (destination == u.rank):
                                continue
                            u.comm.Isend([buff, MPI.FLOAT], destination, u.tags.COMMSOLUTION)
                            u.comm.Isend([buff, MPI.FLOAT], destination, u.tags.COMMSOLUTION)
                        """

                        if (self.__problemType == u.solutionType.FUSION):
                            self.__bestSolution.prepare("input.best." + filenametime)
                            shutil.copyfile(str(beeIdx) + '/threed1.tj' + str(beeIdx), 'threed1.best.' + filenametime)
                            shutil.copyfile(str(beeIdx) + '/wout_tj' + str(beeIdx) + ".txt", 'wout.best.' + filenametime)
                            try:
                                shutil.copyfile(str(beeIdx) +
                                                '/OUTPUT/results.av',
                                                'results.best.' + filenametime)
                            except:
                                pass
                    u.logger.debug("Scout bee putting solution on pending queue")
        return

    def check_finish(self):
        try:
            #first check if it's too early to finish
            elapsedTime = time.time() - u.starttime
            if (elapsedTime + (60 * 5) < self.__runtime):
                return False
            allNull = True
            for i in range(len(self.__requestsEnd)):
                if (self.__requestsEnd[i] != MPI.REQUEST_NULL):
                    allNull = False
                    break
            if (allNull):
                u.logger.info("MASTER. All slaves have finished")
                return True
            status = MPI.Status()
            idx, flag = MPI.Request.Testany(self.__requestsEnd, status)
            if (flag and idx >= 0):
                source = status.source
                self.__requestsEnd[source] = MPI.REQUEST_NULL
                u.logger.info('MASTER. Received a termination request from slave' +
                               str(source))
            return False
        except Exception, e:
            u.logger.error('MASTER. Error checking finish.' + str(e))
            return True

    def finish(self):
        self.__pendingSolutions.writeAllSolutions()
        u.logger.info('DAB Master finish')
