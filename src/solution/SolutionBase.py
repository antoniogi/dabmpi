#!/usr/bin/env python
# vim: set fileencoding=utf-8 :


import math
from abc import ABC, abstractmethod

from core.enums import ObjectiveType


class SolutionBase(ABC):
    """Abstract base class for optimization solutions.
    
    Defines the interface that all solution types must implement.
    Initializes the solution value based on the optimization objective:
    - MINIMIZE: starts at +infinity (any real value improves it)
    - MAXIMIZE: starts at -infinity (any real value improves it)
    """

    def __init__(self, runtime, comms):
        """Initialize solution with appropriate initial value.
        
        Args:
            infile: Input configuration file path
            
        Raises:
            ValueError: If objective type is not defined
        """
        # Set initial value based on optimization objective
        if runtime.objective == ObjectiveType.MINIMIZE:
            self._value = math.inf  # Start at +infinity for minimization
        else:
            self._value = -math.inf  # Start at -infinity for maximization

        self._isValid = True
        self._runtime = runtime
        self._comms = comms

    def getValue(self) -> float:
        """Return the current solution value."""
        return self._value

    def setValue(self, value: float) -> None:
        """Set the solution value.
        
        Args:
            value: New solution value
        """
        self._value = value

    @abstractmethod
    def getNumberofParams(self) -> int:
        """Return the number of parameters in this solution."""
        raise NotImplementedError(
            f"{self._class__.__name__} must implement getNumberofParams()")

    @abstractmethod
    def getMaxNumberofValues(self) -> int:
        """Return the maximum number of parameter values."""
        raise NotImplementedError(
            f"{self._class__.__name__} must implement getMaxNumberofValues()")

    @abstractmethod
    def print(self) -> None:
        """Print solution information.
        
        Must be implemented by subclasses to display solution details.
        """
        raise NotImplementedError(
            f"{self._class__.__name__} must implement print()")

    def isValid(self) -> bool:
        """Return whether the solution is valid."""
        return self._isValid

    def setValid(self, valid: bool) -> None:
        """Set the validity flag of the solution.
        
        Args:
            valid: True if solution is valid, False otherwise
        """
        self._isValid = valid

    @abstractmethod
    def getParametersValues(self):
        """Return the current values of all parameters."""
        raise NotImplementedError(f"{self._class__.__name__} must implement getParametersValues()")

    @abstractmethod
    def setParametersValues(self, buff: list) -> None:
        """Set parameter values.
        
        Args:
            buff: Array of parameter values
        """
        raise NotImplementedError

    @abstractmethod
    def getParameters(self) -> list:
        """Return the parameter objects."""
        raise NotImplementedError(
            f"{self._class__.__name__} must implement getParameters()")

    @abstractmethod
    def setParameters(self, params: list) -> None:
        """Set parameters.
        
        Args:
            params: List of parameter objects
        """
        raise NotImplementedError(
            f"{self._class__.__name__} must implement setParameters()")

    @abstractmethod
    def initialize(self, data) -> None:
        """Initialize solution with data.
        
        Args:
            data: Data object for initialization
        """
        raise NotImplementedError(
            f"{self._class__.__name__} must implement initialize()")

    @abstractmethod
    def prepare(self, filename: str) -> bool:
        """Prepare input file for solver.
        
        Args:
            filename: Output filename to prepare
        """
        raise NotImplementedError(
            f"{self._class__.__name__} must implement prepare()")
