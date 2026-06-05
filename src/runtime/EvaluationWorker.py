#!/usr/bin/env python

from array import array
from copy import deepcopy
from time import time

from mpi4py import MPI

from core.comms import GlobalComms
from core.enums import ProblemType, Tags
from core.runtime import GlobalRuntime
from problems.ProblemCristina import ProblemCristina
from problems.ProblemFusion import ProblemFusion
from problems.ProblemNonSeparable import ProblemNonSeparable
from solution.SolutionCristina import SolutionCristina
from solution.SolutionFusion import SolutionFusion
from solution.SolutionNonSeparable import SolutionNonSeparable


class EvaluationWorker:
    _problem: ProblemFusion | ProblemNonSeparable | ProblemCristina

    def __init__(self, runtime: GlobalRuntime, comm: GlobalComms):
        try:
            self._comm: GlobalComms = comm
            self._runtime: GlobalRuntime = runtime
            self._rank: int = self._comm.comm.Get_rank()
            self._endRequest: MPI.Request | None = None

            self._end = array("i", [0])
            self._requestsEnd: list[MPI.Request] = []
            if self._runtime.problem_type == ProblemType.FUSION:
                self._problem = ProblemFusion(runtime, comm)
            elif self._runtime.problem_type == ProblemType.NONSEPARABLE:
                self._problem = ProblemNonSeparable(runtime, comm)
            elif self._runtime.problem_type == ProblemType.CRISTINA:
                self._problem = ProblemCristina(runtime, comm)
            else:
                raise ValueError(f"Unknown problem type: {self._runtime.problem_type}")
        except Exception:
            self._runtime.logger.exception("Worker initialization failed")
            raise

    # This is the worker. It sends a request for data, then receives
    # a solution and the bee index.
    # Solves the solution and sends the solution back to the driver
    def run(self):
        try:
            start_time = self._runtime.start_time
            elapsed_time = 0
            solutions_evaluated = 0

            # Send the finish message 10 minutes before the end time to allow
            # the jobs that are still running to finish on time
            while True:
                elapsed_time = time() - start_time

                if elapsed_time + 300 >= float(self._runtime.max_execution_time):
                    break
                self._runtime.logger.debug(
                    "WORKER ("
                    + str(self._rank)
                    + ") elapsed "
                    + str(elapsed_time)
                    + " - Runtime "
                    + str(self._runtime)
                )
                # Send a request for data
                status = MPI.Status()
                if self._runtime.problem_type == ProblemType.FUSION:
                    template = SolutionFusion.get_template_data(
                        self._runtime, self._comm
                    )
                    solution = SolutionFusion(
                        self._runtime, self._comm, data=deepcopy(template)
                    )
                    # solution = SolutionFusion(self._runtime, self._comm)
                elif self._runtime.problem_type == ProblemType.NONSEPARABLE:
                    solution = SolutionNonSeparable(self._runtime, self._comm, None)
                elif self._runtime.problem_type == ProblemType.CRISTINA:
                    solution = SolutionCristina(self._runtime, self._comm, None)
                else:
                    raise ValueError(
                        f"Unknown problem type: {self._runtime.problem_type}"
                    )

                num_params = solution.get_number_of_params()
                buff = array("f", [0]) * num_params
                solution_value = array("f", [0]) * 1
                dump = array("i", [0]) * 1
                self._runtime.logger.debug(
                    "WORKER (" + str(self._rank) + ") waiting for a solution"
                )
                # self._comm.Isend(dump, dest=0, tag=u.tags.REQINPUT)
                self._comm.comm.Send(dump, dest=0, tag=Tags.REQINPUT)

                agent_idx = array("i", [0]) * 1
                # Receive the solution
                req = self._comm.comm.Irecv(buff, 0, Tags.RECVFROMDRIVER)
                req.wait(status)

                # Receive the bee id
                req = self._comm.comm.Irecv(agent_idx, 0, Tags.RECVFROMDRIVER)
                req.wait(status)

                self._runtime.logger.info(
                    f"WORKER ( {self._rank} ) has received a solution to evaluate from bee {agent_idx[0]}"
                )
                solution.set_parameters_values(buff)

                # Evalute the solution
                self._problem.solve(solution)

                buff = solution.get_parameters_values()
                solution_value[0] = float(solution.value)

                # Send the solution back together with the bee id
                req = self._comm.comm.Isend([dump, MPI.INT], 0, Tags.REQSENDINPUT)
                req.Wait(status)

                self._runtime.logger.debug(
                    f"WORKER ( {self._rank} ) Buffer size: {len(buff)}"
                )
                self._runtime.logger.debug(
                    f"WORKER ( {self._rank} ) found solution with value {solution_value[0]}"
                )

                self._comm.comm.Send(buff, 0, Tags.COMMSOLUTION)
                self._comm.comm.Send(solution_value, 0, Tags.COMMSOLUTION)
                self._comm.comm.Send(agent_idx, 0, Tags.COMMSOLUTION)

                solutions_evaluated += 1
            self._runtime.logger.info(
                f"WORKER ( {self._rank} ) configurations evaluated: {solutions_evaluated}"
            )
        except Exception:
            self._runtime.logger.exception("Worker run failed")
            raise

    # This method just checks if there is message from the driver indicating the
    # end of the simulation

    def finish(self):
        end = array("i", [0]) * 1
        self._comm.comm.Send([end, MPI.INT], 0, Tags.ENDSIM)
        self._runtime.logger.info(f"WORKER ( {self._rank} ) Sent end request to driver")
