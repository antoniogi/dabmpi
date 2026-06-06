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
        self.x_index = x_index if x_index is not None else -1
        self.y_index = y_index if y_index is not None else -1

    @property
    def to_be_modified(self) -> bool:
        """Dynamically checks if the parameter is open for optimization modifications."""
        return self.display and not self.fixed
