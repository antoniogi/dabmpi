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
from core.runtime import GlobalRuntime
from core.enums import ProblemType
import configparser
import sys
from mpi4py import MPI
from solution.SolutionCristina import SolutionCristina
from solution.SolutionFusion import SolutionFusion
from solution.SolutionNonSeparable import SolutionNonSeparable
from problems.ProblemCristina import ProblemCristina
from problems.ProblemFusion import ProblemFusion
from problems.ProblemNonSeparable import ProblemNonSeparable

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
class Worker (object):
    def __init__(self, comm, problem_type, runtime: GlobalRuntime):
        try:
            self._comm = comm
            self._rank = self._comm.Get_rank()
            self._endRequest = None
            self._problem_type = problem_type
            self._runtime = runtime
            self._end = array('i', [0]) * 1
            self._runtime = 0
            self._requestsEnd = []
            if self._problem_type == ProblemType.FUSION:
                self._problem = ProblemFusion(runtime)
            elif self._problem_type == u.problem_type.NONSEPARABLE:
                self._problem = ProblemNonSeparable(runtime)
            elif self._problem_type == u.problem_type.CRISTINA:
                self._problem = ProblemCristina(runtime)
        except Exception as e:
            print("Worker " + str(sys.exc_info()[2].tb_lineno) + " " + str(e))

    #This is the worker. It sends a request for data, then receives
    #a solution and the bee index.
    #Solves the solution and sends the solution back to the driver
    def run(self, infile, cfile):
        try:
            start_time = self._runtime.start_time
            elapsed_time = 0
            solutions_evaluated = 0
            """
            start_time = time()
            config = configparser.ConfigParser()
            config.read(cfile)
            if config.has_option("Algorithm", "time"):
                val = config.get("Algorithm", "time")
                if val is not None:
                    self._runtime = int(val)
            if config.has_option("Algorithm", "objective"):
                val = config.get("Algorithm", "objective")
                if val is not None:
                    if str(val).lower == "max":
                        self._runtime.objective =  u.objectiveType.MAXIMIZE
                        u.logger.debug("WORKER (" + str(self._rank) +
                                        ") Objective set to MAXIMIZE")
                    else:
                        u.objective = u.objectiveType.MINIMIZE
                        u.logger.debug("WORKER (" + str(self._rank) +
                                        ") Objective set to MINIMIZE")
            elapsed_time = time() - start_time
            """
            #Send the finish message 10 minutes before the end time to allow
            #the jobs that are still running to finish on time
            while (elapsed_time + (60 * 5)) < float(self._runtime.max_execution_time):
                #solution = SolutionFusion()
                #Send a request for data
                status = MPI.Status()
                if self._problem_type == ProblemType.FUSION:
                    solution = SolutionFusion(infile)
                elif self._problem_type == ProblemType.NONSEPARABLE:
                    solution = SolutionNonSeparable(infile)
                elif self._problem_type == ProblemType.CRISTINA:
                    solution = SolutionCristina(infile)
                else:
                    u.logger.error("WORKER (" + str(self._rank) +
                                   ") Problem type not supported")
                    return
                num_params = solution.getNumberofParams()
                buff = array('f', [0]) * num_params
                solution_value = array('f', [0]) * 1
                dump = array('i', [0]) * 1
                u.logger.debug("WORKER (" + str(self._rank) +
                               ") waiting for a solution")
                #self._comm.Isend(dump, dest=0, tag=u.tags.REQINPUT)
                self._comm.Send(dump, dest=0, tag=u.tags.REQINPUT)

                agent_idx = array('i', [0]) * 1
                #Receive the solution
                req = self._comm.Irecv(buff, 0, u.tags.RECVFROMDRIVER)
                req.wait(status)

                #Receive the bee id
                req = self._comm.Irecv(agent_idx, 0, u.tags.RECVFROMDRIVER)
                req.wait(status)

                u.logger.info("WORKER (" + str(self._rank) +
                               ") has received a solution to evaluate from bee " +
                               str(agent_idx[0]))
                solution.setParametersValues(buff)

                #Evalute the solution
                self._problem.solve(solution)

                buff = solution.getParametersValues()
                solution_value[0] = float(solution.getValue())

                #Send the solution back together with the bee id
                req = self._comm.Isend([dump, MPI.INT], 0,
                                        u.tags.REQSENDINPUT)
                req.Wait(status)

                u.logger.debug("WORKER (" + str(self._rank) +
                               "). Buffer size: " + str(len(buff)))
                u.logger.debug("WORKER (" + str(self._rank) +
                               "- " + str(agent_idx) + ") found solution with value " 
                               + str(solution_value[0]))

                self._comm.Send(buff, 0, u.tags.COMMSOLUTION)
                self._comm.Send(solution_value, 0, u.tags.COMMSOLUTION)
                self._comm.Send(agent_idx, 0, u.tags.COMMSOLUTION)

                elapsed_time = time() - start_time
                solutions_evaluated += 1
                u.logger.debug("WORKER (" + str(self._rank) + ") elapsed " +
                                str(elapsed_time) + " - Runtime " +
                                str(self._runtime))
            u.logger.info("WORKER (" + str(self._rank) +
                          ") configurations evaluated: " +
                           str(solutions_evaluated))
        except Exception as e:
            u.logger.error("WORKER (" + str(self._rank) + ")" +
                           str(sys.exc_info()[2].tb_lineno) + " " + str(e))

    #This method just checks if there is message from the driver indicating the
    #end of the simulation

    def finish(self):
        end = array('i', [0]) * 1
        u.comm.Send([end, MPI.INT], 0, u.tags.ENDSIM)
        u.logger.info("WORKER (" + str(self._rank) +
                      "). Sent end request to driver")
