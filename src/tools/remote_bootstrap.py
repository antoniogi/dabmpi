#!/usr/bin/env python
# vim: set fileencoding=utf-8 :


import sys
import os
import subprocess

def main(argv):
    try:
        subprocess.getoutput("cp -rf ../../../../external/DKES/* .")
        inputFile = "input.tj0"
        if not os.path.lexists("xvmec2000"):
            subprocess.getoutput("ln -s ../../../../external/xvmec2000 xvmec2000")
        # subprocess.getoutput("./xvmec2000 " + inputFile)
        if not os.path.exists('wout_tj0.txt'):
            return
        if not os.path.exists('threed1.tj0'):
            return
        subprocess.getoutput('mv wout_tj0.txt INPUT/wout_DAB_0.0.txt')
        subprocess.getoutput('mv threed1.tj0 INPUT/threed1.DAB_0.0')
        print('grep Radius INPUT/threed1.DAB_0.0 | head -2 | cut -f2 -d=| cut -f 1 -d"(" > temp.1')
        subprocess.getoutput('grep Radius INPUT/threed1.DAB_0.0 | head -2 | cut -f2 -d=| cut -f 1 -d"(" > temp.1')
        subprocess.getoutput('grep Radius INPUT/threed1.DAB_0.0 | head -2 | cut -f1 -d= > temp.2')
        subprocess.getoutput('paste temp.1 temp.2 > radius.dat')
        print("source EXE/dab.sh")
        out = subprocess.getoutput("source EXE/dab.sh")
        print(out)
        subprocess.getoutput("source EXE/recoge_res.sh")

    except Exception as e:
        print("remote_bootstrap " + str(sys.exc_info()[2].tb_lineno) + " " + str(e))

if __name__ == "__main__":
    main(sys.argv[1:])
