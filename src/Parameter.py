#!/usr/bin/env python
# vim: set fileencoding=utf-8 :

#############################################################################
#    Copyright 2013  by Antonio Gomez and Miguel Cardenas                   #
#                                                                           #
#   Licensed under the Apache License, Version 2.0 (the "License");         #
#   you may not use this file except in compliance with the License.        #
#   You may obtain a copy of the License at                                 #
#                                                                           #
#       http://www.apache.org/licenses/LICENSE-2.0                          #
#                                                                           #
#   Unless required by applicable law or agreed to in writing, software     #
#   distributed under the License is distributed on an "AS IS" BASIS,       #
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.#
#   See the License for the specific language governing permissions and     #
#   limitations under the License.                                          #
#############################################################################

__author__ = ' AUTHORS:     Antonio Gomez (antonio.gomez@csiro.au)'


__version__ = ' REVISION:   1.0  -  15-01-2014'

"""
HISTORY
    Version 0.1 (12-04-2013):   Creation of the file.
    Version 1.0 (15-01-2014):   Fist stable version.
"""

import Utils as u


class Parameter(object):
    """
    This class represents a parameter of the problem that will be used
    during the optimization (a chromosome in Genetic Algorithms).
    """

    def __init__(self):
        self.__value = None
        self.__type = "string"
        self.__name = ""
        self.__index = None
        self.__gap = None
        self.__min_value = -u.infinity
        self.__max_value = u.infinity

    def set_value(self, value):
        try:
            if (self.__type == "string"):
                self.__value = value
            elif (self.__type == "double") or (self.__type == "float"):
                self.__value = float(value)
            elif (self.__type == "bool"):
                self.__value = ((value == "T") or (value == "True") or
                               (value == "TRUE"))
            else:
                self.__value = int(round(value))
        except Exception as e:
            u.logger.error("Parameter. Error when setting value of " +
                            "parameter: " + str(e))

    def get_index(self):
        return (self.__index)

    def set_index(self, index):
        try:
            self.__index = int(index)
        except Exception as e:
            u.logger.error("Parameter. Error when copying getting value of " +
                            "parameter: " + str(e))

    def set_name(self, name):
        self.__name = str(name)

    def get_name(self):
        return (self.__name)

    def set_type(self, type_):
        self.__type = type_

    def get_type(self):
        return self.__type

    def get_value(self):
        if (self.__type == "double" or self.__type == "float"):
            return float(self.__value)
        if (self.__type == "int"):
            return int(self.__value)
        if (self.__type == "bool"):
            if (self.__value == "T") or (self.__value == "True"):
                return True
            else:
                return False
        return self.__value

    def set_min_value(self, min_value):
        try:
            if (self.__type == "string"):
                self.__min_value = ""
            elif (self.__type == "double"):
                self.__min_value = float(min_value)
            elif (self.__type == "bool"):
                self.__min_value = False
            else:
                self.__min_value = int(min_value)
        except Exception as e:
            u.logger.error("Parameter. Error when copying min value of " +
                            "parameter: " + str(e))

    def get_min_value(self):
        return (self.__min_value)

    def set_max_value(self, max_value):
        try:
            if (self.__type == "string"):
                self.__max_value = ""
            elif (self.__type == "double"):
                self.__max_value = float(max_value)
            elif (self.__type == "bool"):
                self.__max_value = True
            else:
                self.__max_value = int(max_value)
        except Exception as e:
            u.logger.error("Parameter. Error when copying max value of " +
                            "parameter: " + str(e))

    def get_max_value(self):
        return self.__max_value

    def __getitem__(self, item):
        return (self.__index)

    def set_gap(self, gap):
        self.__gap = float(gap)

    def get_gap(self):
        return (self.__gap)
