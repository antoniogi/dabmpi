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


from array import array
from time import time
import configparser
import sys
from mpi4py import MPI
import Utils as u
from SolutionCristina import SolutionCristina
from SolutionFusion import SolutionFusion
from SolutionNonSeparable import SolutionNonSeparable
from ProblemCristina import ProblemCristina
from ProblemFusion import ProblemFusion
from ProblemNonSeparable import ProblemNonSeparable

__author__ = ' AUTHORS:     Antonio Gomez (antonio.gomez@csiro.au)'


__version__ = ' REVISION:   1.0  -  15-01-2014'

"""
HISTORY
    Version 0.1 (23-08-2013):   Creation of the file.
    Version 1.0 (15-01-2014):   Fist stable version.

Objects of this class will represent a worker.
Workers wait for an input message, build a problem instance, and solve the
problem.
Once the problem has been solved, the worker sends the result back to the
driver and waits for a new input message.
"""
class Worker ():
    def __init__(self, comm, problem_type):
        try:
            self.__comm = comm
            self.__rank = self.__comm.Get_rank()
            self.__endRequest = None
            self.__problem_type = problem_type
            self.__end = array('i', [0]) * 1
            self.__runtime = 0
            self.__requestsEnd = []
            if self.__problem_type == u.problem_type.FUSION:
                self.__problem = ProblemFusion()
            elif self.__problem_type == u.problem_type.NONSEPARABLE:
                self.__problem = ProblemNonSeparable()
            elif self.__problem_type == u.problem_type.CRISTINA:
                self.__problem = ProblemCristina()
        except Exception as e:
            print("Worker " + str(sys.exc_info()[2].tb_lineno) + " " + str(e))

    #This is the worker. It sends a request for data, then receives
    #a solution and the bee index.
    #Solves the solution and sends the solution back to the driver
    def run(self, infile, cfile):
        try:
            start_time = time()
            config = configparser.ConfigParser()
            config.read(cfile)
            if config.has_option("Algorithm", "time"):
                val = config.get("Algorithm", "time")
                if val is not None:
                    self.__runtime = int(val)
            if config.has_option("Algorithm", "objective"):
                val = config.get("Algorithm", "objective")
                if val is not None:
                    if val == "max":
                        u.objective = u.objectiveType.MAXIMIZE
                    else:
                        u.objective = u.objectiveType.MINIMIZE
            elapsed_time = time() - start_time
            solutions_evaluated = 0
            #Send the finish message 10 minutes before the end time to allow
            #the jobs that are still running to finish on time
            while (elapsed_time + (60 * 5)) < self.__runtime:
                #solution = SolutionFusion()
                #Send a request for data
                status = MPI.Status()
                if self.__problem_type == u.problem_type.FUSION:
                    solution = SolutionFusion(infile)
                elif self.__problem_type == u.problem_type.NONSEPARABLE:
                    solution = SolutionNonSeparable(infile)
                elif self.__problem_type == u.problem_type.CRISTINA:
                    solution = SolutionCristina(infile)
                else:
                    u.logger.error("WORKER (" + str(self.__rank) +
                                   ") Problem type not supported")
                    return
                num_params = solution.getNumberofParams()
                buff = array('f', [0]) * num_params
                solution_value = array('f', [0]) * 1
                dump = array('i', [0]) * 1
                u.logger.debug("WORKER (" + str(self.__rank) +
                               ") waiting for a solution")
                #self.__comm.Isend(dump, dest=0, tag=u.tags.REQINPUT)
                self.__comm.Send(dump, dest=0, tag=u.tags.REQINPUT)

                agent_idx = array('i', [0]) * 1
                #Receive the solution
                req = self.__comm.Irecv(buff, 0, u.tags.RECVFROMDRIVER)
                req.wait(status)

                #Receive the bee id
                req = self.__comm.Irecv(agent_idx, 0, u.tags.RECVFROMDRIVER)
                req.wait(status)

                u.logger.info("WORKER (" + str(self.__rank) +
                               ") has received a solution from bee " +
                               str(agent_idx[0]))
                solution.setParametersValues(buff)

                #Evalute the solution
                self.__problem.solve(solution)

                buff = solution.getParametersValues()
                solution_value[0] = float(solution.getValue())

                #Send the solution back together with the bee id
                req = self.__comm.Isend([dump, MPI.INT], 0,
                                        u.tags.REQSENDINPUT)
                req.Wait(status)

                u.logger.debug("WORKER (" + str(self.__rank) +
                               "). Buffer size: " + str(len(buff)))

                self.__comm.Send(buff, 0, u.tags.COMMSOLUTION)
                self.__comm.Send(solution_value, 0, u.tags.COMMSOLUTION)
                self.__comm.Send(agent_idx, 0, u.tags.COMMSOLUTION)

                elapsed_time = time() - start_time
                solutions_evaluated += 1
                u.logger.debug("WORKER (" + str(self.__rank) + ") elapsed " +
                                str(elapsed_time) + " - Runtime " +
                                str(self.__runtime))
            u.logger.info("WORKER (" + str(self.__rank) +
                          ") configurations evaluated: " +
                           str(solutions_evaluated))
        except Exception as e:
            u.logger.error("WORKER (" + str(self.__rank) + ")" +
                           str(sys.exc_info()[2].tb_lineno) + " " + str(e))

    #This method just checks if there is message from the driver indicating the
    #end of the simulation

    def finish(self):
        end = array('i', [0]) * 1
        u.comm.Send([end, MPI.INT], 0, u.tags.ENDSIM)
        u.logger.info("WORKER (" + str(self.__rank) +
                      "). Sent end request to driver")
