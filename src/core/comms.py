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

from dataclasses import dataclass, field
from typing import Any


__author__ = "Antonio Gomez"
__version__ = "2.0"


# ============================================================================
# Global variables - initialized by disop.py
# ============================================================================

@dataclass(frozen=True)
class GlobalComms:
    # Rank of each process
    rank: int = field(default=-1)
    # Number of processes
    size: int = field(default=-1)
    # MPI communicator
    comm: Any = field(default=None)
