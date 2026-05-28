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

"""Global runtime configuration and state management.

Manages optimization settings, logging, and application configuration.
Provides a singleton instance for application-wide access to runtime state.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from logging import Logger
from typing import Optional

import core.enums as e
from core.logging import get_logger


__author__ = "Antonio Gomez"
__version__ = "2.0"


@dataclass
class GlobalRuntime:
    # File and timing
    config_file: str = field(default="")
    input_file: str = field(default="")
    start_time: float = field(default=0)
    max_execution_time: float = field(default=0)
    # Optimization settings
    iterations: int = field(default=10)
    objective: e.ObjectiveType = field(default=e.ObjectiveType.MINIMIZE)
    comm_model: e.CommModelType = field(default=e.CommModelType.DRIVERWORKER)
    problem_type: e.ProblemType = field(default=e.ProblemType.FUSION)
    solution_type: e.SolutionType = field(default=e.SolutionType.FUSION)
    solver_type: e.SolverType = field(default=e.SolverType.DAB)
    # Logger instance
    logger: Optional[Logger] = field(default_factory=lambda: get_logger())
    max_valid_solution_value: float = field(default=1e6)

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        self.validate()

    def validate(self) -> None:
        """Validate all configuration values.
        
        Raises:
            ValueError: If any configuration is invalid
        """
        if self.iterations <= 0:
            raise ValueError(f"iterations must be positive, got {self.iterations}")
        
        if self.start_time < 0:
            raise ValueError(f"start_time must be >= 0, got {self.start_time}")
        
        if self.max_execution_time < 0:
            raise ValueError(f"max_execution_time must be >= 0, got {self.max_execution_time}")
        
        if self.max_valid_solution_value <= 0:
            raise ValueError(f"max_valid_solution_value must be > 0, got {self.max_valid_solution_value}")

    def log_configuration(self) -> None:
        """Log current configuration for debugging."""
        if self.logger:
            self.logger.info(f"  Iterations: {self.iterations}")
            self.logger.info(f"  Config File: {self.config_file}")

    def reset(self) -> None:
        """Reset to default values (primarily for testing)."""
        self.config_file = ""
        self.start_time = 0
        self.iterations = 10
        self.objective = e.ObjectiveType.MINIMIZE
        self.comm_model = e.CommModelType.DRIVERWORKER

# Global singleton instance (thread-safe)
_runtime: Optional[GlobalRuntime] = None
_runtime_lock = threading.Lock()

def get_runtime() -> GlobalRuntime:
    """Get the global runtime instance (thread-safe singleton).
    
    Creates a new instance on first call. Subsequent calls return the
    same instance.
    
    Returns:
        The global GlobalRuntime instance.
    """
    global _runtime
    if _runtime is None:
        with _runtime_lock:
            if _runtime is None:  # Double-check locking pattern
                _runtime = GlobalRuntime()
    return _runtime


def set_runtime(runtime: GlobalRuntime) -> None:
    """Set the global runtime instance.
    
    Args:
        runtime: New GlobalRuntime instance to use globally.
    """
    global _runtime
    with _runtime_lock:
        _runtime = runtime

def reset_runtime() -> None:
    """Reset runtime to defaults (primarily for testing)."""
    global _runtime
    with _runtime_lock:
        _runtime = None

