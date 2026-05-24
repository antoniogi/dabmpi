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

from collections import deque
from enum import IntEnum
from pathlib import Path
from typing import Optional

import numpy as np


__author__ = "Antonio Gomez"
__version__ = "2.0"


# ============================================================================
# Global variables - initialized by disop.py
# ============================================================================

# Rank of each process
rank: int = -1

# Number of processes
size: int = -1

# MPI communicator
comm = None

# Config file
cfile: str = ""

# Start time
starttime: int = 0

# Logger initialized externally
logger = None


# ============================================================================
# Configuration constants
# ============================================================================

# Extra value for logging when a new solution has been found
EXTRA_LOG: int = 100

# Numerical infinity approximation
INFINITY: float = 9.999999e37

# File size threshold for tail implementation selection
SMALL_FILE_THRESHOLD: int = 100 * 1024 * 1024  # 100 MB

# Runtime configuration
iterations: int = 10


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


# Default runtime configuration
objective: ObjectiveType = ObjectiveType.MINIMIZE
comm_model: CommModelType = CommModelType.DRIVERWORKER


# ============================================================================
# File utilities
# ============================================================================

def tail_small(filepath: str) -> str:
    """
    Read the last line from a small file.

    Uses deque for simplicity and correctness.

    Args:
        filepath: Path to the file.

    Returns:
        Last line without trailing newline.
    """
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        lines = deque(f, maxlen=1)

    return lines[0].rstrip("\n") if lines else ""


def tail_large(filepath: str, read_size: int = 4096) -> str:
    """
    Efficiently read the last line from a large file.

    Reads backwards from the end of the file in binary mode.

    Args:
        filepath: Path to the file.
        read_size: Chunk size for backward reads.

    Returns:
        Last line without trailing newline.
    """
    with open(filepath, "rb") as f:
        f.seek(0, 2)
        file_size = f.tell()

        if file_size == 0:
            return ""

        buffer = bytearray()
        pos = file_size

        while pos > 0:
            read_len = min(read_size, pos)
            pos -= read_len

            f.seek(pos)
            chunk = f.read(read_len)

            buffer[:0] = chunk

            # Found newline before final chunk
            if b"\n" in chunk and pos != file_size - read_len:
                break

        lines = buffer.rstrip(b"\n").splitlines()

        if not lines:
            return ""

        return lines[-1].decode("utf-8", errors="replace")


def tail(filepath: str) -> str:
    """
    Read the last line from a file.

    Automatically selects an optimized implementation based
    on file size.

    Args:
        filepath: Path to the file.

    Returns:
        Last line without trailing newline.

    Raises:
        FileNotFoundError: If the file does not exist.
        OSError: If the file cannot be read.
    """
    file_size = Path(filepath).stat().st_size

    if file_size < SMALL_FILE_THRESHOLD:
        return tail_small(filepath)

    return tail_large(filepath)


# ============================================================================
# Matrix class
# ============================================================================

class Matrix:
    """
    Matrix abstraction backed by NumPy.

    Internally stores data in NumPy row-major format:
        matrix[row, col]

    Externally exposes legacy-compatible 1-based indexing:
        matrix[col, row]

    Example:
        m[1, 1] = 5.0
        value = m[1, 1]
    """

    def __init__(
        self,
        cols: int,
        rows: int,
        init: float = 0.0,
        dtype=np.float64,
    ) -> None:
        """
        Initialize matrix.

        Args:
            cols: Number of columns.
            rows: Number of rows.
            init: Initial value.
            dtype: NumPy dtype.
        """
        if cols <= 0 or rows <= 0:
            raise ValueError(
                f"Rows and columns must be positive: "
                f"cols={cols}, rows={rows}"
            )

        self.cols = cols
        self.rows = rows

        self._matrix = np.full(
            (rows, cols),
            init,
            dtype=dtype,
        )

    # ---------------------------------------------------------------------
    # Internal helpers
    # ---------------------------------------------------------------------

    def _validate_indices(self, col: int, row: int) -> None:
        if not (1 <= col <= self.cols):
            raise IndexError(f"Column out of range: {col}")

        if not (1 <= row <= self.rows):
            raise IndexError(f"Row out of range: {row}")

    # ---------------------------------------------------------------------
    # Element access
    # ---------------------------------------------------------------------

    def __getitem__(self, key: tuple[int, int]) -> float:
        """
        Access matrix element using 1-based indexing.

        Example:
            value = m[col, row]
        """
        col, row = key

        self._validate_indices(col, row)

        return float(self._matrix[row - 1, col - 1])

    def __setitem__(
        self,
        key: tuple[int, int],
        value: float,
    ) -> None:
        """
        Set matrix element using 1-based indexing.

        Example:
            m[col, row] = value
        """
        col, row = key

        self._validate_indices(col, row)

        self._matrix[row - 1, col - 1] = value

    # ---------------------------------------------------------------------
    # Legacy compatibility methods
    # ---------------------------------------------------------------------

    def setitem(self, col: int, row: int, value: float) -> None:
        self[col, row] = value

    def getitem(self, col: int, row: int) -> float:
        return self[col, row]

    def get_num_rows(self) -> int:
        return self.rows

    def get_num_cols(self) -> int:
        return self.cols

    # ---------------------------------------------------------------------
    # Properties
    # ---------------------------------------------------------------------

    @property
    def shape(self) -> tuple[int, int]:
        return self._matrix.shape

    @property
    def array(self) -> np.ndarray:
        """
        Direct access to underlying NumPy array.
        """
        return self._matrix

    # ---------------------------------------------------------------------
    # String representation
    # ---------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"Matrix(cols={self.cols}, "
            f"rows={self.rows}, "
            f"dtype={self._matrix.dtype})"
        )

    def __str__(self) -> str:
        return str(self._matrix)