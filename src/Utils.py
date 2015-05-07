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

"""
Global constants and structures
"""

#rank of each process
rank = -1
#number of processes
size = -1
#communicator
comm = None
#config file
cfile = ""
#start time
starttime = 0

#extra value for logging when a new solution has been found
extraLog = 100

#define enumerations


def enum(**enums):
    return type('Enum', (), enums)

#problem type
problemType = enum(NONE=0, FUSION=1, NONSEPARABLE=2)

#solution type
solutionType = enum(FUSION=1, NONSEPARABLE=2)

#solver type
solverType = enum(NONE=0, DAB=1, SA=2)

commModelType = enum(MASTERSLAVE=0, ALL2ALL=1)
#tags for MPI
tags = enum(RECVFROMMASTER=1, RECVFROMSLAVE=2, COMMSOLUTION=3,
            REQSENDINPUT=4, REQINPUT=5, ENDSIM=6)

objectiveType = enum(MINIMIZE=1, MAXIMIZE=2)

objective = objectiveType.MINIMIZE

commModel = commModelType.MASTERSLAVE

#logger class
logger = None

#number of iterations
iterations = 10

#very large double
infinity = 9.999999e+37

"""
Check if a float is nan
"""


def is_nan(x):
    return type(x) is float and x != x

"""
Given a file, it reads the last lines of the file.
Argument:
    -filepath: complete path of the file we want to read
    -read_size: how many characters we want to read
"""


def Tail(filepath, read_size=1024):
    # U is to open it with Universal newline support
    f = open(filepath, 'rU')
    offset = read_size
    f.seek(0, 2)
    file_size = f.tell()
    while 1:
        if file_size < offset:
            offset = file_size
        f.seek(-1 * offset, 2)
        read_str = f.read(offset)
        # Remove newline at the end
        if read_str[offset - 1] == '\n':
            read_str = read_str[0:-1]
        lines = read_str.split('\n')
        if len(lines) > 1:  # Got a line
            return lines[len(lines) - 1]
        if offset == file_size:   # Reached the beginning
            return read_str
        offset += read_size
    f.close()


class Matrix(object):
    def __init__(self, cols, rows, init=0.0):
        self.cols = cols
        self.rows = rows
        logger.debug("Init matrix [" + str(cols) + "][" + str(rows) + "]")
        # initialize matrix and fill with zeroes
        self.matrix = []
        for i in range(rows):
            logger.debug("Row " + str(i))
            ea_row = []
            for j in range(cols):
                ea_row.append(init)
            self.matrix.append(ea_row)
        logger.debug("Matrix initialised")

    def getNumRows(self):
        return (self.rows)

    def getNumCols(self):
        return (self.cols)

    def setitem(self, col, row, v):
        self.matrix[col - 1][row - 1] = v

    def getitem(self, col, row):
        return self.matrix[col - 1][row - 1]

    def __repr__(self):
        outStr = ""
        for i in range(self.rows):
            outStr += 'Row %s = %s\n' % (i + 1, self.matrix[i])
        return outStr
