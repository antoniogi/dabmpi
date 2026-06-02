#!/usr/bin/env python3

from __future__ import annotations

import math
from enum import IntEnum
from typing import Any, Optional

INFINITY = math.inf


class ParamType(IntEnum):
    INT = 1
    FLOAT = 2
    BOOL = 3
    STRING = 4


TRUE_VALUES = {"true", "t", "yes", "y", "1"}
FALSE_VALUES = {"false", "f", "no", "n", "0"}


class Parameter:
    """Represents a parameter used during optimization."""

    def __init__(
        self,
        runtime: Any | None = None,
        name: str = "",
        index: int | None = None,
        type: ParamType = ParamType.STRING,
        value: Any = None,
        gap: float | None = None,
        min_value: Any = -INFINITY,
        max_value: Any = INFINITY,
    ) -> None:
        self._runtime = runtime
        self._name = str(name)
        self._index = int(index) if index is not None else None
        self._type = type
        self._value = None
        self._gap = float(gap) if gap is not None else None
        self._min_value = min_value
        self._max_value = max_value

        if not isinstance(self._type, ParamType):
            raise TypeError("type must be a ParamType")

        if value is not None:
            self.set_value(value)

    def _parse_bool(self, value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0
        normalized = str(value).strip().lower()
        if normalized in TRUE_VALUES:
            return True
        if normalized in FALSE_VALUES:
            return False
        raise ValueError(f"Cannot parse boolean value: {value}")

    def set_value(self, value: Any) -> None:
        if self._type == ParamType.STRING:
            self._value = str(value)
            return

        if self._type == ParamType.FLOAT:
            self._value = float(value)
            return

        if self._type == ParamType.INT:
            self._value = int(round(float(value)))
            return

        if self._type == ParamType.BOOL:
            self._value = self._parse_bool(value)
            return

        raise TypeError(f"Unsupported parameter type: {self._type}")

    def get_index(self) -> int | None:
        return self._index

    def set_index(self, index: Any) -> None:
        self._index = int(index)

    def get_name(self) -> str:
        return self._name

    def set_name(self, name: Any) -> None:
        self._name = str(name)

    def set_type(self, type_: Any) -> None:
        if isinstance(type_, ParamType):
            self._type = type_
            return

        if isinstance(type_, str):
            normalized = type_.strip()
            if normalized in ("float", "double"):
                self._type = ParamType.FLOAT
                return
            if normalized == "int":
                self._type = ParamType.INT
                return
            if normalized == "bool":
                self._type = ParamType.BOOL
                return
            if normalized == "string":
                self._type = ParamType.STRING
                return

        raise TypeError("type must be a ParamType")

    def get_type(self) -> ParamType:
        return self._type

    def get_value(self) -> Any:
        if self._type == ParamType.FLOAT:
            return float(self._value)
        if self._type == ParamType.INT:
            return int(self._value)
        if self._type == ParamType.BOOL:
            return self._parse_bool(self._value)
        return self._value

    def set_min_value(self, min_value: Any) -> None:
        if self._type == ParamType.STRING:
            self._min_value = str(min_value)
            return
        if self._type == ParamType.FLOAT:
            self._min_value = float(min_value)
            return
        if self._type == ParamType.INT:
            self._min_value = int(min_value)
            return
        if self._type == ParamType.BOOL:
            self._min_value = self._parse_bool(min_value)
            return
        raise TypeError(f"Unsupported parameter type: {self._type}")

    def get_min_value(self) -> Any:
        return self._min_value

    def set_max_value(self, max_value: Any) -> None:
        if self._type == ParamType.STRING:
            self._max_value = str(max_value)
            return
        if self._type == ParamType.FLOAT:
            self._max_value = float(max_value)
            return
        if self._type == ParamType.INT:
            self._max_value = int(max_value)
            return
        if self._type == ParamType.BOOL:
            self._max_value = self._parse_bool(max_value)
            return
        raise TypeError(f"Unsupported parameter type: {self._type}")

    def get_max_value(self) -> Any:
        return self._max_value

    def set_gap(self, gap: Any) -> None:
        self._gap = float(gap)

    def get_gap(self) -> float | None:
        return self._gap

    def is_numeric(self) -> bool:
        return self._type in {ParamType.INT, ParamType.FLOAT}

    def validate_bounds(self) -> None:
        if float(self._min_value) > float(self._max_value):
            raise ValueError(
                f"min_value ({self._min_value}) must be less than or equal to max_value ({self._max_value})"
            )

    def __repr__(self) -> str:
        return (
            f"Parameter(name={self._name!r}, index={self._index}, "
            f"type={self._type.name}, value={self._value!r})"
        )

    @property
    def type(self) -> ParamType:
        return self._type

    @type.setter
    def type(self, type_: Any) -> None:
        self.set_type(type_)

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, name: Any) -> None:
        self.set_name(name)

    @property
    def index(self) -> int | None:
        return self._index

    @index.setter
    def index(self, index: Any) -> None:
        self.set_index(index)
