#!/usr/bin/env python

import os
from array import array
import xml.etree.ElementTree as ET

from .Parameter import Parameter


class CristinaData:
    """
    This class stores all the data required by VMEC.
    It reads and writes structural parameter data via XML configuration.
    """

    def __init__(self, runtime):
        self._maxRange = 0
        self._fInput = None
        self._parameters = []
        self._runtime = runtime

    @property
    def num_parameters(self):
        """Dynamically returns the number of parameters."""
        return len(self._parameters)

    @property
    def max_range(self):
        return self._maxRange

    @property
    def parameters(self):
        return self._parameters

    @parameters.setter
    def parameters(self, parameters):
        self._parameters = parameters

    def print_data(self):
        for i, param in enumerate(self._parameters):
            self._runtime.logger.info(
                f"CristinaData. Param({i}) - Value: {param.get_value()}"
            )

    def get_parameters_values(self):
        """Returns a float array of modifiable parameter values."""
        return array("f", [float(p.get_value()) for p in self._parameters])

    def set_parameters_values(self, buff):
        """Updates internal parameter states from an iterable buffer."""
        self._runtime.logger.debug(
            f"CristinaData. Setting parameters (number: {len(buff)})"
        )
        for i, val in enumerate(buff):
            if i < len(self._parameters):
                self._parameters[i].set_value(val)

    def set_parameters(self, parameters):
        for param in parameters:
            self.assign_parameter(param)

    def assign_parameter(self, parameter):
        # NOTE: If parameter.get_index() returns a string from XML, cast it to int here.
        try:
            index = int(parameter.get_index())
        except (TypeError, ValueError):
            index = len(self._parameters)

        if index >= len(self._parameters):
            self._parameters.append(parameter)

    def initialize(self, filepath):
        """Reads the xml input file and builds the parameter tree all at once."""
        if not os.path.exists(filepath):
            filepath = os.path.join("..", filepath)

        try:
            tree = ET.parse(filepath)
            root = tree.getroot()

            for node in root:
                # 1. Gather configuration details out of XML child tags
                raw_data = {
                    "name": "",
                    "index": None,
                    "type": "string",
                    "value": None,
                    "gap": None,
                    "min_value": None,
                    "max_value": None,
                }

                for param_node in node:
                    tag = param_node.tag
                    # Map the XML tag 'type' to our internal argument 'ptype' to avoid conflicting with builtins
                    arg_key = "ptype" if tag == "type" else tag
                    if arg_key in raw_data or tag == "type":
                        raw_data[arg_key] = param_node.text

                try:
                    # 2. Instantiate Parameter using dictionary unpacking
                    c = Parameter(
                        name=raw_data["name"],
                        index=raw_data["index"],
                        ptype=raw_data["ptype"],
                        value=raw_data["value"],
                        gap=raw_data["gap"],
                        min_value=raw_data["min_value"],
                        max_value=raw_data["max_value"],
                    )

                    self.assign_parameter(c)

                    # 3. Handle structural limits based on completed attributes
                    if c.is_numeric and c.gap:
                        values = 1 + int(
                            round((float(c.max_value) - float(c.min_value)) / c.gap)
                        )
                        self._maxRange = max(values, self._maxRange)

                except (ValueError, TypeError) as e:
                    self._runtime.logger.warning(
                        f"Problem processing parameter from XML: {e}"
                    )

            self._runtime.logger.debug(
                f"Number of parameters {self.num_parameters}({len(self._parameters)})"
            )

        except Exception as e:
            self._runtime.logger.exception(
                "CristinaData. Exception while initializing from XML file"
            )
            raise RuntimeError(
                "Failed to initialize system state from XML configuration."
            ) from e
