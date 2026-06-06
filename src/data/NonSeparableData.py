#!/usr/bin/env python3

import os
from array import array
import xml.etree.ElementTree as ET

from .Parameter import Parameter, ParamType


class NonSeparableData:
    """
    This class stores all the data required by VMEC.
    Handles non-separable structural configuration parameter groups.
    """

    def __init__(self, runtime) -> None:
        self._maxRange = 0
        self._fInput = None
        self._params: list[Parameter] = []
        self._logger = runtime.logger

    @property
    def num_params(self) -> int:
        """Dynamically returns the number of active parameters."""
        return len(self._params)

    @property
    def max_range(self) -> int:
        return self._maxRange

    @property
    def params(self) -> list[Parameter]:
        """Exposes the collection of Parameter objects."""
        return self._params

    @params.setter
    def params(self, parameters: list[Parameter]) -> None:
        self._params = parameters

    def get_params_values(self) -> array:
        """Returns a float array containing the current values of the parameters."""
        return array("f", [float(p.value) for p in self._params])

    def set_params_values(self, buff: list[float] | array) -> None:
        """Updates internal parameter states sequence-wise from an iterable buffer."""
        self._logger.debug(
            f"NonSeparableData. Setting parameters (number: {len(buff)})"
        )
        for i, val in enumerate(buff):
            if i < len(self._params):
                self._params[i].value = val

    def set_parameters(self, parameters: list[Parameter]) -> None:
        for param in parameters:
            self.assign_parameter(param)

    def assign_parameter(self, parameter: Parameter) -> None:
        """Assigns or appends a Parameter structural object."""
        try:
            index = (
                int(parameter.index)
                if parameter.index is not None
                else len(self._params)
            )
        except (TypeError, ValueError):
            index = len(self._params)

        if index >= len(self._params):
            self._params.append(parameter)

    def initialize(self, filepath: str) -> None:
        """Reads the XML input file and instantiates immutable-ready parameter states."""
        if not os.path.exists(filepath):
            filepath = os.path.join("..", filepath)

        try:
            tree = ET.parse(filepath)
            root = tree.getroot()

            for node in root:
                # 1. Use explicitly typed local variables to keep Mypy happy
                p_name = ""
                p_index_str: str | None = None
                p_type_str = "string"
                p_value: str | None = None
                p_gap_str: str | None = None
                p_min_value: str | None = None
                p_max_value: str | None = None

                for param_node in node:
                    tag = param_node.tag
                    val = param_node.text
                    if tag == "name" and val is not None:
                        p_name = val
                    elif tag == "index":
                        p_index_str = val
                    elif tag == "type" and val is not None:
                        p_type_str = val
                    elif tag == "value":
                        p_value = val
                    elif tag == "gap":
                        p_gap_str = val
                    elif tag == "min_value":
                        p_min_value = val
                    elif tag == "max_value":
                        p_max_value = val

                try:
                    # Resolve string to ParamType Enum to satisfy expected type
                    type_mapping = {
                        "float": ParamType.FLOAT,
                        "double": ParamType.FLOAT,
                        "int": ParamType.INT,
                        "bool": ParamType.BOOL,
                        "string": ParamType.STRING,
                    }
                    ptype_enum = type_mapping.get(
                        p_type_str.strip().lower(), ParamType.STRING
                    )

                    # Safely convert primitives with explicit fallbacks
                    p_index = int(p_index_str) if p_index_str is not None else 0
                    p_gap = float(p_gap_str) if p_gap_str is not None else 0.0

                    # 2. Instantiate Parameter using clean, typed arguments
                    c = Parameter(
                        name=p_name,
                        index=p_index,
                        ptype=ptype_enum,
                        value=p_value,
                        gap=p_gap,
                        min_value=p_min_value,
                        max_value=p_max_value,
                    )

                    self.assign_parameter(c)

                    # 3. Add parentheses to is_numeric() to resolve truthy function error
                    if c.is_numeric() and c.gap:
                        values = 1 + int(
                            round((float(c.max_value) - float(c.min_value)) / c.gap)
                        )
                        self._maxRange = max(values, self._maxRange)

                except Exception:
                    self._logger.exception(
                        f"Problem calculating max range for parameter with index "
                        f"{p_index_str} and name {p_name}"
                    )
                    raise

            self._logger.debug(
                f"Number of parameters {self.num_params}({len(self._params)})"
            )

        except Exception as e:
            self._logger.exception(
                "NonSeparableData. Exception while initializing from XML file"
            )
            raise RuntimeError(
                "Failed to safely build framework structural elements from configuration source."
            ) from e
