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

import os
import sys
import math
import traceback
from xml.dom import minidom
from ParameterVMEC import ParameterVMEC
from Parameter import ParamType
from array import array

import subprocess


class VMECData (object):
    """
    This class stores all the data required by VMEC.
    It also provides methods to read the input xml file that, for each
    parameter, specifies the min/max/default values, the gap, the index,...
    It can also create an XML output file with the data it contains
    """
    def __init__(self, runtime):
        self._runtime = runtime
        self._numParams = 0
        self._maxRange = 0
        self._show_indata = True
        self._show_optimum = True
        self._show_bootin = True
        self._fInput = None

        self.mgrid_file = None
        self.loldout = None
        self.lwouttxt = None
        self.ldiagno = None
        self.lfreeb = None
        self.loptim = None
        self.delt = None
        self.tcon0 = None
        self.nfp = None
        self.ncurr = None
        self.mpol = None
        self.ntor = None
        self.nzeta = None
        self.ns = []
        self.niter = None
        self.nstep = None
        self.nvacskip = None
        self.gamma = None
        self.ftol = []
        self.phiedge = None
        self.bloat = None
        self.extcur = []
        self.curtor = None
        self.spres_ped = None
        self.pres_scale = None
        self.pmass = None
        self.am = []
        self.piota = None
        self.ai = []
        self.pcurr = None        
        self.ac = []
        self.raxis = []
        self.zaxis = []
        self.rbc = []
        self.zbc = []

        self.epsfcn = None
        self.niter_opt = None
        self.lreset_opt = None
        self.lprof_opt = None
        self.lbmn = None
        self.lfix_ntor = None
        self.lsurf_mask = None
        self.target_aspectratio = None
        self.target_beta = None
        self.target_maxcurrent = None
        self.target_rmax = None
        self.target_rmin = None
        self.target_iota = []
        self.target_well = []
        self.sigma_aspect = None
        self.sigma_curv = None
        self.sigma_beta = None
        self.sigma_kink = None
        self.sigma_maxcurrent = None
        self.sigma_rmax = None
        self.sigma_rmin = None
        self.sigma_iota = []
        self.sigma_vp = []
        self.sigma_bmin = []
        self.sigma_bmax = []
        self.sigma_ripple = []
        self.sigma_jstar0 = []
        self.sigma_jstar1 = []
        self.sigma_jstar2 = []
        self.sigma_jstar3 = []
        self.sigma_balloon = []
        self.sigma_pgrad = []
        self.sigma_pedge = None
        self.lballon_test = None
        self.bal_zeta0 = None
        self.bal_theta0 = None
        self.bal_xmax = None
        self.bal_np0 = None
        self.bal_kth = None
        self.bal_x0 = None

        self.nrh = None
        self.mbuse = None
        self.nbuse = None
        self.zeff1 = None
        self.damp = None
        self.isymm0 = None
        self.ate = None
        self.ati = None
        return

    def __del__(self):
        try:
            del self.ns[:]
            del self.am[:]
            del self.ai[:]
            del self.ac[:]
            del self.raxis[:]
            del self.zaxis[:]
            del self.rbc[:]
            del self.zbc[:]
            del self.ftol[:]
        except:
            pass

    #returns the number of parameters that can be actually modified
    def getNumParams(self):
        return self._numParams

    #returns the maximum range(maximum number of values) that a parameter
    #can take. This is the global maximum, meaning that most of the
    #parameters will take less values than this.
    #If param.max_value = 3, and param.min_value=1, and param.gap=1, the
    #range for param is 3 (it can take values 1,2,3)
    def getMaxRange(self):
        return self._maxRange

    """
    Returns a list of doubles with the values of the modificable parameters
    """
    def getValsOfParameters(self):
        buff = array('f', [0]) * self._numParams
        idx = 0
        if (self.delt.to_be_modified()):
            buff[idx] = float(self.delt.get_value())
            idx += 1
        if (self.tcon0.to_be_modified()):
            buff[idx] = float(self.tcon0.get_value())
            idx += 1
        if (self.nfp.to_be_modified()):
            buff[idx] = float(self.nfp.get_value())
            idx += 1
        if (self.ncurr.to_be_modified()):
            buff[idx] = float(self.ncurr.get_value())
            idx += 1
        if (self.mpol.to_be_modified()):
            buff[idx] = float(self.mpol.get_value())
            idx += 1
        if (self.ntor.to_be_modified()):
            buff[idx] = float(self.ntor.get_value())
            idx += 1
        if (self.nzeta.to_be_modified()):
            buff[idx] = float(self.nzeta.get_value())
            idx += 1
        for i in range(len(self.ns)):
            if (self.ns[i].to_be_modified()):
                buff[idx] = float(self.ns[i].get_value())
                idx += 1
        if (self.niter.to_be_modified()):
            buff[idx] = float(self.niter.get_value())
            idx += 1
        if (self.nstep.to_be_modified()):
            buff[idx] = float(self.nstep.get_value())
            idx += 1
        if (self.nvacskip.to_be_modified()):
            buff[idx] = float(self.nvacskip.get_value())
            idx += 1
        if (self.gamma.to_be_modified()):
            buff[idx] = float(self.gamma.get_value())
            idx += 1
        for i in range(len(self.ftol)):
            if (self.ftol[i].to_be_modified()):
                buff[idx] = float(self.ftol[i].get_value())
                idx += 1
        if (self.bloat.to_be_modified()):
            buff[idx] = float(self.bloat.get_value())
            idx += 1
        if (self.phiedge.to_be_modified()):
            buff[idx] = float(self.phiedge.get_value())
            idx += 1
        for i in range(len(self.extcur)):
            if (self.extcur[i].to_be_modified()):
                buff[idx] = float(self.extcur[i].get_value())
                idx += 1
        if (self.curtor.to_be_modified()):
            buff[idx] = float(self.curtor.get_value())
            idx += 1
        if (self.spres_ped.to_be_modified()):
            buff[idx] = float(self.spres_ped.get_value())
            idx += 1
        if (self.pres_scale.to_be_modified()):
            buff[idx] = float(self.pres_scale.get_value())
            idx += 1
        for i in range(len(self.am)):
            if (self.am[i].to_be_modified()):
                buff[idx] = float(self.am[i].get_value())
                idx += 1
        for i in range(len(self.ai)):
            if (self.ai[i].to_be_modified()):
                buff[idx] = float(self.ai[i].get_value())
                idx += 1
        for i in range(len(self.ac)):
            if (self.ac[i].to_be_modified()):
                buff[idx] = float(self.ac[i].get_value())
                idx += 1
        for i in range(len(self.raxis)):
            if (self.raxis[i].to_be_modified()):
                buff[idx] = float(self.raxis[i].get_value())
                idx += 1
        for i in range(len(self.zaxis)):
            if (self.zaxis[i].to_be_modified()):
                buff[idx] = float(self.zaxis[i].get_value())
                idx += 1
        for i in range(len(self.rbc)):
            if (self.rbc[i].to_be_modified()):
                buff[idx] = float(self.rbc[i].get_value())
                idx += 1
        for i in range(len(self.zbc)):
            if (self.zbc[i].to_be_modified()):
                buff[idx] = float(self.zbc[i].get_value())
                idx += 1
        if (self.epsfcn.to_be_modified()):
            buff[idx] = float(self.epsfcn.get_value())
            idx += 1
        if (self.niter_opt.to_be_modified()):
            buff[idx] = float(self.niter_opt.get_value())
            idx += 1
        if (self.lreset_opt.to_be_modified()):
            buff[idx] = float(self.lreset_opt.get_value())
            idx += 1
        if (self.lprof_opt.to_be_modified()):
            buff[idx] = float(self.lprof_opt.get_value())
            idx += 1
        if (self.lbmn.to_be_modified()):
            buff[idx] = float(self.lbmn.get_value())
            idx += 1
        if (self.lfix_ntor.to_be_modified()):
            buff[idx] = float(self.lfix_ntor.get_value())
            idx += 1
        if (self.lsurf_mask.to_be_modified()):
            buff[idx] = float(self.lsurf_mask.get_value())
            idx += 1
        if (self.target_aspectratio.to_be_modified()):
            buff[idx] = float(self.target_aspectratio.get_value())
            idx += 1
        if (self.target_beta.to_be_modified()):
            buff[idx] = float(self.target_beta.get_value())
            idx += 1
        if (self.target_maxcurrent.to_be_modified()):
            buff[idx] = float(self.target_maxcurrent.get_value())
            idx += 1
        if (self.target_rmax.to_be_modified()):
            buff[idx] = float(self.target_rmax.get_value())
            idx += 1
        if (self.target_rmin.to_be_modified()):
            buff[idx] = float(self.target_rmin.get_value())
            idx += 1
        for i in range(len(self.target_iota)):
            if (self.target_iota[i].to_be_modified()):
                buff[idx] = float(self.target_iota[i].get_value())
                idx += 1
        for i in range(len(self.target_well)):
            if (self.target_well[i].to_be_modified()):
                buff[idx] = float(self.target_well[i].get_value())
                idx += 1
        if (self.sigma_aspect.to_be_modified()):
            buff[idx] = float(self.sigma_aspect.get_value())
            idx += 1
        if (self.sigma_curv.to_be_modified()):
            buff[idx] = float(self.sigma_curv.get_value())
            idx += 1
        if (self.sigma_beta.to_be_modified()):
            buff[idx] = float(self.sigma_beta.get_value())
            idx += 1
        if (self.sigma_kink.to_be_modified()):
            buff[idx] = float(self.sigma_kink.get_value())
            idx += 1
        if (self.sigma_maxcurrent.to_be_modified()):
            buff[idx] = float(self.sigma_maxcurrent.get_value())
            idx += 1
        if (self.sigma_rmax.to_be_modified()):
            buff[idx] = float(self.sigma_rmax.get_value())
            idx += 1
        if (self.sigma_rmin.to_be_modified()):
            buff[idx] = float(self.sigma_rmin.get_value())
            idx += 1
        for i in range(len(self.sigma_iota)):
            if (self.sigma_iota[i].to_be_modified()):
                buff[idx] = float(self.sigma_iota[i].get_value())
                idx += 1
        for i in range(len(self.sigma_vp)):
            if (self.sigma_vp[i].to_be_modified()):
                buff[idx] = float(self.sigma_vp[i].get_value())
                idx += 1
        for i in range(len(self.sigma_bmin)):
            if (self.sigma_bmin[i].to_be_modified()):
                buff[idx] = float(self.sigma_bmin[i].get_value())
                idx += 1
        for i in range(len(self.sigma_bmax)):
            if (self.sigma_bmax[i].to_be_modified()):
                buff[idx] = float(self.sigma_bmax[i].get_value())
                idx += 1
        for i in range(len(self.sigma_ripple)):
            if (self.sigma_ripple[i].to_be_modified()):
                buff[idx] = float(self.sigma_ripple[i].get_value())
                idx += 1
        for i in range(len(self.sigma_jstar0)):
            if (self.sigma_jstar0[i].to_be_modified()):
                buff[idx] = float(self.sigma_jstar0[i].get_value())
                idx += 1
        for i in range(len(self.sigma_jstar1)):
            if (self.sigma_jstar1[i].to_be_modified()):
                buff[idx] = float(self.sigma_jstar1[i].get_value())
                idx += 1
        for i in range(len(self.sigma_jstar2)):
            if (self.sigma_jstar2[i].to_be_modified()):
                buff[idx] = float(self.sigma_jstar2[i].get_value())
                idx += 1
        for i in range(len(self.sigma_jstar3)):
            if (self.sigma_jstar3[i].to_be_modified()):
                buff[idx] = float(self.sigma_jstar3[i].get_value())
                idx += 1
        for i in range(len(self.sigma_balloon)):
            if (self.sigma_balloon[i].to_be_modified()):
                buff[idx] = float(self.sigma_balloon[i].get_value())
                idx += 1
        for i in range(len(self.sigma_pgrad)):
            if (self.sigma_pgrad[i].to_be_modified()):
                buff[idx] = float(self.sigma_pgrad[i].get_value())
                idx += 1
        if (self.sigma_pedge.to_be_modified()):
            buff[idx] = float(self.sigma_pedge.get_value())
            idx += 1
        if (self.lballon_test.to_be_modified()):
            buff[idx] = float(self.lballon_test.get_value())
            idx += 1
        if (self.bal_zeta0.to_be_modified()):
            buff[idx] = float(self.bal_zeta0.get_value())
            idx += 1
        if (self.bal_theta0.to_be_modified()):
            buff[idx] = float(self.bal_theta0.get_value())
            idx += 1
        if (self.bal_xmax.to_be_modified()):
            buff[idx] = float(self.bal_xmax.get_value())
            idx += 1
        if (self.bal_np0.to_be_modified()):
            buff[idx] = float(self.bal_np0.get_value())
            idx += 1
        if (self.bal_kth.to_be_modified()):
            buff[idx] = float(self.bal_kth.get_value())
            idx += 1
        if (self.bal_x0.to_be_modified()):
            buff[idx] = float(self.bal_x0.get_value())
            idx += 1
        if (self.nrh.to_be_modified()):
            buff[idx] = float(self.nrh.get_value())
            idx += 1
        if (self.mbuse.to_be_modified()):
            buff[idx] = float(self.mbuse.get_value())
            idx += 1
        if (self.nbuse.to_be_modified()):
            buff[idx] = float(self.nbuse.get_value())
            idx += 1
        if (self.zeff1.to_be_modified()):
            buff[idx] = float(self.zeff1.get_value())
            idx += 1
        if (self.damp.to_be_modified()):
            buff[idx] = float(self.damp.get_value())
            idx += 1
        if (self.isymm0.to_be_modified()):
            buff[idx] = float(self.isymm0.get_value())
            idx += 1
        if (self.ate.to_be_modified()):
            buff[idx] = float(self.ate.get_value())
            idx += 1
        if (self.ati.to_be_modified()):
            buff[idx] = float(self.ati.get_value())
            idx += 1

        return buff

    """
    Receives as parameter (buff) a list of values corresponding to the values
    that the parameters that can be modified must take.
    Goes through all of the parameters and changes the values of the modificable
    parameters to the value specified in this list
    """

    def setValsOfParameters(self, buff):
        self._runtime.logger.debug("VMECData. Setting parameters (number: " + str(len(buff)) + ")")
        idx = 0
        if (self.delt.to_be_modified()):
            self.delt.set_value(buff[idx])
            idx += 1
        if (self.tcon0.to_be_modified()):
            self.tcon0.set_value(buff[idx])
            idx += 1
        if (self.nfp.to_be_modified()):
            self.nfp.set_value(buff[idx])
            idx += 1
        if (self.ncurr.to_be_modified()):
            self.ncurr.set_value(buff[idx])
            idx += 1
        if (self.mpol.to_be_modified()):
            self.mpol.set_value(buff[idx])
            idx += 1
        if (self.ntor.to_be_modified()):
            self.ntor.set_value(buff[idx])
            idx += 1
        if (self.nzeta.to_be_modified()):
            self.nzeta.set_value(buff[idx])
            idx += 1
        for i in range(len(self.ns)):
            if (self.ns[i].to_be_modified()):
                self.ns[i].set_value(buff[idx])
                idx += 1
        if (self.niter.to_be_modified()):
            self.niter.set_value(buff[idx])
            idx += 1
        if (self.nstep.to_be_modified()):
            self.nstep.set_value(buff[idx])
            idx += 1
        if (self.nvacskip.to_be_modified()):
            self.nvacskip.set_value(buff[idx])
            idx += 1
        if (self.gamma.to_be_modified()):
            self.gamma.set_value(buff[idx])
            idx += 1
        for i in range(len(self.ftol)):
            if (self.ftol[i].to_be_modified()):
                self.ftol[i].set_value(buff[idx])
                idx += 1
        if (self.bloat.to_be_modified()):
            self.bloat.set_value(buff[idx])
            idx += 1
        if (self.phiedge.to_be_modified()):
            self.phiedge.set_value(buff[idx])
            idx += 1
        for i in range(len(self.extcur)):
            if (self.extcur[i].to_be_modified()):
                self.extcur[i].set_value(buff[idx])
                idx += 1
        if (self.curtor.to_be_modified()):
            self.curtor.set_value(buff[idx])
            idx += 1
        if (self.spres_ped.to_be_modified()):
            self.spres_ped.set_value(buff[idx])
            idx += 1
        if (self.pres_scale.to_be_modified()):
            self.pres_scale.set_value(buff[idx])
            idx += 1
        for i in range(len(self.am)):
            if (self.am[i].to_be_modified()):
                self.am[i].set_value(buff[idx])
                idx += 1
        for i in range(len(self.ai)):
            if (self.ai[i].to_be_modified()):
                self.ai[i].set_value(buff[idx])
                idx += 1
        for i in range(len(self.ac)):
            if (self.ac[i].to_be_modified()):
                self.ac[i].set_value(buff[idx])
                idx += 1
        for i in range(len(self.raxis)):
            if (self.raxis[i].to_be_modified()):
                self.raxis[i].set_value(buff[idx])
                idx += 1
        for i in range(len(self.zaxis)):
            if (self.zaxis[i].to_be_modified()):
                self.zaxis[i].set_value(buff[idx])
                idx += 1
        for i in range(len(self.rbc)):
            if (self.rbc[i].to_be_modified()):
                #just testing everything works fine
                #self._runtime.logger.debug ("rbc " + str(i) + " " + str(buff[idx]))
                self.rbc[i].set_value(buff[idx])
                idx += 1
        for i in range(len(self.zbc)):
            if (self.zbc[i].to_be_modified()):
                self.zbc[i].set_value(buff[idx])
                idx += 1
        if (self.epsfcn.to_be_modified()):
            self.epsfcn.set_value(buff[idx])
            idx += 1
        if (self.niter_opt.to_be_modified()):
            self.niter_opt.set_value(buff[idx])
            idx += 1
        if (self.lreset_opt.to_be_modified()):
            self.lreset_opt.set_value(buff[idx])
            idx += 1
        if (self.lprof_opt.to_be_modified()):
            self.lprof_opt.set_value(buff[idx])
            idx += 1
        if (self.lbmn.to_be_modified()):
            self.lbmn.set_value(buff[idx])
            idx += 1
        if (self.lfix_ntor.to_be_modified()):
            self.lfix_ntor.set_value(buff[idx])
            idx += 1
        if (self.lsurf_mask.to_be_modified()):
            self.lsurf_mask.set_value(buff[idx])
            idx += 1
        if (self.target_aspectratio.to_be_modified()):
            self.target_aspectratio.set_value(buff[idx])
            idx += 1
        if (self.target_beta.to_be_modified()):
            self.target_beta.set_value(buff[idx])
            idx += 1
        if (self.target_maxcurrent.to_be_modified()):
            self.target_maxcurrent.set_value(buff[idx])
            idx += 1
        if (self.target_rmax.to_be_modified()):
            self.target_rmax.set_value(buff[idx])
            idx += 1
        if (self.target_rmin.to_be_modified()):
            self.target_rmin.set_value(buff[idx])
            idx += 1
        for i in range(len(self.target_iota)):
            if (self.target_iota[i].to_be_modified()):
                self.target_iota[i].set_value(buff[idx])
                idx += 1
        for i in range(len(self.target_well)):
            if (self.target_well[i].to_be_modified()):
                self.target_well[i].set_value(buff[idx])
                idx += 1
        if (self.sigma_aspect.to_be_modified()):
            self.sigma_aspect.set_value(buff[idx])
            idx += 1
        if (self.sigma_curv.to_be_modified()):
            self.sigma_curv.set_value(buff[idx])
            idx += 1
        if (self.sigma_beta.to_be_modified()):
            self.sigma_beta.set_value(buff[idx])
            idx += 1
        if (self.sigma_kink.to_be_modified()):
            self.sigma_kink.set_value(buff[idx])
            idx += 1
        if (self.sigma_maxcurrent.to_be_modified()):
            self.sigma_maxcurrent.set_value(buff[idx])
            idx += 1
        if (self.sigma_rmax.to_be_modified()):
            self.sigma_rmax.set_value(buff[idx])
            idx += 1
        if (self.sigma_rmin.to_be_modified()):
            self.sigma_rmin.set_value(buff[idx])
            idx += 1
        for i in range(len(self.sigma_iota)):
            if (self.sigma_iota[i].to_be_modified()):
                self.sigma_iota[i].set_value(buff[idx])
                idx += 1
        for i in range(len(self.sigma_vp)):
            if (self.sigma_vp[i].to_be_modified()):
                self.sigma_vp[i].set_value(buff[idx])
                idx += 1
        for i in range(len(self.sigma_bmin)):
            if (self.sigma_bmin[i].to_be_modified()):
                self.sigma_bmin[i].set_value(buff[idx])
                idx += 1
        for i in range(len(self.sigma_bmax)):
            if (self.sigma_bmax[i].to_be_modified()):
                self.sigma_bmax[i].set_value(buff[idx])
                idx += 1
        for i in range(len(self.sigma_ripple)):
            if (self.sigma_ripple[i].to_be_modified()):
                self.sigma_ripple[i].set_value(buff[idx])
                idx += 1
        for i in range(len(self.sigma_jstar0)):
            if (self.sigma_jstar0[i].to_be_modified()):
                self.sigma_jstar0[i].set_value(buff[idx])
                idx += 1
        for i in range(len(self.sigma_jstar1)):
            if (self.sigma_jstar1[i].to_be_modified()):
                self.sigma_jstar1[i].set_value(buff[idx])
                idx += 1
        for i in range(len(self.sigma_jstar2)):
            if (self.sigma_jstar2[i].to_be_modified()):
                self.sigma_jstar2[i].set_value(buff[idx])
                idx += 1
        for i in range(len(self.sigma_jstar3)):
            if (self.sigma_jstar3[i].to_be_modified()):
                self.sigma_jstar3[i].set_value(buff[idx])
                idx += 1
        for i in range(len(self.sigma_balloon)):
            if (self.sigma_balloon[i].to_be_modified()):
                self.sigma_balloon[i].set_value(buff[idx])
                idx += 1
        for i in range(len(self.sigma_pgrad)):
            if (self.sigma_pgrad[i].to_be_modified()):
                self.sigma_pgrad[i].set_value(buff[idx])
                idx += 1
        if (self.sigma_pedge.to_be_modified()):
            self.sigma_pedge.set_value(buff[idx])
            idx += 1
        if (self.lballon_test.to_be_modified()):
            self.lballon_test.set_value(buff[idx])
            idx += 1
        if (self.bal_zeta0.to_be_modified()):
            self.bal_zeta0.set_value(buff[idx])
            idx += 1
        if (self.bal_theta0.to_be_modified()):
            self.bal_theta0.set_value(buff[idx])
            idx += 1
        if (self.bal_xmax.to_be_modified()):
            self.bal_xmax.set_value(buff[idx])
            idx += 1
        if (self.bal_np0.to_be_modified()):
            self.bal_np0.set_value(buff[idx])
            idx += 1
        if (self.bal_kth.to_be_modified()):
            self.bal_kth.set_value(buff[idx])
            idx += 1
        if (self.bal_x0.to_be_modified()):
            self.bal_x0.set_value(buff[idx])
            idx += 1
        if (self.nrh.to_be_modified()):
            self.nrh.set_value(buff[idx])
            idx += 1
        if (self.mbuse.to_be_modified()):
            self.mbuse.set_value(buff[idx])
            idx += 1
        if (self.nbuse.to_be_modified()):
            self.nbuse.set_value(buff[idx])
            idx += 1
        if (self.zeff1.to_be_modified()):
            self.zeff1.set_value(buff[idx])
            idx += 1
        if (self.damp.to_be_modified()):
            self.damp.set_value(buff[idx])
            idx += 1
        if (self.isymm0.to_be_modified()):
            self.isymm0.set_value(buff[idx])
            idx += 1
        if (self.ate.to_be_modified()):
            self.ate.set_value(buff[idx])
            idx += 1
        if (self.ati.to_be_modified()):
            self.ati.set_value(buff[idx])
            idx += 1
        return

    """
    Return a list with all the parameters (list of Parameter objects)
    """
    def getParameters(self):
        parameters = []
        try:
            if (self.mgrid_file.to_be_modified()):
                parameters.append(self.mgrid_file)
            if (self.lfreeb.to_be_modified()):
                parameters.append(self.lfreeb)
            if (self.loldout.to_be_modified()):
                parameters.append(self.loldout)
            if (self.lwouttxt.to_be_modified()):
                parameters.append(self.lwouttxt)
            if (self.ldiagno.to_be_modified()):
                parameters.append(self.ldiagno)
            if (self.loptim.to_be_modified()):
                parameters.append(self.loptim)
            if (self.delt.to_be_modified()):
                parameters.append(self.delt)

            if (self.tcon0.to_be_modified()):
                parameters.append(self.tcon0)
    
            if (self.nfp.to_be_modified()):
                parameters.append(self.nfp)

            if (self.ncurr.to_be_modified()):
                parameters.append(self.ncurr)

            if (self.mpol.to_be_modified()):
                parameters.append(self.mpol)

            if (self.ntor.to_be_modified()):
                parameters.append(self.ntor)

            if (self.nzeta.to_be_modified()):
                parameters.append(self.nzeta)

            for i in range(len(self.ns)):
                if (self.ns[i].to_be_modified()):
                    parameters.append(self.ns[i])

            if (self.niter.to_be_modified()):
                parameters.append(self.niter)

            if (self.nstep.to_be_modified()):
                parameters.append(self.nstep)

            if (self.nvacskip.to_be_modified()):
                parameters.append(self.nvacskip)

            if (self.gamma.to_be_modified()):
                parameters.append(self.gamma)

            for i in range(len(self.ftol)):
                if (self.ftol[i].to_be_modified()):
                    parameters.append(self.ftol[i])

            if (self.phiedge.to_be_modified()):
                parameters.append(self.phiedge)
            if (self.bloat.to_be_modified()):
                parameters.append(self.bloat)

            for i in range(len(self.extcur)):
                if (self.extcur[i].to_be_modified()):
                    parameters.append(self.extcur[i])

            if (self.curtor.to_be_modified()):
                parameters.append(self.curtor)
            if (self.spres_ped.to_be_modified()):
                parameters.append(self.spres_ped)
            if (self.pres_scale.to_be_modified()):
                parameters.append(self.pres_scale)

            for i in range(len(self.am)):
                if (self.am[i].to_be_modified()):
                    parameters.append(self.am[i])

            for i in range(len(self.ai)):
                if (self.ai[i].to_be_modified()):
                    parameters.append(self.ai[i])

            for i in range(len(self.ac)):
                if (self.ac[i].to_be_modified()):
                    parameters.append(self.ac[i])

            for i in range(len(self.raxis)):
                if (self.raxis[i].to_be_modified()):
                    parameters.append(self.raxis[i])

            for i in range(len(self.zaxis)):
                if (self.zaxis[i].to_be_modified()):
                    parameters.append(self.zaxis[i])

            for i in range(len(self.rbc)):
                if (self.rbc[i].to_be_modified()):
                    parameters.append(self.rbc[i])

            for i in range(len(self.zbc)):
                if (self.zbc[i].to_be_modified()):
                    parameters.append(self.zbc[i])

            if (self.epsfcn.to_be_modified()):
                parameters.append(self.epsfcn)

            if (self.niter_opt.to_be_modified()):
                parameters.append(self.niter_opt)

            if (self.lreset_opt.to_be_modified()):
                parameters.append(self.lreset_opt)

            if (self.lprof_opt.to_be_modified()):
                parameters.append(self.lprof_opt)

            if (self.lbmn.to_be_modified()):
                parameters.append(self.lbmn)

            if (self.lfix_ntor.to_be_modified()):
                parameters.append(self.lfix_ntor)

            if (self.lsurf_mask.to_be_modified()):
                parameters.append(self.lsurf_mask)

            if (self.target_aspectratio.to_be_modified()):
                parameters.append(self.target_aspectratio)

            if (self.target_beta.to_be_modified()):
                parameters.append(self.target_beta)

            if (self.target_maxcurrent.to_be_modified()):
                parameters.append(self.target_maxcurrent)

            if (self.target_rmax.to_be_modified()):
                parameters.append(self.target_rmax)

            if (self.target_rmin.to_be_modified()):
                parameters.append(self.target_rmin)

            for i in range(len(self.target_iota)):
                if (self.target_iota[i].to_be_modified()):
                    parameters.append(self.target_iota[i])

            for i in range(len(self.target_well)):
                if (self.target_well[i].to_be_modified()):
                    parameters.append(self.target_well[i])

            if (self.sigma_aspect.to_be_modified()):
                parameters.append(self.sigma_aspect)

            if (self.sigma_curv.to_be_modified()):
                parameters.append(self.sigma_curv)

            if (self.sigma_beta.to_be_modified()):
                parameters.append(self.sigma_beta)

            if (self.sigma_kink.to_be_modified()):
                parameters.append(self.sigma_kink)

            if (self.sigma_maxcurrent.to_be_modified()):
                parameters.append(self.sigma_maxcurrent)

            if (self.sigma_rmax.to_be_modified()):
                parameters.append(self.sigma_rmax)

            if (self.sigma_rmin.to_be_modified()):
                parameters.append(self.sigma_rmin)

            for i in range(len(self.sigma_iota)):
                if (self.sigma_iota[i].to_be_modified()):
                    parameters.append(self.sigma_iota[i])

            for i in range(len(self.sigma_vp)):
                if (self.sigma_vp[i].to_be_modified()):
                    parameters.append(self.sigma_vp[i])

            for i in range(len(self.sigma_bmin)):
                if (self.sigma_bmin[i].to_be_modified()):
                    parameters.append(self.sigma_bmin[i])

            for i in range(len(self.sigma_bmax)):
                if (self.sigma_bmax[i].to_be_modified()):
                    parameters.append(self.sigma_bmax[i])

            for i in range(len(self.sigma_ripple)):
                if (self.sigma_ripple[i].to_be_modified()):
                    parameters.append(self.sigma_ripple[i])

            for i in range(len(self.sigma_jstar0)):
                if (self.sigma_jstar0[i].to_be_modified()):
                    parameters.append(self.sigma_jstar0[i])

            for i in range(len(self.sigma_jstar1)):
                if (self.sigma_jstar1[i].to_be_modified()):
                    parameters.append(self.sigma_jstar1[i])

            for i in range(len(self.sigma_jstar2)):
                if (self.sigma_jstar2[i].to_be_modified()):
                    parameters.append(self.sigma_jstar2[i])

            for i in range(len(self.sigma_jstar3)):
                if (self.sigma_jstar3[i].to_be_modified()):
                    parameters.append(self.sigma_jstar3[i])

            for i in range(len(self.sigma_balloon)):
                if (self.sigma_balloon[i].to_be_modified()):
                    parameters.append(self.sigma_balloon[i])

            for i in range(len(self.sigma_pgrad)):
                if (self.sigma_pgrad[i].to_be_modified()):
                    parameters.append(self.sigma_pgrad[i])

            if (self.sigma_pedge.to_be_modified()):
                parameters.append(self.sigma_pedge)

            if (self.lballon_test.to_be_modified()):
                parameters.append(self.lballon_test)

            if (self.bal_zeta0.to_be_modified()):
                parameters.append(self.bal_zeta0)

            if (self.bal_theta0.to_be_modified()):
                parameters.append(self.bal_theta0)

            if (self.bal_xmax.to_be_modified()):
                parameters.append(self.bal_xmax)

            if (self.bal_np0.to_be_modified()):
                parameters.append(self.bal_np0)

            if (self.bal_kth.to_be_modified()):
                parameters.append(self.bal_kth)

            if (self.bal_x0.to_be_modified()):
                parameters.append(self.bal_x0)

            if (self.nrh.to_be_modified()):
                parameters.append(self.nrh)

            if (self.mbuse.to_be_modified()):
                parameters.append(self.mbuse)

            if (self.nbuse.to_be_modified()):
                parameters.append(self.nbuse)

            if (self.zeff1.to_be_modified()):
                parameters.append(self.zeff1)

            if (self.damp.to_be_modified()):
                parameters.append(self.damp)

            if (self.isymm0.to_be_modified()):
                parameters.append(self.isymm0)

            if (self.ate.to_be_modified()):
                parameters.append(self.ate)

            if (self.ati.to_be_modified()):
                parameters.append(self.ati)

        except Exception as e:
            self._runtime.logger.error("VMECData (" + str(sys.exc_info()[2].tb_lineno) + "). " + str(e))
            raise
            
        if (int(self._numParams) != len(parameters)):
            self._runtime.logger.error("VMECData. Incorrect number of parameters (" + str(self._numParams) + "--" + str(len(parameters)) + ")")
        return parameters

    """
    Assign a parameter with a new value to an older version of the same parameter
    """

    def _assign_to_list(self, attr_name, pos, parameter):
        lst = getattr(self, attr_name)
        if pos >= len(lst):
            lst.append(parameter)
        else:
            lst[pos] = parameter
        return 1

    def assign_parameter(self, parameter):
        DIRECT_ASSIGNMENTS = {
            0: "mgrid_file",
            1: "lfreeb",
            2: "loldout",
            3: "lwouttxt",
            4: "ldiagno",
            5: "loptim",
            6: "delt",
            7: "tcon0",
            8: "nfp",
            9: "ncurr",
            10: "mpol",
            11: "ntor",
            12: "nzeta",
            43: "niter",
            44: "nstep",
            45: "nvacskip",
            46: "gamma",
            52: "phiedge",
            53: "bloat",
            59: "curtor",
            60: "spres_ped",
            61: "pres_scale",
            62: "pmass",
            83: "piota",
            105: "pcurr",
            551: "epsfcn",
            552: "niter_opt",
            553: "lreset_opt",
            554: "lprof_opt",
            555: "lbmn",
            556: "lfix_ntor",
            557: "lsurf_mask",
            558: "target_aspectratio",
            559: "target_beta",
            560: "target_maxcurrent",
            561: "target_rmax",
            562: "target_rmin",
            585: "sigma_aspect",
            586: "sigma_curv",
            587: "sigma_beta",
            588: "sigma_kink",
            589: "sigma_maxcurrent",
            590: "sigma_rmax",
            591: "sigma_rmin",
            933: "sigma_pedge",
            934: "lballon_test",
            935: "bal_zeta0",
            936: "bal_theta0",
            937: "bal_xmax",
            938: "bal_np0",
            939: "bal_kth",
            940: "bal_x0",
            941: "nrh",
            942: "mbuse",
            943: "nbuse",
            944: "zeff1",
            945: "damp",
            946: "isymm0",
            947: "ate",
            948: "ati",
        }
        RANGE_ASSIGNMENTS = [
            (13, 42, "ns"),
            (47, 51, "ftol"),
            (54, 58, "extcur"),
            (63, 82, "am"),
            (84, 104, "ai"),
            (106, 128, "ac"),
            (129, 139, "raxis"),
            (140, 150, "zaxis"),
            (563, 573, "target_iota"),
            (574, 584, "target_well"),
            (592, 622, "sigma_iota"),
            (623, 653, "sigma_vp"),
            (654, 684, "sigma_bmin"),
            (685, 715, "sigma_bmax"),
            (716, 746, "sigma_ripple"),
            (747, 777, "sigma_jstar0"),
            (778, 808, "sigma_jstar1"),
            (809, 839, "sigma_jstar2"),
            (840, 870, "sigma_jstar3"),
            (871, 901, "sigma_balloon"),
            (902, 932, "sigma_pgrad"),
        ]
        index = parameter.get_index()

        # Direct assignments
        if attr := DIRECT_ASSIGNMENTS.get(index):
            setattr(self, attr, parameter)
            return 1

        # Standard ranged assignments
        for start, end, target in RANGE_ASSIGNMENTS:
            if start <= index <= end:
                return self._assign_to_list(target, index - start, parameter)

        # Special alternating rbc/zbc case
        if 151 <= index <= 550:
            offset = index - 151
            target = "rbc" if offset % 2 == 0 else "zbc"
            return self._assign_to_list(target, offset // 2, parameter)
        # If we reach this point, the parameter index is unrecognized.
        # Only log a warning if the parameter is meant to be displayed, otherwise silently ignore it.
        if parameter.get_display():
            self._runtime.logger.warning(
                f"Unassigned element with index: {index}"
            )
        return -1


    """
    Method that reads the xml input file. Puts into memory all the data
    contained in that file (min-max values, initial value, gap,...)
    Argument:
        - filepath: path to the XML input file
    """

    def initialize(self, filepath):
        try:
            if (not os.path.exists(filepath)):
                filepath = "../" + filepath
            xmldoc = minidom.parse(filepath)
            pNode = xmldoc.childNodes[0]
            for namelists in pNode.childNodes:
                if namelists.nodeType == namelists.ELEMENT_NODE:
                    if (namelists.attributes["display"].value == "False"):
                        if (namelists.localName == "indata"):
                            self._show_indata = False
                        if (namelists.localName == "optimum"):
                            self._show_optimum = False
                        if (namelists.localName == "bootin"):
                            self._show_bootin = False
                    for node in namelists.childNodes:
                        if node.nodeType == node.ELEMENT_NODE:
                            c = ParameterVMEC(self._runtime)
                            for node_param in node.childNodes:
                                if (node_param.nodeType == node_param.ELEMENT_NODE):
                                            name = node_param.localName
                                            # helper to safely read text
                                            text = None
                                            if node_param.firstChild is not None:
                                                text = node_param.firstChild.data

                                            if name == "display" and text is not None:
                                                c.set_display(text)

                                            if name == "fixed" and text is not None:
                                                c.set_fixed(text)

                                            if name == "type" and text is not None:
                                                t = text.strip().lower()
                                                mapping = {
                                                    "float": ParamType.FLOAT,
                                                    "double": ParamType.FLOAT,
                                                    "int": ParamType.INT,
                                                    "bool": ParamType.BOOL,
                                                    "string": ParamType.STRING,
                                                }
                                                c.set_type(mapping.get(t, ParamType.STRING))

                                            if name == "value" and text is not None:
                                                c.set_value(text)
                                                try:
                                                    if node_param.hasAttribute("x"):
                                                        x_index = node_param.getAttribute("x")
                                                        c.set_x_index(x_index)
                                                    if node_param.hasAttribute("y"):
                                                        y_index = node_param.getAttribute("y")
                                                        c.set_y_index(y_index)
                                                except Exception:
                                                    pass

                                            if name == "min_value" and text is not None:
                                                c.set_min_value(text)

                                            if name == "max_value" and text is not None:
                                                c.set_max_value(text)

                                            if name == "index" and text is not None:
                                                c.set_index(text)

                                            if name == "name" and text is not None:
                                                c.set_name(text)

                                            if name == "gap" and text is not None:
                                                c.set_gap(text)
                            try:
                                self.assign_parameter(c)
                                if (c.to_be_modified()):
                                    self._numParams += 1
                                    values = 1 + int(round((c.get_max_value() - c.get_min_value()) / c.get_gap()))
                                    self._maxRange = max(values, self._maxRange)
                            except Exception as e:
                                traceback.print_tb(sys.exc_info()[2])
                                self._runtime.logger.warning("Problem calculating max range: " + str(e))
                                pass
        except Exception as e:
            self._runtime.logger.error("VMECData (" + str(sys.exc_info()[2].tb_lineno) + "). Problem reading input xml file: " + str(e))
            traceback.print_tb(sys.exc_info()[2])
            sys.exit(111)
        return

    def _write_bool(self, f, name, param):
        if param.get_display():
            value = "T" if param.get_value() else "F"
            f.write(f"  {name} = {value}\n")


    def _write_scalar(self, f, name, param, fmt="{}"):
        if param.get_display():
            value = fmt.format(param.get_value())
            f.write(f"  {name} = {value}\n")


    def _write_array(
        self,
        f,
        name,
        params,
        fmt="{:.4E}",
        per_line=5,
        header_suffix=" = ",
    ):
        displayed = [p for p in params if p.get_display()]

        if not displayed:
            return

        values = [fmt.format(float(p.get_value())) for p in displayed]

        lines = [
            " ".join(values[i:i + per_line])
            for i in range(0, len(values), per_line)
        ]

        f.write(f"  {name}{header_suffix}")
        f.write("\n".join(lines))
        f.write("\n")


    def _write_group(self, f, params):
        """
        params:
            [
                ("NAME", parameter, format),
                ...
            ]
        """
        if not all(param.get_display() for _, param, _ in params):
            return
        values = [
            f"{name}={fmt.format(param.get_value())}"
            for name, param, fmt in params
        ]
        f.write(f"  {', '.join(values)}\n")

    def __write_indata(self, f_input):
        try:
            f_input.write("&INDATA\n")

            self._write_scalar(
                f_input,
                "MGRID_FILE",
                self.mgrid_file,
            )

            for name, param in [
                ("LFREEB", self.lfreeb),
                ("LOLDOUT", self.loldout),
                ("LWOUTTXT", self.lwouttxt),
                ("LDIAGNO", self.ldiagno),
                ("LOPTIM", self.loptim),
            ]:
                self._write_bool(f_input, name, param)

            scalar_fields = [
                ("DELT", self.delt, "{}"),
                ("TCON0", self.tcon0, "{}"),
                ("NFP", self.nfp, "{}"),
                ("NCURR", self.ncurr, "{:d}"),
                ("NZETA", self.nzeta, "{}"),
                ("NITER", self.niter, "{}"),
                ("NSTEP", self.nstep, "{}"),
                ("NVACSKIP", self.nvacskip, "{}"),
                ("GAMMA", self.gamma, "{:.6E}"),
                ("PHIEDGE", self.phiedge, "{:.6E}"),
                ("BLOAT", self.bloat, "{:.6E}"),
                ("CURTOR", self.curtor, "{}"),
                ("SPRES_PED", self.spres_ped, "{:.6E}"),
                ("PRES_SCALE", self.pres_scale, "{:.6E}"),
                ("PMASS_TYPE", self.pmass, "{}"),
                ("PIOTA_TYPE", self.piota, "{}"),
                ("PCURR_TYPE", self.pcurr, "{}"),
            ]

            for name, param, fmt in scalar_fields:
                self._write_scalar(f_input, name, param, fmt)

            if self.mpol.get_display() and self.ntor.get_display():
                f_input.write(
                    f"  MPOL = {self.mpol.get_value()}  "
                    f"NTOR = {self.ntor.get_value()}\n"
                )

            self._write_array(
                f_input,
                "NS_ARRAY",
                self.ns,
                fmt="{}",
            )

            self._write_array(
                f_input,
                "FTOL_ARRAY",
                self.ftol,
                fmt="{:.6E}",
            )

            self._write_array(
                f_input,
                "EXTCUR( 1)",
                self.extcur,
                fmt="{:.6E}",
            )

            self._write_array(
                f_input,
                "AM",
                self.am,
            )

            self._write_array(
                f_input,
                "AI",
                self.ai,
            )

            self._write_array(
                f_input,
                "AC",
                self.ac,
            )

            self._write_array(
                f_input,
                "RAXIS",
                self.raxis,
            )

            self._write_array(
                f_input,
                "ZAXIS",
                self.zaxis,
            )

            for rbc, zbs in zip(self.rbc, self.zbc):
                if not rbc.get_display():
                    continue

                f_input.write(
                    f"  RBC({rbc.get_x_index():3d},"
                    f"{rbc.get_y_index()}) = "
                    f"{float(rbc.get_value()): .4E}     "
                    f"ZBS({zbs.get_x_index():3d},"
                    f"{zbs.get_y_index()}) = "
                    f"{float(zbs.get_value()): .4E}\n"
                )

            f_input.write("/\n")

        except Exception:
            self._runtime.logger.exception(
                "Error writing INDATA section"
            )
            raise


    def __write_optimum(self, f_input):
        try:
            f_input.write("\n/\n&OPTIMUM\n")

            for name, param in [
                ("LRESET_OPT", self.lreset_opt),
                ("LPROF_OPT", self.lprof_opt),
                ("LBMN", self.lbmn),
                ("LBALLOON_TEST", self.lballon_test),
            ]:
                self._write_bool(f_input, name, param)

            scalar_fields = [
                ("EPSFCN", self.epsfcn, "{:.6E}"),
                ("NITER_OPT", self.niter_opt, "{:d}"),
                ("LFIX_NTOR", self.lfix_ntor, "{}"),
                ("LSURF_MASK", self.lsurf_mask, "{}"),
                ("TARGET_ASPECTRATIO", self.target_aspectratio, "{}"),
                ("TARGET_BETA", self.target_beta, "{:.4E}"),
                ("TARGET_MAXCURRENT", self.target_maxcurrent, "{}"),
                ("TARGET_RMAX", self.target_rmax, "{}"),
                ("TARGET_RMIN", self.target_rmin, "{}"),
                ("SIGMA_ASPECT", self.sigma_aspect, "{}"),
                ("SIGMA_CURV", self.sigma_curv, "{}"),
                ("SIGMA_BETA", self.sigma_beta, "{:.4E}"),
                ("SIGMA_KINK", self.sigma_kink, "{:.4E}"),
                ("SIGMA_MAXCURRENT", self.sigma_maxcurrent, "{:.4E}"),
                ("SIGMA_RMAX", self.sigma_rmax, "{:.4E}"),
                ("SIGMA_RMIN", self.sigma_rmin, "{:.4E}"),
                ("SIGMA_PEDGE", self.sigma_pedge, "{:.4E}"),
                ("BAL_ZETA0", self.bal_zeta0, "{:.4E}"),
                ("BAL_THETA0", self.bal_theta0, "{:.4E}"),
                ("BAL_XMAX", self.bal_xmax, "{:.4E}"),
                ("BAL_NP0", self.bal_np0, "{:d}"),
                ("BAL_KTH", self.bal_kth, "{:d}"),
                ("BAL_X0", self.bal_x0, "{:.4E}"),
            ]

            for name, param, fmt in scalar_fields:
                self._write_scalar(f_input, name, param, fmt)

            array_fields = [
                ("TARGET_IOTA", self.target_iota, "{:.4E}", 5),
                ("TARGET_WELL", self.target_well, "{:.4E}", 5),
                ("SIGMA_IOTA", self.sigma_iota, "{:.4E}", 5),
                ("SIGMA_VP", self.sigma_vp, "{:.4E}", 5),
                ("SIGMA_BMIN", self.sigma_bmin, "{:.4E}", 5),
                ("SIGMA_BMAX", self.sigma_bmax, "{:.4E}", 5),
                ("SIGMA_RIPPLE", self.sigma_ripple, "{:.4E}", 5),
                ("SIGMA_JSTAR(1,1)", self.sigma_jstar0, "{:.3E}", 8),
                ("SIGMA_JSTAR(1,2)", self.sigma_jstar1, "{:.3E}", 8),
                ("SIGMA_JSTAR(1,3)", self.sigma_jstar2, "{:.3E}", 8),
                ("SIGMA_JSTAR(1,4)", self.sigma_jstar3, "{:.3E}", 8),
                ("SIGMA_BALLOON", self.sigma_balloon, "{:.3E}", 8),
                ("SIGMA_PGRAD", self.sigma_pgrad, "{:.3E}", 8),
            ]

            for name, params, fmt, per_line in array_fields:
                self._write_array(
                    f_input,
                    name,
                    params,
                    fmt=fmt,
                    per_line=per_line,
                    header_suffix=" =\n",
                )

        except Exception:
            self._runtime.logger.exception(
                "Error writing OPTIMUM section"
            )
            raise

    """
    Writes the /bootin section of VMEC's input file
    Argument:
      - fInput: file struct that will store the input
    """

    def __write_bootin(self, f_input):
        try:
            f_input.write("/\n&BOOTIN\n")
            self._write_group(
                f_input,
                [
                    ("NRHO", self.nrh, "{}"),
                    ("MBUSE", self.mbuse, "{}"),
                    ("NBUSE", self.nbuse, "{}"),
                    ("ZEFF1", self.zeff1, "{}"),
                ],
            )
            self._write_group(
                f_input,
                [
                    ("DAMP", self.damp, "{}"),
                    ("ISYMM0", self.isymm0, "{}"),
                    ("ATE", self.ate, "{}"),
                ],
            )
            self._write_scalar(
                f_input,
                "ATI",
                self.ati,
            )
            f_input.write("/\n\n")
        except Exception:
            self._runtime.logger.exception(
                "Error writing BOOTIN section"
            )
            raise

    """
    Main method for creating the input file
    """

def create_input_file(self, filename):
    try:
        self._runtime.logger.debug(
            f"Worker {self._comms.rank} creating file {filename}"
        )
        with open(filename, "w", encoding="utf-8") as f_input:
            writers = [
                (self._show_indata, self._write_indata),
                (self._show_optimum, self._write_optimum),
                (self._show_bootin, self._write_bootin),
            ]
            for enabled, writer in writers:
                if enabled:
                    writer(f_input)
        return True
    except Exception:
        self._runtime.logger.exception(
            f"Error creating input file "
            f"(worker {self._comms.rank}): {filename}"
        )
        return False
