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
import Utils as u
from ParameterVMEC import ParameterVMEC
from array import array
import imp

subProcFound = False
try:
    imp.find_module('subprocess')
    subProcFound = True
    import subprocess
except ImportError:
    subProcFound = False


class VMECData (object):
    """
    This class stores all the data required by VMEC.
    It also provides methods to read the input xml file that, for each
    parameter, specifies the min/max/default values, the gap, the index,...
    It can also create an XML output file with the data it contains
    """
    def __init__(self):
        self.__numParams = 0
        self.__maxRange = 0
        self.__show_indata = True
        self.__show_optimum = True
        self.__show_bootin = True
        self.__fInput = None

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
        return self.__numParams

    #returns the maximum range(maximum number of values) that a parameter
    #can take. This is the global maximum, meaning that most of the
    #parameters will take less values than this.
    #If param.max_value = 3, and param.min_value=1, and param.gap=1, the
    #range for param is 3 (it can take values 1,2,3)
    def getMaxRange(self):
        return self.__maxRange

    """
    Returns a list of doubles with the values of the modificable parameters
    """
    def getValsOfParameters(self):
        buff = array('f', [0]) * self.__numParams
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
        u.logger.debug("VMECData. Setting parameters (number: " + str(len(buff)) + ")")
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
                #u.logger.debug ("rbc " + str(i) + " " + str(buff[idx]))
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

        if (int(self.__numParams) != len(parameters)):
            u.logger.error("VMECData. Incorrect number of parameters (" + str(self.__numParams) + "--" + str(len(parameters)) + ")")
        return parameters

    """
    Assign a parameter with a new value to an older version of the same parameter
    """

    def assign_parameter(self, parameter):
        index = parameter.get_index()
        if (index == 0):
            self.mgrid_file = parameter
            return 1
        if (index == 1):
            self.lfreeb = parameter
            return 1
        if (index == 2):
            self.loldout = parameter
            return 1
        if (index == 3):
            self.lwouttxt = parameter
            return 1
        if (index == 4):
            self.ldiagno = parameter
            return 1
        if (index == 5):
            self.loptim = parameter
            return 1
        if (index == 6):
            self.delt = parameter
            return 1
        if (index == 7):
            self.tcon0 = parameter
            return 1
        if (index == 8):
            self.nfp = parameter
            return 1
        if (index == 9):
            self.ncurr = parameter
            return 1
        if (index == 10):
            self.mpol = parameter
            return 1
        if (index == 11):
            self.ntor = parameter
            return 1
        if (index == 12):
            self.nzeta = parameter
            return 1
        if (index >= 13 and index < 43):
            if ((index - 13) >= len(self.ns)):
                self.ns.append(parameter)
            else:
                self.ns[index - 13] = parameter
            return 1
        if (index == 43):
            self.niter = parameter
            return 1
        if (index == 44):
            self.nstep = parameter
            return 1
        if (index == 45):
            self.nvacskip = parameter
            return 1
        if (index == 46):
            self.gamma = parameter
            return 1
        if (index >= 47 and index <= 51):
            if ((index - 47) >= len(self.ftol)):
                self.ftol.append(parameter)
            else:
                self.ftol[index - 47] = parameter
            return 1
        if (index == 52):
            self.phiedge = parameter
            return 1
        if (index == 53):
            self.bloat = parameter
            return 1
        if (index >= 54 and index <= 58):
            if ((index - 54) >= len(self.extcur)):
                self.extcur.append(parameter)
            else:
                self.extcur[index - 54] = parameter
            return 1
        if (index == 59):
            self.curtor = parameter
            return 1
        if (index == 60):
            self.spres_ped = parameter
            return 1
        if (index == 61):
            self.pres_scale = parameter
            return 1
        if (index == 62):
            self.pres = parameter
            return 1
        if (index >= 63 and index <= 82):
            if ((index - 63) >= len(self.am)):
                self.am.append(parameter)
            else:
                self.am[index - 63] = parameter
            return 1
        if (index==83):
            self.piota = parameter
            return 1
        if (index >= 84 and index <= 104):
            if ((index - 84) >= len(self.ai)):
                self.ai.append(parameter)
            else:
                self.ai[index - 84] = parameter
            return 1
        if (index==105):
            self.pcurr = parameter
            return 1
        if (index >= 106 and index <= 128):
            if ((index - 106) >= len(self.ac)):
                self.ac.append(parameter)
            else:
                self.ac[index - 106] = parameter
            return 1
        if (index >= 129 and index <= 139):
            if ((index - 129) >= len(self.raxis)):
                self.raxis.append(parameter)
            else:
                self.raxis[index - 129] = parameter
            return 1
        if (index >= 140 and index <= 150):
            if ((index - 140) >= len(self.zaxis)):
                self.zaxis.append(parameter)
            else:
                self.zaxis[index - 140] = parameter
            return 1
        if (index >= 151 and index <= 624):
            pos = int(math.floor((index - 151) / 2))
            if (index % 2 == 0):
                if (pos >= len(self.rbc)):
                    self.rbc.append(parameter)
                else:
                    self.rbc[pos] = parameter
            else:
                if (pos >= len(self.zbc)):
                    self.zbc.append(parameter)
                else:
                    self.zbc[pos] = parameter
            return 1
        if (index == 625):
            self.epsfcn = parameter
            return 1
        if (index == 626):
            self.niter_opt = parameter
            return 1
        if (index == 627):
            self.lreset_opt = parameter
            return 1
        if (index == 628):
            self.lprof_opt = parameter
            return 1
        if (index == 629):
            self.lbmn = parameter
            return 1
        if (index == 630):
            self.lfix_ntor = parameter
            return 1
        if (index == 631):
            self.lsurf_mask = parameter
            return 1
        if (index == 632):
            self.target_aspectratio = parameter
            return 1
        if (index == 633):
            self.target_beta = parameter
            return 1
        if (index == 634):
            self.target_maxcurrent = parameter
            return 1
        if (index == 635):
            self.target_rmax = parameter
            return 1
        if (index == 636):
            self.target_rmin = parameter
            return 1
        if (index >= 637 and index <= 647):
            if ((index - 637) >= len(self.target_iota)):
                self.target_iota.append(parameter)
            else:
                self.target_iota[index - 637] = parameter
            return 1
        if (index >= 648 and index <= 658):
            if ((index - 648) >= len(self.target_well)):
                self.target_well.append(parameter)
            else:
                self.target_well[index - 648] = parameter
            return 1
        if (index == 659):
            self.sigma_aspect = parameter
            return 1
        if (index == 660):
            self.sigma_curv = parameter
            return 1
        if (index == 661):
            self.sigma_beta = parameter
            return 1
        if (index == 662):
            self.sigma_kink = parameter
            return 1
        if (index == 663):
            self.sigma_maxcurrent = parameter
            return 1
        if (index == 664):
            self.sigma_rmax = parameter
            return 1
        if (index == 665):
            self.sigma_rmin = parameter
            return 1
        if (index >= 666 and index <= 696):
            if ((index - 666) >= len(self.sigma_iota)):
                self.sigma_iota.append(parameter)
            else:
                self.sigma_iota[index - 666] = parameter
            return 1
        if (index >= 697 and index <= 727):
            if ((index - 697) >= len(self.sigma_vp)):
                self.sigma_vp.append(parameter)
            else:
                self.sigma_vp[index - 697] = parameter
            return 1
        if (index >= 728 and index <= 758):
            if ((index - 728) >= len(self.sigma_bmin)):
                self.sigma_bmin.append(parameter)
            else:
                self.sigma_bmin[index - 728] = parameter
            return 1
        if (index >= 759 and index <= 789):
            if ((index - 759) >= len(self.sigma_bmax)):
                self.sigma_bmax.append(parameter)
            else:
                self.sigma_bmax[index - 759] = parameter
            return 1
        if (index >= 790 and index <= 820):
            if ((index - 790) >= len(self.sigma_ripple)):
                self.sigma_ripple.append(parameter)
            else:
                self.sigma_ripple[index - 790] = parameter
            return 1
        if (index >= 821 and index <= 851):
            if ((index - 821) >= len(self.sigma_jstar0)):
                self.sigma_jstar0.append(parameter)
            else:
                self.sigma_jstar0[index - 821] = parameter
            return 1
        if (index >= 852 and index <= 882):
            if ((index - 852) >= len(self.sigma_jstar1)):
                self.sigma_jstar1.append(parameter)
            else:
                self.sigma_jstar1[index - 852] = parameter
            return 1
        if (index >= 883 and index <= 913):
            if ((index - 883) >= len(self.sigma_jstar2)):
                self.sigma_jstar2.append(parameter)
            else:
                self.sigma_jstar2[index - 883] = parameter
            return 1
        if (index >= 914 and index <= 944):
            if ((index - 914) >= len(self.sigma_jstar3)):
                self.sigma_jstar3.append(parameter)
            else:
                self.sigma_jstar3[index - 914] = parameter
            return 1
        if (index >= 945 and index <= 975):
            if ((index - 945) >= len(self.sigma_balloon)):
                self.sigma_balloon.append(parameter)
            else:
                self.sigma_balloon[index - 945] = parameter
            return 1
        if (index >= 976 and index <= 1006):
            if ((index - 976) >= len(self.sigma_pgrad)):
                self.sigma_pgrad.append(parameter)
            else:
                self.sigma_pgrad[index - 976] = parameter
            return 1
        if (index == 1007):
            self.sigma_pedge = parameter
            return 1
        if (index == 1008):
            self.lballon_test = parameter
            return 1
        if (index == 1009):
            self.bal_zeta0 = parameter
            return 1
        if (index == 1010):
            self.bal_theta0 = parameter
            return 1
        if (index == 1011):
            self.bal_xmax = parameter
            return 1
        if (index == 1012):
            self.bal_np0 = parameter
            return 1
        if (index == 1013):
            self.bal_kth = parameter
            return 1
        if (index == 1014):
            self.bal_x0 = parameter
            return 1
        if (index == 1015):
            self.nrh = parameter
            return 1
        if (index == 1016):
            self.mbuse = parameter
            return 1
        if (index == 1017):
            self.nbuse = parameter
            return 1
        if (index == 1018):
            self.zeff1 = parameter
            return 1
        if (index == 1019):
            self.damp = parameter
            return 1
        if (index == 1020):
            self.isymm0 = parameter
            return 1
        if (index == 1021):
            self.ate = parameter
            return 1
        if (index == 1022):
            self.ati = parameter
            return 1
        u.logger.warning("Unassigned element with index: " + str(index))
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
                            self.__show_indata = False
                        if (namelists.localName == "optimum"):
                            self.__show_optimum = False
                        if (namelists.localName == "bootin"):
                            self.__show_bootin = False
                    for node in namelists.childNodes:
                        if node.nodeType == node.ELEMENT_NODE:
                            c = ParameterVMEC()
                            for node_param in node.childNodes:
                                if (node_param.nodeType == node_param.ELEMENT_NODE):
                                    if (node_param.localName == "display"):
                                        c.set_display(node_param.firstChild.data)
                                    if (node_param.localName == "fixed"):
                                        c.set_fixed(node_param.firstChild.data)
                                    if (node_param.localName == "type"):
                                        c.set_type(node_param.firstChild.data)
                                    if (node_param.localName == "value"):
                                        c.set_value(node_param.firstChild.data)
                                        try:
                                            x_index = node_param.attributes["x"].value
                                            c.set_x_index(x_index)
                                            y_index = node_param.attributes["y"].value
                                            c.set_y_index(y_index)
                                        except:
                                            pass
                                    if (node_param.localName == "min_value"):
                                        c.set_min_value(node_param.firstChild.data)
                                    if (node_param.localName == "max_value"):
                                        c.set_max_value(node_param.firstChild.data)
                                    if (node_param.localName == "index"):
                                        c.set_index(node_param.firstChild.data)
                                    if (node_param.localName == "name"):
                                        c.set_name(node_param.firstChild.data)
                                    if (node_param.localName == "gap"):
                                        c.set_gap(node_param.firstChild.data)
                            try:
                                self.assign_parameter(c)
                                if (c.to_be_modified()):
                                    self.__numParams += 1
                                    values = 1 + int(round((c.get_max_value() - c.get_min_value())
                                            / c.get_gap()))
                                    self.__maxRange = max(values, self.__maxRange)
                            except Exception, e:
                                traceback.print_tb(sys.exc_info()[2])
                                u.logger.warning("Problem calculating max range: " + str(e))
        except Exception, e:
            u.logger.error("VMECData (" + str(sys.exc_traceback.tb_lineno) + "). Problem reading input xml file: " + str(e))
            traceback.print_tb(sys.exc_info()[2])
            sys.exit(111)
        return

    """
    Writes the /indata section of VMEC's input file
    Argument:
      - fInput: file struct that will store the input
    """

    def __write_indata(self, fInput):
        try:
            fInput.write("&INDATA\n")
            fInput.write("  MGRID_FILE = " +
                            self.mgrid_file.get_value() + '\n')
            if (self.lfreeb.get_display()):
                if (self.lfreeb.get_value() == True):
                    fInput.write("  LFREEB = T\n")
                else:
                    fInput.write("  LFREEB = F\n")
            if (self.loldout.get_display()):
                if (self.loldout.get_value() == True):
                    fInput.write("  LOLDOUT = T\n")
                else:
                    fInput.write("  LOLDOUT = F\n")
            if (self.lwouttxt.get_display()):
                if (self.lwouttxt.get_value() == True):
                    fInput.write("  LWOUTTXT = T\n")
                else:
                    fInput.write("  LWOUTTXT = F\n")
            if (self.ldiagno.get_display()):
                if (self.ldiagno.get_value() == True):
                    fInput.write("  LDIAGNO = T\n")
                else:
                    fInput.write("  LDIAGNO = F\n")
            if (self.loptim.get_display()):
                if (self.loptim.get_value() == True):
                    fInput.write("  LOPTIM =  T\n")
                else:
                    fInput.write("  LOPTIM =  F\n")
            if (self.delt.get_display()):
                fInput.write("  DELT = " + str(self.delt.get_value()) + "\n")
            if (self.tcon0.get_display()):
                fInput.write("  TCON0 = " + str(self.tcon0.get_value()) + "\n")
            if (self.nfp.get_display()):
                fInput.write("  NFP = " + str(self.nfp.get_value()) + "\n")
            if (self.ncurr.get_display()):
                fInput.write("  NCURR = " + str(
                             int(self.ncurr.get_value())) + "\n")
            if (self.mpol.get_display() and self.ntor.get_display()):
                fInput.write("  MPOL = " + str(self.mpol.get_value()) +
                             "  NTOR = " + str(self.ntor.get_value()) + "\n")
            if (self.nzeta.get_display()):
                fInput.write("  NZETA = " + str(self.nzeta.get_value()) + "\n")
            if (self.ns[0].get_display()):
                temptxt = "  NS_ARRAY ="
                cont = 0
                for i in self.ns:
                    if (i.get_display()):
                        if (cont % 5 == 0 and cont > 0):
                            temptxt = temptxt + "\n"
                        cont = cont + 1
                        temptxt = temptxt + "  " + str(i.get_value())
                fInput.write(temptxt + "\n")
            if (self.niter.get_display()):
                fInput.write("  NITER = " + str(
                                           self.niter.get_value()) + "\n")
            if (self.nstep.get_display()):
                fInput.write("  NSTEP = " + str(
                                           self.nstep.get_value()) + "\n")
            if (self.nvacskip.get_display()):
                fInput.write("  NVACSKIP = " + str(
                                        self.nvacskip.get_value()) + "\n")
            if (self.gamma.get_display()):
                fInput.write("  GAMMA = " + str(
                                "%E" % float(self.gamma.get_value())) + "\n")

            if (self.ftol[0].get_display()):
                temptxt = "  FTOL_ARRAY = "
                for i in self.ftol:
                    if (i.get_display()):
                        temptxt = temptxt + "  " + str(
                                        "%E" % float(i.get_value()))
                fInput.write(temptxt + "\n")

            if (self.phiedge.get_display()):
                fInput.write("  PHIEDGE =" + str(
                                "%E" % float(self.phiedge.get_value())) + "\n")
            if (self.bloat.get_display()):
                fInput.write("  BLOAT =" + str(
                                "%E" % float(self.bloat.get_value())) + "\n")

            if (self.extcur[0].get_display()):
                temptxt = "  EXTCUR( 1) = "
                cont = 0
                for i in self.extcur:
                    if (i.get_display()):
                        if (cont % 5 == 0 and cont > 0):
                            temptxt = temptxt + "\n"
                    cont = cont + 1
                    temptxt = temptxt + "  " + str(
                              "%E" % float(i.get_value()))
                fInput.write(temptxt + "\n")

            if (self.curtor.get_display()):
                fInput.write("  CURTOR = " + str(
                                 self.curtor.get_value()) + "\n")
            if (self.spres_ped.get_display()):
                fInput.write("  SPRES_PED = " + str(
                    "%E" % float(self.spres_ped.get_value())) + "\n")
            if (self.pres_scale.get_display()):
                fInput.write("  PRES_SCALE = " + str(
                    "%E" % float(self.pres_scale.get_value())) + "\n")
            if (self.pmass.get_display()):
                fInput.write("  PMASS_TYPE = " + self.pmass.get_value() + "\n")
            display = False
            for i in self.am:
                if (i.get_display()):
                    display = True
                    break
            if (display):
                temptxt = "  AM = "
                cont = 0
                for i in self.am:
                    if (i.get_display()):
                        if (cont % 5 == 0 and cont > 0):
                            temptxt = temptxt + "\n"
                        cont = cont + 1
                        temptxt = temptxt + "  " + str(
                                  "%E" % float(i.get_value()))
                fInput.write(temptxt + "\n")
            if (self.piota.get_display()):
                fInput.write("  PIOTA_TYPE = " + self.piota.get_value() + "\n")
                            
            display = False
            for i in self.ai:
                if (i.get_display()):
                    display = True
                    break
            if (display):
                temptxt = "  AI = "
                cont = 0
                for i in self.ai:
                    if (i.get_display()):
                        if (cont % 5 == 0 and cont > 0):
                            temptxt = temptxt + "\n"
                        cont = cont + 1
                        temptxt = temptxt + "  " + str("%E" % float(i.get_value()))
                fInput.write(temptxt + "\n")
            if (self.pcurr.get_display()):
                fInput.write("  PCURR_TYPE = " + self.pcurr.get_value() + "\n")
                            
            display = False
            for i in self.ac:
                if (i.get_display()):
                    display = True
                    break
            if (display):
                temptxt = "  AC = "
                cont = 0
                for i in self.ac:
                    if (i.get_display()):
                        if (cont % 5 == 0 and cont > 0):
                            temptxt = temptxt + "\n"
                        cont = cont + 1
                        temptxt = temptxt + "  " + str("%E" % float(i.get_value()))
                fInput.write(temptxt + "\n")

            temptxt = "  RAXIS = "
            cont = 0
            for i in self.raxis:
                if (i.get_display()):
                    if cont > 0:
                        if (cont % 5 == 0):
                            temptxt = temptxt + "\n" + str("%E" % i.get_value())
                        else:
                            temptxt = temptxt + "\t" + str("%E" % i.get_value())
                    else:
                        temptxt = temptxt + str("%E" % i.get_value())
                    cont = cont + 1
            fInput.write(temptxt + "\n")

            temptxt = "  ZAXIS = "
            cont = 0
            for i in self.zaxis:
                if (i.get_display()):
                    if cont > 0:
                        if (cont % 5 == 0):
                            temptxt = temptxt + "\n" + str(
                            "%E" % i.get_value())
                        else:
                            temptxt = temptxt + "\t" + str(
                            "%E" % i.get_value())
                    else:
                        temptxt = temptxt + str("%E" % i.get_value())
                    cont = cont + 1
            fInput.write(temptxt + "\n")

            index = 0
            for i in self.rbc:
                j = self.zbc[index]
                index = index + 1
                if (i.get_display()):
                    temptxt = "  RBC("
                    if (i.get_x_index() > -10):
                        temptxt = temptxt + ' '
                    if (i.get_x_index() < 10) and (i.get_x_index() >= 0):
                        temptxt = temptxt + ' '
                    temptxt = temptxt + str(i.get_x_index()) + ',' + str(
                                i.get_y_index()) + ') =  '
                    if (float(i.get_value()) >= 0):
                        temptxt = temptxt + ' '
                    temptxt = temptxt + str(
                                "%.4E" % float(i.get_value())) + "     ZBS("
                    if (j.get_x_index() > -10):
                        temptxt = temptxt + ' '
                    if (j.get_x_index() < 10) and (j.get_x_index() >= 0):
                        temptxt = temptxt + ' '
                    temptxt = temptxt + str(j.get_x_index()) + ',' + str(
                              j.get_y_index()) + ') =  '
                    if (float(j.get_value()) >= 0):
                        temptxt = temptxt + ' '
                    temptxt = temptxt + str("%.4E" % float(j.get_value()))
                    fInput.write(temptxt + "\n")
            fInput.write('/\n')
        except Exception, e:
            u.logger.warning("Error writting indata:" +
                str(e) + " line: " + str(sys.exc_traceback.tb_lineno))
            sys.exit(111)
            pass
        return True

    """
    Writes the /optimum section of VMEC's input file
    Argument:
      - fInput: file struct that will store the input
    """

    def __write_optimum(self, fInput):
        try:
            fInput.write("\n/\n&OPTIMUM\n")
            if (self.epsfcn.get_display()):
                fInput.write("  EPSFCN = " + str("%E" %
                        float(self.epsfcn.get_value())) + "\n")
            if (self.niter_opt.get_display()):
                fInput.write("  NITER_OPT = " + str(int(
                        self.niter_opt.get_value())) + "\n")
            if (self.lreset_opt.get_display()):
                if (self.lreset_opt.get_value() == True):
                    fInput.write("  LRESET_OPT = T\n")
                else:
                    fInput.write("  LRESET_OPT = F\n")
            if (self.lprof_opt.get_display()):
                if (self.lprof_opt.get_value() == True):
                    fInput.write("  LPROF_OPT = T\n")
                else:
                    fInput.write("  LPROF_OPT = F\n")
            if (self.lbmn.get_display()):
                if (self.lbmn.get_value() == True):
                    fInput.write("  LBMN = T\n")
                else:
                    fInput.write("  LBMN = F\n")
            if (self.lfix_ntor.get_display()):
                fInput.write("  LFIX_NTOR = " + str(
                        self.lfix_ntor.get_value()) + "\n")

            if (self.lsurf_mask.get_display()):
                fInput.write("  LFIX_NTOR = " + str(
                        self.lsurf_mask.get_value()) + "\n")

            if (self.target_aspectratio.get_display()):
                fInput.write("  TARGET_ASPECTRATIO = " + str(
                        self.target_aspectratio.get_value()) + "\n")
            if (self.target_beta.get_display()):
                fInput.write("  TARGET_BETA = " + str("%.4E"
                        % float(self.target_beta.get_value())) + "\n")
            if (self.target_maxcurrent.get_display()):
                fInput.write("  TARGET_MAXCURRENT = " + str(
                        self.target_maxcurrent.get_value()) + "\n")
            if (self.target_rmax.get_display()):
                fInput.write("  TARGET_RMAX = " + str(
                        self.target_rmax.get_value()) + "\n")
            if (self.target_rmin.get_display()):
                fInput.write("  TARGET_RMIN = " + str(
                        self.target_rmin.get_value()) + "\n")

            temptxt = "  TARGET_IOTA = "
            cont = 0
            for i in self.target_iota:
                if (i.get_display()):
                    if (cont % 5 == 0 and cont > 0):
                        temptxt = temptxt + "\n"
                    temptxt = temptxt + str("%.4E" % float(i.get_value())) + " "
                    cont += 1
            fInput.write(temptxt + "\n")

            temptxt = "  TARGET_WELL = "
            cont = 0
            for i in self.target_well:
                if (i.get_display()):
                    if (cont % 5 == 0 and cont > 0):
                        temptxt = temptxt + "\n"
                    temptxt = temptxt + str("%.4E" % float(i.get_value())) + " "
                    cont += 1
            fInput.write(temptxt + "\n")

            if (self.sigma_aspect.get_display()):
                fInput.write("  SIGMA_ASPECT = " + str(
                self.sigma_aspect.get_value()) + "\n")
            if (self.sigma_curv.get_display()):
                fInput.write("  SIGMA_CURV = " + str(
                self.sigma_curv.get_value()) + "\n")
            if (self.sigma_beta.get_display()):
                fInput.write("  SIGMA_BETA = " + str(
                "%E" % float(self.sigma_beta.get_value())) + "\n")
            if (self.sigma_kink.get_display()):
                fInput.write("  SIGMA_KINK = " + str(
                "%E" % float(self.sigma_kink.get_value())) + "\n")
            if (self.sigma_maxcurrent.get_display()):
                fInput.write("  SIGMA_MAXCURRENT = " + str(
                "%E" % float(self.sigma_maxcurrent.get_value())) + "\n")
            if (self.sigma_rmax.get_display()):
                fInput.write("  SIGMA_RMAX = " + str(
                "%E" % float(self.sigma_rmax.get_value())) + "\n")
            if (self.sigma_rmin.get_display()):
                fInput.write("  SIGMA_RMIN = " + str(
                "%E" % float(self.sigma_rmin.get_value())) + "\n")

            temptxt = "  SIGMA_IOTA = "
            cont = 0
            for i in self.sigma_iota:
                if (i.get_display()):
                    if (cont % 5 == 0 and cont > 0):
                        temptxt = temptxt + "\n"
                    temptxt = temptxt + str("%.4E" % float(i.get_value())) + " "
                    cont += 1
            fInput.write(temptxt + "\n")

            temptxt = "  SIGMA_VP = "
            cont = 0
            for i in self.sigma_vp:
                if (i.get_display()):
                    if (cont % 5 == 0 and cont > 0):
                        temptxt = temptxt + "\n"
                    temptxt = temptxt + str("%.4E" % float(i.get_value())) + " "
                    cont += 1
            fInput.write(temptxt + "\n")

            temptxt = "  SIGMA_BMIN = "
            cont = 0
            for i in self.sigma_bmin:
                if (i.get_display()):
                    if (cont % 5 == 0 and cont > 0):
                        temptxt = temptxt + "\n"
                    temptxt = temptxt + str("%.4E" % float(i.get_value())) + " "
                    cont += 1
            fInput.write(temptxt + "\n")

            temptxt = "  SIGMA_BMAX = "
            cont = 0
            for i in self.sigma_bmax:
                if (i.get_display()):
                    if (cont % 5 == 0 and cont > 0):
                        temptxt = temptxt + "\n"
                    temptxt = temptxt + str("%.4E" % float(i.get_value())) + " "
                    cont += 1
            fInput.write(temptxt + "\n")

            temptxt = "  SIGMA_RIPPLE = "
            cont = 0
            for i in self.sigma_ripple:
                if (i.get_display()):
                    if (cont % 5 == 0 and cont > 0):
                        temptxt = temptxt + "\n"
                    temptxt = temptxt + str("%.4E" % float(i.get_value())) + " "
                    cont += 1
            fInput.write(temptxt + "\n")

            cont = 0
            temptxt = ""
            fInput.write("  SIGMA_JSTAR(1,1) =\n")
            for i in self.sigma_jstar0:
                if (i.get_display()):
                    if (cont % 8 == 0 and cont > 0):
                        temptxt = temptxt + "\n"
                    temptxt = temptxt + str("%.3E" % float(i.get_value())) + " "
                    cont += 1
            fInput.write(temptxt + "\n")

            cont = 0
            temptxt = ""
            fInput.write("  SIGMA_JSTAR(1,2) =\n")
            for i in self.sigma_jstar1:
                if (i.get_display()):
                    if (cont % 8 == 0 and cont > 0):
                        temptxt = temptxt + "\n"
                    temptxt = temptxt + str("%.3E" % float(i.get_value())) + " "
                    cont += 1
            fInput.write(temptxt + "\n")

            cont = 0
            temptxt = ""
            fInput.write("  SIGMA_JSTAR(1,3) =\n")
            for i in self.sigma_jstar2:
                if (i.get_display()):
                    if (cont % 8 == 0 and cont > 0):
                        temptxt = temptxt + "\n"
                    temptxt = temptxt + str("%.3E" % float(i.get_value())) + " "
                    cont += 1
            fInput.write(temptxt + "\n")

            cont = 0
            temptxt = ""
            fInput.write("  SIGMA_JSTAR(1,4) =\n")
            for i in self.sigma_jstar3:
                if (i.get_display()):
                    if (cont % 8 == 0 and cont > 0):
                        temptxt = temptxt + "\n"
                    temptxt = temptxt + str("%.3E" % float(i.get_value())) + " "
                    cont += 1
            fInput.write(temptxt + "\n")

            fInput.write("  SIGMA_BALLOON  =\n")
            cont = 0
            temptxt = ""
            for i in self.sigma_balloon:
                if (i.get_display()):
                    if (cont % 8 == 0 and cont > 0):
                        temptxt = temptxt + "\n"
                    temptxt = temptxt + str("%.3E" % float(i.get_value())) + " "
                    cont += 1
            fInput.write(temptxt + "\n")

            fInput.write("  SIGMA_PGRAD  =\n")
            cont = 0
            temptxt = ""
            for i in self.sigma_pgrad:
                if (i.get_display()):
                    if (cont % 8 == 0 and cont > 0):
                        temptxt = temptxt + "\n"
                    temptxt = temptxt + str("%.3E" % float(i.get_value())) + " "
                    cont += 1
            fInput.write(temptxt + "\n")

            if (self.sigma_pedge.get_display()):
                fInput.write("  SIGMA_PEDGE = " + (str("%E" %
                        float(self.sigma_pedge.get_value())) + "\n"))
            if (self.lballon_test.get_display()):
                if (self.lballon_test.get_value() == True):
                    fInput.write("  LBALLOON_TEST = T\n")
                else:
                    fInput.write("  LBALLOON_TEST = F\n")
            if (self.bal_zeta0.get_display()):
                fInput.write("  BAL_ZETA0 = " + (str("%E" %
                        float(self.bal_zeta0.get_value())) + "\n"))
            if (self.bal_theta0.get_display()):
                fInput.write("  BAL_THETA0 = " + (str("%E" %
                        float(self.bal_theta0.get_value())) + "\n"))
            if (self.bal_xmax.get_display()):
                fInput.write("  BAL_XMAX = " + (str("%E" %
                        float(self.bal_xmax.get_value())) + "\n"))
            if (self.bal_np0.get_display()):
                fInput.write("  BAL_NP0 = " +
                        str(int(self.bal_np0.get_value())) + "\n")
            if (self.bal_kth.get_display()):
                fInput.write("  BAL_KTH = " +
                        str(int(self.bal_kth.get_value())) + "\n")
            if (self.bal_x0.get_display()):
                fInput.write("  BAL_X0 = " +
                        str("%E" % float(self.bal_x0.get_value())) + "\n")
        except Exception, e:
            u.logger.warning("Error writting optimum " +
                    str(e) + " line: " + str(sys.exc_traceback.tb_lineno))
            pass
        return True

    """
    Writes the /bootin section of VMEC's input file
    Argument:
      - fInput: file struct that will store the input
    """

    def __write_bootin(self, fInput):
        try:
            fInput.write("/\n&BOOTIN\n")
            if (self.nrh.get_display() and
                self.mbuse.get_display() and
                self.nbuse.get_display() and
                self.zeff1.get_display()):
                fInput.write("  NRHO=" + str(self.nrh.get_value()) +
                ", MBUSE=" + str(self.mbuse.get_value()) + ", NBUSE=" +
                str(self.nbuse.get_value()) + ", ZEFF1=" +
                str(self.zeff1.get_value()) + ", \n")

            if (self.damp.get_display() and
            self.isymm0.get_display() and
            self.ate.get_display()):
                fInput.write("  DAMP=" + str(self.damp.get_value()) +
                ", ISYMM0=" + str(self.isymm0.get_value()) + ", ATE=" +
                str(self.ate.get_value()) + "\n")

            if (self.ati.get_display()):
                fInput.write("  ATI=" + str(self.ati.get_value()) + "\n")
            fInput.write("/\n \n")
        except Exception, e:
            u.logger.warning("Error writting booting " + str(e) +
            " line: " + str(sys.exc_traceback.tb_lineno))
            pass
        return True

    """
    Main method for creating the input file
    """

    def create_input_file(self, filename):
        try:
            try:
                if (subProcFound):
                    subprocess.call(['touch', filename])
            except:
                pass
            fInput = open(filename, 'w')
            u.logger.debug("Slave " + str(u.rank) + " creating file " + filename)

            if (self.__show_indata):
                self.__write_indata(fInput)
            if (self.__show_optimum):
                self.__write_optimum(fInput)
            if (self.__show_bootin):
                self.__write_bootin(fInput)
            fInput.close()
        except Exception, e:
            u.logger.warning("When creating input file (" + str(u.rank) + "): " + str(e))
            return False
        return True
