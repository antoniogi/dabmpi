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

from Parameter import Parameter
import Utils as u


class ParameterVMEC(Parameter):
    """
    Extension of the Parameter class. This class adds some extra attribute
    to a parameter (if it is fixed (we can fix a parameter at any time), if
    we have to display the parameter in the VMEC input file, and
    x & y indexes for parameters that are part of a matrix)
    """

    def __init__(self):
        Parameter.__init__(self)
        self.__display = False
        self.__fixed = False
        self.__x_index = None
        self.__y_index = None

    def set_x_index(self, index):
        try:
            if (index is not None):
                self.__x_index = int(index)
        except:
            pass

    def set_y_index(self, index):
        try:
            if (index is not None):
                self.__y_index = int(index)
        except:
            pass

    def set_display(self, display):
        self.__display = (str(display) == "True")

    def set_fixed(self, fixed):
        self.__fixed = (str(fixed) == "True")

    def get_display(self):
        return self.__display

    def get_fixed(self):
        return self.__fixed

    def to_be_modified(self):
        if (self.__fixed == False) and (self.__display == True):
            return True
        else:
            return False

    def get_x_index(self):
        return self.__x_index

    def get_y_index(self):
        return self.__y_index

    def print_value(self):
        if (self.__type == "bool"):
            if (self.__value):
                print (str(self.__name) + ' = TRUE')
                u.logger.info(str(self.__name) + ' = TRUE')
            else:
                print (str(self.__name) + ' = FALSE')
                u.logger.info(str(self.__name) + ' = FALSE')
        else:
            print (str(self.__name) + ' = ' + str(self.__value))
            u.logger.info(str(self.__name) + ' = ' + str(self.__value))

    def get_value_and_index(self):
        if (str(self.__type) == "float") or (str(self.__type) == "double"):
            return str("%.6E" % float(self.__value))
        else:
            return str(self.__value)
