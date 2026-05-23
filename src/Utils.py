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

__version__ = ' REVISION:   2.0  -  23-05-2026'

"""
HISTORY
    Version 0.1 (12-04-2013):   Creation of the file.
    Version 1.0 (15-01-2014):   First stable version.
    Version 1.1 (09-01-2015):   Use Numpy for the Matrix.
    Version 2.0 (23-05-2026):   Refactoring and modernization
"""

"""Distributed optimization utility module.

Provides global configuration, MPI communication tags, logging, and utility
classes for the DAB MPI solver. Global variables (rank, comm, logger, etc.)
are initialized by disop.py during startup.
"""
import numpy as np

# ============================================================================
# Global variables - initialized by disop.py
# ============================================================================

#rank of each process
rank: int = -1
#number of processes
size: int = -1
#communicator
comm = None
#config file
cfile: str = ""
#start time
starttime: int = 0

# ============================================================================
# Configuration and constants
# ============================================================================

#extra value for logging when a new solution has been found
extraLog: int = 100

# ============================================================================
# Type definitions (enumerations)
# ============================================================================


def enum(**enums):
    """Create a simple enumeration type.
    
    Args:
        **enums: Keyword arguments defining enum members (name=value)
        
    Returns:
        A type with the enum members as class attributes
    """
    return type('Enum', (), enums)

# Problem types
problem_type = enum(NONE=0, FUSION=1, NONSEPARABLE=2, CRISTINA=3)

# Solution types
solution_type = enum(FUSION=1, NONSEPARABLE=2, CRISTINA=3)

# Solver types
solver_type = enum(NONE=0, DAB=1, SA=2)

# Communication model types
commModelType = enum(DRIVERWORKER=0, ALL2ALL=1)

# MPI message tags
tags = enum(
    RECVFROMDRIVER=1,
    RECVFROMWORKER=2,
    COMMSOLUTION=3,
    REQSENDINPUT=4,
    REQINPUT=5,
    ENDSIM=6
)

# Optimization objective types
objectiveType = enum(MINIMIZE=1, MAXIMIZE=2)

# ============================================================================
# Runtime configuration
# ============================================================================

objective = objectiveType.MINIMIZE
commModel = commModelType.DRIVERWORKER
logger = None  # Initialized by disop.py
iterations: int = 10
infinity: float = 9.999999e+37

def Tail(filepath: str, read_size: int = 1024) -> str:
    """Read the last line from a file.
    
    Reads the file from the end and works backwards to find the last
    complete line, useful for tailing log files.
    
    Args:
        filepath: Complete path to the file to read
        read_size: Number of bytes to read per iteration (default 1024).
                   Increase for faster reading of large files.
        
    Returns:
        The last line of the file as a string (without trailing newline)
        
    Raises:
        FileNotFoundError: If the file does not exist
        IOError: If the file cannot be read
    """
    with open(filepath, 'r') as f:
        offset = read_size
        f.seek(0, 2)
        file_size = f.tell()
        while 1:
            if file_size < offset:
                offset = file_size
            f.seek(-1 * offset, 2)
            read_str = f.read(offset)
            # Remove newline at the end
            if read_str[offset - 1] == '\n':
                read_str = read_str[0:-1]
            lines = read_str.split('\n')
            if len(lines) > 1:  # Got a line
                return lines[len(lines) - 1]
            if offset == file_size:   # Reached the beginning
                return read_str
            offset += read_size
    return ""  # Should never reach here""


class Matrix:
    """Matrix class using nested lists for 2D array operations.
    
    Provides a simple matrix implementation backed by nested Python lists.
    Uses 1-based indexing for compatibility with legacy code.
    Requires the global logger to be initialized.
    """

    def __init__(self, cols: int, rows: int, init: float = 0.0):
        """Initialize a matrix with given dimensions.
        
        Args:
            cols: Number of columns
            rows: Number of rows
            init: Initial value for all elements (default 0.0)
            
        Raises:
            RuntimeError: If global logger is not initialized
        """
        if logger is None:
            raise RuntimeError("Global logger must be initialized before creating Matrix")
        self.cols = cols
        self.rows = rows
        logger.debug("Init matrix [" + str(cols) + "][" + str(rows) + "]")
        self.matrix = []
        # initialize matrix and fill with zeroes
        for i in range(rows):
            logger.debug("Row " + str(i))
            ea_row = []
            for j in range(cols):
                ea_row.append(init)
            self.matrix.append(ea_row)
        logger.debug("Matrix initialised")

    def getNumRows(self) -> int:
        """Return the number of rows in the matrix."""
        return self.rows

    def getNumCols(self) -> int:
        """Return the number of columns in the matrix."""
        return self.cols

    def setitem(self, col: int, row: int, v: float) -> None:
        """Set a matrix element at (col, row) to value v.
        
        Args:
            col: Column index (1-based)
            row: Row index (1-based)
            v: Value to set
        """
        self.matrix[col - 1][row - 1] = v

    def getitem(self, col: int, row: int) -> float:
        """Get a matrix element at (col, row).
        
        Args:
            col: Column index (1-based)
            row: Row index (1-based)
            
        Returns:
            The value at position (col, row)
        """
        return self.matrix[col - 1][row - 1]

    def __repr__(self) -> str:
        """Return a string representation of the matrix.
        
        Returns:
            Formatted string showing each row
        """
        out_str = ""
        for i in range(self.rows):
            out_str += 'Row %s = %s\n' % (i + 1, self.matrix[i])
        return out_str
