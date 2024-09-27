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
    Version 0.1 (23-08-2013):   Creation of the file.
    Version 1.0 (15-01-2014):   Fist stable version.
"""

"""
Objects of this class will represent a slave.
Slaves wait for an input message, build a problem instance, and solve the
problem.
Once the problem has been solved, the slave sends the result back to the
master and waits for a new input message.
"""

import Utils as u
from SolutionFusion import SolutionFusion
from SolutionNonSeparable import SolutionNonSeparable
from ProblemFusion import ProblemFusion
from ProblemNonSeparable import ProblemNonSeparable
from mpi4py import MPI
from array import array
from time import time
import configparser
import sys


class Slave (object):
    def __init__(self, comm, ProblemType):
        try:
            self.__comm = comm
            self.__rank = self.__comm.Get_rank()
            self.__endRequest = None
            self.__problemType = ProblemType
            self.__end = array('i', [0]) * 1
            self.__runtime = 0
            self.__requestsEnd = []
            if (self.__problemType == u.problemType.FUSION):
                self.__problem = ProblemFusion()
            elif (self.__problemType == u.problemType.NONSEPARABLE):
                self.__problem = ProblemNonSeparable()
            return
        except Exception, e:
            print("Slave " + str(sys.exc_traceback.tb_lineno) + " " + str(e))

    """
    This is the slave. It sends a request for data, then receives
    a solution and the bee index.
    Solves the solution and sends the solution back to the master
    """

    def run(self, infile, cfile):
        try:
            startTime = time()
            config = configparser.ConfigParser()
            config.read(cfile)
            if (config.has_option("Algorithm", "time")):
                val = config.get("Algorithm", "time")
                if (val != None):
                    self.__runtime = int(val)
            if (config.has_option("Algorithm", "objective")):
                val = config.get("Algorithm", "objective")
                if (val != None):
                    if (val == "max"):
                        u.objective = u.objectiveType.MAXIMIZE
                    else:
                        u.objective = u.objectiveType.MINIMIZE
            elapsedTime = time() - startTime
            solutionsEvaluated = 0
            """
            Send the finish message 10 minutes before the end time to allow
            the jobs that are still running to finish on time
            """
            while((elapsedTime + (60 * 5)) < self.__runtime):
                #solution = SolutionFusion()
                #Send a request for data
                status = MPI.Status()
                if (self.__problemType == u.problemType.FUSION):
                    solution = SolutionFusion(infile)
                elif (self.__problemType == u.problemType.NONSEPARABLE):
                    solution = SolutionNonSeparable(infile)
                numParams = solution.getNumberofParams()
                buff = array('f', [0]) * numParams
                solValue = array('f', [0]) * 1
                dump = array('i', [0]) * 1
                u.logger.debug("SLAVE (" + str(self.__rank) +
                               ") waiting for a solution")
                #self.__comm.Isend(dump, dest=0, tag=u.tags.REQINPUT)
                self.__comm.Send(dump, dest=0, tag=u.tags.REQINPUT)

                agentIdx = array('i', [0]) * 1
                #Receive the solution
                req = self.__comm.Irecv(buff, 0, u.tags.RECVFROMMASTER)
                req.wait(status)

                #Receive the bee id
                req = self.__comm.Irecv(agentIdx, 0, u.tags.RECVFROMMASTER)
                req.wait(status)

                u.logger.info("SLAVE (" + str(self.__rank) +
                               ") has received a solution from bee " +
                               str(agentIdx[0]))
                solution.setParametersValues(buff)

                #Evalute the solution
                self.__problem.solve(solution)

                buff = solution.getParametersValues()
                solValue[0] = float(solution.getValue())

                #Send the solution back together with the bee id
                req = self.__comm.Isend([dump, MPI.INT], 0,
                                        u.tags.REQSENDINPUT)
                req.Wait(status)

                u.logger.debug("SLAVE (" + str(self.__rank) +
                               "). Buffer size: " + str(len(buff)))

                self.__comm.Send(buff, 0, u.tags.COMMSOLUTION)
                self.__comm.Send(solValue, 0, u.tags.COMMSOLUTION)
                self.__comm.Send(agentIdx, 0, u.tags.COMMSOLUTION)

                elapsedTime = time() - startTime
                solutionsEvaluated += 1
                u.logger.debug("SLAVE (" + str(self.__rank) + ") elapsed " +
                                str(elapsedTime) + " - Runtime " +
                                str(self.__runtime))
            u.logger.info("SLAVE (" + str(self.__rank) +
                          ") configurations evaluated: " +
                           str(solutionsEvaluated))
        except Exception, e:
            u.logger.error("SLAVE (" + str(self.__rank) + ")" +
                           str(sys.exc_traceback.tb_lineno) + " " + str(e))

    """
    This method just checks if there is message from the master indicating the
    end of the simulation
    """

    def finish(self):
        end = array('i', [0]) * 1
        u.comm.Send([end, MPI.INT], 0, u.tags.ENDSIM)
        u.logger.info("SLAVE (" + str(self.__rank) +
                      "). Sent end request to master")
