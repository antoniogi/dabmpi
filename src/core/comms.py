#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :

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
