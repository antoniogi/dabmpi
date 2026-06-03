#!/usr/bin/env python

from .Parameter import INFINITY, Parameter, ParamType

class ParameterVMEC(Parameter):
    """
    Extension of Parameter with VMEC-specific metadata.
    """

    def __init__(
        self,
        name: str,
        index: int,
        ptype: ParamType | None,
        value,
        gap: float,
        min_value: float | None,
        max_value: float | None,
        x_index: int,
        y_index: int,
        fixed: bool,
        display: bool,
    ):
        super().__init__(
            name=name,
            index=index,
            ptype=ptype or ParamType.STRING,
            value=value,
            gap=gap,
            min_value=min_value if min_value is not None else -INFINITY,
            max_value=max_value if max_value is not None else INFINITY,
        )

        self.display = display
        self.fixed = fixed
        self.x_index = x_index
        self.y_index = y_index

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
