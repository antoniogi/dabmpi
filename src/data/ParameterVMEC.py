#!/usr/bin/env python
# vim: set fileencoding=utf-8 :

import logging

from .Parameter import INFINITY, Parameter, ParamType


class ParameterVMEC(Parameter):
    """
    Extension of the Parameter class. This class adds some extra attribute
    to a parameter (if it is fixed (we can fix a parameter at any time), if
    we have to display the parameter in the VMEC input file, and
    x & y indexes for parameters that are part of a matrix)
    """

    def __init__(
        self,
        runtime=None,
        name: str = "",
        index=None,
        type=None,
        value=None,
        gap=None,
        min_value=None,
        max_value=None,
    ):
        super().__init__(
            runtime=runtime,
            name=name,
            index=index,
            type=type or ParamType.STRING,
            value=value,
            gap=gap,
            min_value=min_value if min_value is not None else -INFINITY,
            max_value=max_value if max_value is not None else INFINITY,
        )
        self.display = False
        self.fixed = False
        self.x_index = None
        self.y_index = None

    def set_x_index(self, index):
        if index is None:
            self.x_index = None
            return

        self.x_index = int(index)

    def set_y_index(self, index):
        if index is None:
            self.y_index = None
            return

        self.y_index = int(index)

    def set_display(self, display):
        if isinstance(display, str):
            self.display = display.strip().lower() in ("true", "t", "yes", "1")
            return

        self.display = bool(display)

    def set_fixed(self, fixed):
        if isinstance(fixed, str):
            self.fixed = fixed.strip().lower() in ("true", "t", "yes", "1")
            return

        self.fixed = bool(fixed)

    def get_display(self):
        return self.display

    def get_fixed(self):
        return self.fixed

    def to_be_modified(self):
        return self.display and not self.fixed

    def get_x_index(self):
        return self.x_index

    def get_y_index(self):
        return self.y_index

    def _logger(self):
        if getattr(self, "_runtime", None) is not None and getattr(self._runtime, "logger", None) is not None:
            return self._runtime.logger
        return logging.getLogger(__name__)


    def print_value(self):
        logger = self._logger()
        if self._type == ParamType.BOOL:
            formatted_value = "TRUE" if self._value else "FALSE"
        else:
            formatted_value = self._value

        logger.info(f"{self._name} = {formatted_value}")

    def get_value_and_index(self):
        if self._type == ParamType.FLOAT:
            return f"{float(self._value):.6E}"
        return str(self._value)