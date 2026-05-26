#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :

#############################################################################
#    Copyright 2013 by Antonio Gomez and Miguel Cardenas                    #
#                                                                           #
#    Licensed under the Apache License, Version 2.0 (the "License");        #
#    you may not use this file except in compliance with the License.       #
#    You may obtain a copy of the License at                                #
#                                                                           #
#        http://www.apache.org/licenses/LICENSE-2.0                         #
#                                                                           #
#    Unless required by applicable law or agreed to in writing, software    #
#    distributed under the License is distributed on an "AS IS" BASIS,      #
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied#
#    See the License for the specific language governing permissions and    #
#    limitations under the License.                                         #
#############################################################################

"""
Distributed optimization utility module.

Provides:

- Global MPI runtime configuration
- Communication tags and enumerations
- File utility helpers
- Matrix abstraction backed by NumPy

Global variables (rank, size, comm, logger, etc.) are initialized
by disop.py during startup.
"""

from __future__ import annotations

from enum import IntEnum


__author__ = "Antonio Gomez"
__version__ = "2.0"


# ============================================================================
# Enumerations
# ============================================================================

class ProblemType(IntEnum):
    NONE = 0
    FUSION = 1
    NONSEPARABLE = 2
    CRISTINA = 3


class SolutionType(IntEnum):
    FUSION = 1
    NONSEPARABLE = 2
    CRISTINA = 3


class SolverType(IntEnum):
    NONE = 0
    DAB = 1
    SA = 2


class CommModelType(IntEnum):
    DRIVERWORKER = 0
    ALL2ALL = 1


class Tags(IntEnum):
    RECVFROMDRIVER = 1
    RECVFROMWORKER = 2
    COMMSOLUTION = 3
    REQSENDINPUT = 4
    REQINPUT = 5
    ENDSIM = 6


class ObjectiveType(IntEnum):
    MINIMIZE = 1
    MAXIMIZE = 2
