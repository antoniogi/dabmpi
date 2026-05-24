#!/usr/bin/env python3

from dataclasses import dataclass, field
from typing import Optional

from Parameter import Parameter, ParamType
import Utils as u


@dataclass
class ParameterVMEC(Parameter):
    """VMEC-specific parameter with display, fixed, and matrix indices."""

    display: bool = field(default=False)
    fixed: bool = field(default=False)

    x_index: Optional[int] = field(default=None)
    y_index: Optional[int] = field(default=None)

    # ------------------------------------------------------------
    # Index handling
    # ------------------------------------------------------------

    def set_x_index(self, index: Optional[int]) -> None:
        self.x_index = int(index) if index is not None else None

    def set_y_index(self, index: Optional[int]) -> None:
        self.y_index = int(index) if index is not None else None

    def get_x_index(self) -> Optional[int]:
        return self.x_index

    def get_y_index(self) -> Optional[int]:
        return self.y_index

    # ------------------------------------------------------------
    # Flags
    # ------------------------------------------------------------

    def set_display(self, display: bool) -> None:
        self.display = bool(display)

    def set_fixed(self, fixed: bool) -> None:
        self.fixed = bool(fixed)

    def get_display(self) -> bool:
        return self.display

    def get_fixed(self) -> bool:
        return self.fixed

    def to_be_modified(self) -> bool:
        return self.display and not self.fixed

    # ------------------------------------------------------------
    # Output helpers
    # ------------------------------------------------------------

    def print_value(self) -> None:
        if self.type == ParamType.BOOL:
            value_str = "TRUE" if self.value else "FALSE"
        else:
            value_str = str(self.value)

        u.logger.info(f"{self.name} = {value_str}")

    def get_value_and_index(self) -> str:
        if self.type == ParamType.FLOAT:
            return f"{float(self.value):.6E}"
        if self.type == ParamType.INT:
            return str(int(self.value))
        return str(self.value)