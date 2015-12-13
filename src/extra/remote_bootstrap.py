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


__version__ = '0.1 - 06-12-2013'

"""
HISTORY
    Version 0.1 (06-12-2013): Creation of the file.
"""

import sys
import os
import commands

def main(argv):
    try:
        commands.getoutput("cp -rf ../../../../external/DKES/* .")
        inputFile = "input.tj0"
        if (not os.path.lexists("xvmec2000")):
            commands.getoutput("ln -s ../../../../external/xvmec2000 xvmec2000")
        #commands.getoutput ("./xvmec2000 " + inputFile)
        if (not os.path.exists('wout_tj0.txt')):
            return
        if (not os.path.exists('threed1.tj0')):
            return
        commands.getoutput('mv wout_tj0.txt INPUT/wout_DAB_0.0.txt')
        commands.getoutput('mv threed1.tj0 INPUT/threed1.DAB_0.0')
        print('grep Radius INPUT/threed1.DAB_0.0 | head -2 | cut -f2 -d=| cut -f 1 -d"(" > temp.1')
        commands.getoutput('grep Radius INPUT/threed1.DAB_0.0 | head -2 | cut -f2 -d=| cut -f 1 -d"(" > temp.1')
        commands.getoutput('grep Radius INPUT/threed1.DAB_0.0 | head -2 | cut -f1 -d= > temp.2')
        commands.getoutput('paste temp.1 temp.2 > radius.dat')
        print("source EXE/dab.sh")
        out = commands.getoutput("source EXE/dab.sh")
        print(out)
        commands.getoutput ("source EXE/recoge_res.sh")

    except Exception, e:
        print("remote_bootstrap " + str(sys.exc_traceback.tb_lineno) + " " + str(e))

if __name__ == "__main__":
    main(sys.argv[1:])
