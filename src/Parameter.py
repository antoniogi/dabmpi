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
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional, Union


class ParamType(Enum):
    INT = 1
    FLOAT = 2
    BOOL = 3
    STRING = 4


Number = Union[int, float]


@dataclass
class Parameter:
    """
    Optimization parameter (e.g., GA gene).

    Fully type-safe version using Enum-based typing.
    """

    name: str = ""
    index: Optional[int] = None
    value: Any = None

    type: ParamType = ParamType.STRING
    gap: Optional[float] = None

    min_value: Optional[Number] = None
    max_value: Optional[Number] = None

    # ------------------------------------------------------------
    # Value handling
    # ------------------------------------------------------------

    def set_value(self, value: Any) -> None:
        if self.type == ParamType.STRING:
            self.value = str(value)

        elif self.type == ParamType.FLOAT:
            self.value = float(value)

        elif self.type == ParamType.INT:
            self.value = int(round(float(value)))

        elif self.type == ParamType.BOOL:
            if isinstance(value, bool):
                self.value = value
            elif isinstance(value, (int, float)):
                self.value = bool(value)
            else:
                self.value = str(value).strip().lower() in (
                    "true", "t", "1", "yes", "y"
                )

        else:
            raise ValueError(f"Unsupported ParamType: {self.type}")

    def get_value(self) -> Any:
        return self.value

    # ------------------------------------------------------------
    # Index
    # ------------------------------------------------------------

    def set_index(self, index: int) -> None:
        self.index = int(index)

    def get_index(self) -> Optional[int]:
        return self.index

    # ------------------------------------------------------------
    # Name / type
    # ------------------------------------------------------------

    def set_name(self, name: str) -> None:
        self.name = str(name)

    def get_name(self) -> str:
        return self.name

    def set_type(self, type_: ParamType) -> None:
        if not isinstance(type_, ParamType):
            raise TypeError("type_ must be a ParamType enum")
        self.type = type_

    def get_type(self) -> ParamType:
        return self.type

    # ------------------------------------------------------------
    # Bounds
    # ------------------------------------------------------------

    def set_min_value(self, v: Number) -> None:
        self.min_value = v

    def set_max_value(self, v: Number) -> None:
        self.max_value = v

    def validate_bounds(self) -> None:
        if (
            self.min_value is not None
            and self.max_value is not None
            and self.min_value > self.max_value
        ):
            raise ValueError(
                f"Invalid bounds: min_value ({self.min_value}) "
                f"> max_value ({self.max_value})"
            )

    # ------------------------------------------------------------
    # Gap
    # ------------------------------------------------------------

    def set_gap(self, gap: float) -> None:
        self.gap = float(gap)

    def get_gap(self) -> Optional[float]:
        return self.gap

    # ------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------

    def is_numeric(self) -> bool:
        return self.type in (ParamType.INT, ParamType.FLOAT)

    def is_in_bounds(self) -> bool:
        """Check if current value is within min/max bounds."""
        if self.value is None or not self.is_numeric():
            return True
        if self.min_value is not None and self.value < self.min_value:
            return False
        if self.max_value is not None and self.value > self.max_value:
            return False
        return True

    def __repr__(self) -> str:
        return (
            f"Parameter(name={self.name!r}, "
            f"type={self.type.name}, "
            f"value={self.value}, "
            f"index={self.index})"
        )