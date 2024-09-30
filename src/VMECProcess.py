#!/usr/bin/env python
# vim: set fileencoding=utf-8 :

#############################################################################
#    Copyright 2013  by Antonio Gomez and Miguel Cardenas                   #
#                                                                           #
#   Licensed under the Apache License, Version 2.0(the "License");         #
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

__author__ = ' AUTHORS:     Antonio Gomez(antonio.gomez@csiro.au)'


__version__ = ' REVISION:   1.1  - 09-01-2015'

"""
HISTORY
    Version 0.1(12-04-2013):   Creation of the file.
    Version 1.0(15-01-2014):   Fist stable version.
    Version 1.1(09-01-2015):   Using numpy and new function.
"""
import math
import string
import Utils as u
import configparser
import os
import shutil
import sys
import time
import glob
import subprocess

import numpy as np


class VMECProcess(object):
    """
    This class interacts with VMEC.
    It is responsible for callling VMEC and analising its result.
    """

    def __init__(self, cfile):
        try:
            self.__currentPath = os.getcwd()
            self.__rank = str(u.rank)

            self.__execPath = self.__currentPath + '/' + self.__rank
            self.__filename = "input.tj" + str(u.rank)

            self.__beta = -u.infinity
            self.__bgradbval = -u.infinity
            self.__bootstrap = u.infinity
            self.__is_mercier_stable = True
            self.__is_ballooning_stable = True

            self.__dkes = False
            self.__extra_threed1 = False
            self.__check_mercier = False
            self.__min_mercier_radius = 0.8
            self.__bgradb = False
            self.__check_ballooning = False
            self.__get_beta = False
            self.__min_beta = -u.infinity
            self.__max_beta = u.infinity
            self.__save_configs = False

            self.__netcdf = ""

            #read the configuration from the INI file
            self.read_ini_config_file(cfile)

            #Create a symbolic link for the executable files on the
            #folder where the worker is executed
            if(int(self.__rank) == 0):
                return
            if not os.path.exists(self.__rank):
                os.makedirs(self.__rank)
            if not os.path.exists(self.__rank + "/finished"):
                os.makedirs(self.__rank + "/finished")
            os.chdir(self.__execPath)
            try:
                if(self.__check_ballooning):
                    if(not os.path.lexists("xcobravmec")):
                        subprocess.call(["ln", "-s", "../../external/xcobravmec",
                                          "xcobravmec"])
                if(not os.path.lexists("xgrid") and
                   os.path.exists("../../external/xgrid")):
                    subprocess.call(["ln", "-s", "../../external/xgrid",
                                      "xgrid"])
                if(not os.path.lexists("xvmec2000")):
                    subprocess.call(["ln", "-s", "/home/fraguas/bin/xvmec2000nc",
                                      "xvmec2000"])
            except Exception as e:
                u.logger.error("VMECProcess(" +
                               str(sys.exc_info()[2].tb_lineno) +
                               "). " + str(e))

            else:
                try:
                    if(self.__check_ballooning):
                        if(not os.path.lexists("xcobravmec")):
                            process = subprocess.Popen(["ln", "-s",
                                                       "../../external/xcobravmec",
                                                       "xcobravmec"])
                    if(not os.path.lexists("xgrid")):
                        process = subprocess.Popen(["ln", "-s",
                                                   "../../external/xgrid", "xgrid"])
                    if(not os.path.lexists("xvmec2000")):
                        process = subprocess.Popen(["ln", "-s",
                                                   "/home/fraguas/bin/xvmec2000nc",
                                                   "xvmec2000"])
                except Exception as e:
                    u.logger.warning("VMECProcess(" +
                                    str(sys.exc_info()[2].tb_lineno) + "). " +
                                    str(e))
                    process = subprocess.Popen(["ln", "-s",
                                               "/home/fraguas/bin/xvmec2000nc",
                                               "xvmec2000"])
                    process = subprocess.Popen(["ln", "-s",
                                               "../../external/xgrid", "xgrid"])
        except Exception as e:
            u.logger.error("VMECProcess(" + str(sys.exc_info()[2].tb_lineno) +
                           ") " + str(e))
        os.chdir(self.__currentPath)

    def get_beta(self):
        return self.__beta

    def get_bgradbval(self):
        return self.__bgradbval

    def read_ini_config_file(self, cfile):
        config = configparser.ConfigParser()
        config.read(cfile)
        if(not config.has_section("Fusion")):
            return

        try:
            if(config.has_option("Fusion", "bgradb")):
                val = config.getboolean("Fusion", "bgradb")
                if(val != None):
                    self.__bgradb = val
            if(config.has_option("Fusion", "mercier")):
                val = config.getboolean("Fusion", "mercier")
                if(val != None):
                    self.__check_mercier = val
            if(config.has_option("Fusion", "min_mercier_radius")):
                val = config.get("Fusion", "min_mercier_radius")
                if(val != None):
                    self.__min_mercier_radius = float(val)
            if(config.has_option("Fusion", "ballooning")):
                val = config.getboolean("Fusion", "ballooning")
                if(val != None):
                    self.__check_ballooning = val
            if(config.has_option("Fusion", "threed1")):
                val = config.getboolean("Fusion", "threed1")
                if(val != None):
                    self.__extra_threed1 = val
            if(config.has_option("Fusion", "get_beta")):
                val = config.getboolean("Fusion", "get_beta")
                if(val != None):
                    self.__get_beta = val
            if(config.has_option("Fusion", "min_beta")):
                val = config.get("Fusion", "min_beta")
                if(val != None):
                    self.__min_beta = float(val)
            if(config.has_option("Fusion", "max_beta")):
                val = config.get("Fusion", "max_beta")
                if(val != None):
                    self.__max_beta = float(val)
            if(config.has_option("Fusion", "dkes")):
                val = config.getboolean("Fusion", "dkes")
                if(val != None):
                    self.__dkes = val
            if(config.has_option("Fusion", "save_configurations")):
                val = config.getboolean("Fusion", "save_configurations")
                if(val != None):
                    self.__save_configs = val
            if(config.has_option("General", "netcdf")):
                val = config.get("General", "netcdf")
                if(val != None):
                    self.__netcdf = val
            u.logger.debug("bgradb " + str(self.__bgradb) + " - mercier " +
                            str(self.__check_mercier) + " - min_radius " +
                            str(self.__min_mercier_radius) + " - ballooning " +
                            str(self.__check_ballooning) + " - threed1 " +
                            str(self.__extra_threed1) + " - beta " +
                            str(self.__get_beta))
        except Exception as e:
            u.logger.error("VMECProcess(" + str(sys.exc_info()[2].tb_lineno) +
                           "). " + str(e))

    """
    This method just calls to the solution.prepare function
    to write the input file
    """

    def create_input_file(self, solution):
        u.logger.debug("Creating input file")
        try:
            if(os.path.exists("input.tj" + self.__rank)):
                os.remove("input.tj" + self.__rank)
        except:
            pass
        solution.prepare(self.__rank + "/" + self.__filename)
        return

    def clean_folder(self):
        try:
            if(os.path.exists("threed1.tj" + self.__rank)):
                os.remove("threed1.tj" + self.__rank)
            if(os.path.exists("wout_tj" + self.__rank + ".txt")):
                os.remove("wout_tj" + self.__rank + ".txt")
            if(os.path.exists("wout.flx")):
                os.remove("wout.flx")
            if(os.path.exists("wout.txt")):
                os.remove("wout.txt")
            if(os.path.exists("mercier.tj" + self.__rank)):
                os.remove("mercier.tj" + self.__rank)
            if(os.path.exists("jxbout.tj" + self.__rank)):
                os.remove("jxbout.tj" + self.__rank)
            if(os.path.exists("fort.9")):
                os.remove("fort.9")
        except Exception as e:
            u.logger.error("VMECProcess(" + str(sys.exc_info()[2].tb_lineno) +
                           "). " + str(e))

    """
    Main method of this class. It is responsible for calling the different
    executable files.
    Depending on the configuration specified in the ini file, the methods will
    or won't call the precompiled executables
    """

    def execute_configuration(self):
        #move to the execution folder of this process
        os.chdir(self.__execPath)
        self.clean_folder()

        if(u.objective == u.objectiveType.MINIMIZE):
            val = u.infinity
        else:
            val = -u.infinity
        try:
            if(not self.run_vmec()):
                os.chdir(self.__currentPath)
                if (u.objective == u.objectiveType.MAXIMIZE):
                    return -u.infinity
                return u.infinity

            if(not self.run_mercier()):
                os.chdir(self.__currentPath)
                if (u.objective == u.objectiveType.MAXIMIZE):
                    return -u.infinity
                return u.infinity

            if(not self.run_threed()):
                os.chdir(self.__currentPath)
                if (u.objective == u.objectiveType.MAXIMIZE):
                    return -u.infinity
                return u.infinity
            else:
                val = self.__beta

            if(not self.run_ballooning()):
                os.chdir(self.__currentPath)
                if (u.objective == u.objectiveType.MAXIMIZE):
                    return -u.infinity
                return u.infinity


            if(self.__bgradb):
                if(not self.run_b_grad_b()):
                    os.chdir(self.__currentPath)
                    if (u.objective == u.objectiveType.MAXIMIZE):
                        return -u.infinity
                    return u.infinity
                else:
                    val = self.__bgradbval

            if(self.__dkes):
                if(not self.run_dkes()):
                    os.chdir(self.__currentPath)
                    if (u.objective == u.objectiveType.MAXIMIZE):
                        return -u.infinity
                    return u.infinity
                else:
                    val = self.__bootstrap

            if(not self.__is_mercier_stable):
                u.logger.info("Unstable mercier")
                if (u.objective == u.objectiveType.MAXIMIZE):
                    return -u.infinity
                return u.infinity
            self.save_configuration()
            u.logger.info("VALID configuration(" + self.__rank + "). Val: " +
                           str(val))

        except Exception as e:
            os.chdir(self.__currentPath)
            u.logger.error("VMECProcess(" + str(sys.exc_info()[2].tb_lineno) +
                            "). Error when executing the configuration. " +
                            str(e))
            return val
        #Always restore the working directory to the original path
        os.chdir(self.__currentPath)
        return val

    def save_configuration(self):
        try:
            if(not self.__save_configs):
                return
            filenametime = time.strftime("%Y%m%d-%H%M%S", time.localtime())
            for fileIn in glob.glob('input*'):
                shutil.copyfile(fileIn, 'finished/input.' + filenametime)
            for fileThr in glob.glob('threed*'):
                shutil.copyfile(fileThr, 'finished/threed1.' + filenametime)
            for fileW in glob.glob('wout*'):
                shutil.copyfile(fileW, 'finished/wout.' + filenametime)
            for fileRes in glob.glob('OUTPUT/results*'):
                try:
                    shutil.copyfile(fileRes, 'finished/' + fileRes + "." +
                                    filenametime)
                except:
                    pass
        except Exception as e:
            u.logger.error("VMECProcess(" + str(sys.exc_info()[2].tb_lineno) +
                            "). Error when saving the configuration. " +
                            str(e))

    """
    Method that processes the output file created by vmec.
    Argument:
        - filepath: path to the wout file created by vmec
        - filepath_out: path to the file that will store the
          processed output in a way that can be then used to calculate the
          fitness value
    """

    def process_wout(self, filepath, filepath_out):
        try:
            file_wout = open(filepath, 'r')
            for i in range(0, 4):
                file_wout.readline()
            line = file_wout.readline()
            parts = line.split()
#            parts = map(string.strip, string.split(line))

            ns = int(parts[1].strip())
            nmax = int(parts[4].strip())

            u.logger.debug("NS " + parts[1] + " NMAX " + parts[4])

            file_wout.readline()
            file_wout.readline()
            file_wout.readline()

            m = np.zeros(nmax, dtype=np.int)
            n = np.zeros(nmax, dtype=np.int)

            rmn = u.Matrix(ns, nmax)
            zmn = u.Matrix(ns, nmax)
            bmn = u.Matrix(ns, nmax)

            iotas = []
            phi = np.zeros(ns)
            rho = np.zeros(ns)

            for i in range(0, ns):
                for j in range(0, nmax):
                    if(i == 0):
                        line = file_wout.readline()
                        parts = line.split()
                        m[j] = int(parts[0].strip())
                        n[j] = int(parts[1].strip())
                        u.logger.debug("m " + parts[0] + " n " + parts[1])

                    line = file_wout.readline()
                    parts = line.split()
#                    parts = map(string.strip, string.split(line))

                    rmn.setitem(j, i, float(parts[0].strip()))
                    zmn.setitem(j, i, float(parts[1].strip()))
                for j in range(0, nmax):
                    if(i == 0):
                        line = file_wout.readline()
#                        parts = map(string.strip, string.split(line))
                        parts = line.split()
                        u.logger.debug("m " + parts[0] + " n " + parts[1])
                    line = file_wout.readline()
                    parts = line.split()
#                    parts = map(string.strip, string.split(line))
                    bmn.setitem(j, i, float(parts[0]))
                    file_wout.readline()
                    file_wout.readline()

            for i in range(0, ns):
                line = file_wout.readline()
#                parts = map(string.strip, string.split(line))
                parts = line.split()
                iotas.append(float(parts[0]))
                file_wout.readline()
                line = file_wout.readline()
                parts = line.split()
#                parts = map(string.strip, string.split(line))
                phi[i] = float(parts[1])
                rho[i] = math.sqrt(abs(phi[i]))
                file_wout.readline()
                file_wout.readline()

            file_wout.close()

            file_out = open(filepath_out, 'w')
            file_out.write('Br, Bphi, Bz, dBr, dBphi, dBz , rho\n')

            delta = 0.000001
            #for i in range(0, ns, 10):
            for i in range(0, ns, 20):
                u.logger.debug('Surface: ' + str(i) + '\n')
                file_out.write('Surface: ' + str(i) + '\n')
                #for phi in range(0, 90):
                #    for epsilon in range(0, 90):
                for phi in range(0, 90, 2):
                    for epsilon in range(0, 90, 2):
                        Z = 0.0
                        R = 0.0
                        BR = 0.0
                        BZ = 0.0
                        BPHI = 0.0
                        dBR = 0.0
                        dBZ = 0.0
                        dBphi = 0.0
                        for j in range(0, nmax):
                            R = R + rmn.getitem(j, i) * math.cos(
                                m[j] * phi * 4 - n[j] * epsilon * 4)
                            Z = Z + zmn.getitem(j, i) * math.sin(
                                m[j] * phi * 4 - n[j] * epsilon * 4)
                            BR = BR + bmn.getitem(j, i) * math.cos(
                                m[j] * phi * 4 - n[j] * epsilon * 4)
                            BZ = BZ + bmn.getitem(j, i) * math.sin(
                                m[j] * phi * 4 - n[j] * epsilon * 4)
                            BPHI = BPHI + bmn.getitem(j, i) * math.cos(
                                m[j] * phi * 4 - n[j] * epsilon * 4)
                            dBR = BR + ((delta + bmn.getitem(j, i)) *
                                  math.cos(m[j] * phi * 4 - n[j] *
                                  epsilon * 4))
                            dBZ = BZ + ((delta + bmn.getitem(j, i)) *
                                  math.sin(m[j] * phi * 4 - n[j] *
                                  epsilon * 4))
                            dBphi = BPHI + ((delta + bmn.getitem(j, i)) *
                                    math.cos(m[j] * phi * 4 - n[j] *
                                    epsilon * 4))

                            file_out.write(str('%e' % BR) + ', ' + str(
                            '%e' % BPHI) + ', ' + str('%e' % BZ) + ', ' + str(
                            '%e' % dBR) + ', ' + str('%e' % dBphi) + ', ' +
                            str('%e' % dBZ) + ', ' + str('%e' % rho[i]) + '\n')

            file_out.close()
            return True
        except Exception as e:
            u.logger.error("VMECProcess(" + str(sys.exc_info()[2].tb_lineno) +
                           "). Unexpected error reading wout. " + str(e))
            return False
    """
    Calculate the fitness value for the BxgradB.
    Argument:
        - filepath: It needs an input file with the data postprocessed
       (coming from wout)
    """

    def calculate_fitness_bgradb(self, filepath):
        fitness = 0.0 #-u.infinity
        try:
            file_out = open(filepath, 'r')
            file_out.readline()
            lineRPhiZ = file_out.readline()
            while(len(lineRPhiZ) > 4):
                if(lineRPhiZ.find("Surface") != -1):
                    lineRPhiZ = file_out.readline()
                    continue
                parts = lineRPhiZ.split(',').strip()
#                parts = map(string.strip, string.split(lineRPhiZ, ','))
                Br = float(parts[0])
                Bphi = float(parts[1])
                Bz = float(parts[2])
                dBr = float(parts[3])
                dBphi = float(parts[4])
                dBz = float(parts[5])
                rho = float(parts[6])
                if(Br != 0.0) or (Bz != 0.0) or (Bphi != 0.0):
                    divisor = (Br ** 3 + Bz ** 3 + Bphi ** 3)
                    if(divisor == 0.0):
                        continue
                    tempBr = (Br * dBr) / divisor
                    tempBz = (Bz * dBz) / divisor
                    tempBphi = (Bphi * dBphi) / divisor
                    temp = abs(math.sqrt(
                        abs(tempBr ** 2 + tempBz ** 2 + tempBphi ** 2)))
                    fitness = fitness + temp
                lineRPhiZ = file_out.readline()
            file_out.close()
        except Exception as e:
            fitness = -u.infinity
            u.logger.error("VMECProcess(" + str(sys.exc_info()[2].tb_lineno) +
                           "). Error when calculating the fitness " + str(e))
            try:
                file_out.close()
            except:
                pass
            pass
        if(fitness < 1.0e+2):
            fitness = -u.infinity
        return fitness

    """
    Runs the dkes
    """

    def run_dkes(self):
        if(not self.__dkes):
            return True
        try:
            try:
                os.remove("EXE")
            except:
                pass
            try:
                os.remove("INPUT")
            except:
                pass
            try:
                os.remove("OUTPUT")
            except:
                pass
            try:
                os.remove ("s_*")
            except:
                pass
            os.environ["LD_LIBRARY_PATH"] = (os.environ["LD_LIBRARY_PATH"] +
                                             ":" + str(self.__netcdf))
            subprocess.call(["cp", "-rf", "../../external/DKES", "."])
            subprocess.call(["cp", "-f", "wout*", "INPUT/wout_DAB_0.0.txt"])
            subprocess.call(["cp", "-f", "threed1*", "INPUT/threed1.DAB_0.0"])
            outDKES = ""
            outPost = ""

            process = subprocess.Popen(["./EXE/dab.sh"], stdout=subprocess.PIPE)
            outDKES = process.communicate()[0]

            process = subprocess.Popen(["./EXE/recoge_res.sh"], stdout=subprocess.PIPE)
            outPost = process.communicate()[0]

            u.logger.info(outDKES)
            u.logger.info(outPost)

            if(not os.path.exists("OUTPUT/results.av")):
                u.logger.info("(" + self.__rank +
                              ") results.av does not exist")
                return False
            try:
                lines = [line.strip() for line in open("OUTPUT/results.av")]
                sum = 0.0
                for l in lines:
                    if (l.find('average')>0):
                        parts = l.split()
#                        parts = map(string.strip, string.split(l))
                        try:
                            d31 = abs(float(parts[4]))
                            rho = math.sqrt(float(parts[0]))
                            sum += d31*rho
                        except:
                            self.__bootstrap = u.infinity
                            return False
                self.__bootstrap = sum
            except:
                return False
            #last = u.Tail("OUTPUT/results.av")
            #parts = map(string.strip, string.split(last))
            #if(len(parts) < 3):
            #    u.logger.info("VMECProcess. Invalid number of values " +
            #                  " in the results file")
            #    return False
            #self.__bootstrap = abs(float(parts[4]))
            try:
                u.logger.info("(" + self.__rank + ") DKES VALUE: " +
                              str(self.__bootstrap))
            except:
                pass

            return True
        except Exception as e:
            u.logger.error("VMECProcess(" + str(sys.exc_info()[2].tb_lineno) +
                            "). Error when running DKES. " + str(e))
            return False

    """
    Runs the bgradb program
    """

    def run_b_grad_b(self):
        if(not self.__bgradb):
            return True
        try:
            if(not os.path.exists("wout_tj" + self.__rank + ".txt")):
                return False
            if(not self.process_wout("wout_tj" + self.__rank + ".txt",
                                     "wout_post.txt")):
                return False
            self.__bgradbval = self.calculate_fitness_bgradb("wout_post.txt")
            u.logger.info("WORKER(" + self.__rank + "). The BxgradB value is " +
                          str(self.__bgradbval))
            if(os.path.exists("wout_post.txt")):
                os.remove("wout_post.txt")
            return True
        except Exception as e:
            u.logger.error("VMECProcess(" + str(sys.exc_info()[2].tb_lineno) +
                            "). Error when transforming output to FLX format. "
                            + str(e))
            return False

    """
    Runs cobra and checks if ballooning is OK
    """

    def run_ballooning(self):
        if(not self.__check_ballooning):
            return True
        files = glob.glob('./wout*')
        for f in files:
            os.symlink(f, 'WOUT.tj' + self.__rank)
        shutil.copy2('../in_cobra_empty', 'in_cobra_tj' + self.__rank)
        subprocess.call(["sed", "-i", "'s/___/wout_tj" + self.__rank +
                         ".txt/g'", "in_cobra_tj" + self.__rank])
        subprocess.call(["./xcobravmec", "in_cobra_tj" + self.__rank])
        try:
            file_cobra = open('./cobra_grate.' + self.__rank, 'r')
            num_lines = len(file_cobra.readlines())
            first_line_to_analyze = num_lines + int(num_lines / 10)
            file_cobra.close()
            if(first_line_to_analyze == 0):
                return False
            file_cobra = open('./cobra_grate.' + self.__rank, 'r')
            i = 0
            self.__is_ballooning_stable = True
            for line in file_cobra.readlines():
                if(i >= first_line_to_analyze):
                    parts = line.split()
#                    parts = map(string.strip, string.split(line))
                    if(float(parts[2]) > 0):
                        self.__is_ballooning_stable = False
                        break
                i += 1
            file_cobra.close()
            if(self.__is_ballooning_stable):
                u.logger.info("WORKER(" + self.__rank +
                              "). Configuration ballooning stable")
            return self.__is_ballooning_stable
        except Exception as e:
            u.logger.error("VMECProcess(" + str(sys.exc_info()[2].tb_lineno) +
                            "). Error when processing ballooning. " + str(e))
            return False

    """
    Analyses the mercier
    """

    def run_mercier(self):
        if not self.__check_mercier:
            return True
        try:
            filename = "mercier.tj" + self.__rank
            if not os.path.exists(filename):
                u.logger.error("VMECProcess(" + self.__rank + "): File " +
                                str(filename) + " doesn't exist")
                return False
            f = open(filename, 'r')
            line = f.readline()
            while line.find('DMerc') == -1:
                line = f.readline()

            f.readline()
            line = f.readline()
            i = 0
            window_size = 0
            sign_change = False
            self.__is_mercier_stable = True
            while(line):
                linestrip = line.strip()
                new_line = linestrip.replace('  ', ' ')
                parts = new_line.split()
#                parts = map(string.strip, string.split(new_line, ' '))
                Si, DMerci, DSheari, DCurri, DWelli, Dgeodi = parts

                if(float(Si) >= self.__min_mercier_radius):
                    if(float(DMerci) > 0):
                        window_size = window_size + 1
                        if(sign_change):
                            if(window_size >= 5):
                                f.close()
                                #There is a sing change in mercier
                                self.__is_mercier_stable = False
                                return False
                        else:
                            sign_change = True
                            window_size = 1
                    else:
                        sign_change = False
                i += 1
                line = f.readline()
            f.close()
        except Exception as e:
            u.logger.error("VMECProcess(" + str(sys.exc_info()[2].tb_lineno) +
                            "). Error while processing mercier. " + str(e))
            self.__is_mercier_stable = False
            return False
        u.logger.info("WORKER(" + self.__rank +
                      "). Configuration mercier stable")
        self.__is_mercier_stable = True
        return True

    """
    Analyses the threed1 file

    """

    def extract_beta(self):
        try:
            self.__beta = -u.infinity
            if(not self.__get_beta):
                return True
            file_threed = open('./threed1.tj' + self.__rank, 'r')
            found = False
            for line in file_threed.readlines():
                if(line.find('beta total') != -1):
                    found = True
                    break
            file_threed.close()
            if(not found):
                return False
            parts = line.split('=')
#            parts = map(string.strip, string.split(line, '='))
            self.__beta = float(parts[1])
            u.logger.info("Worker " + self.__rank + ". Beta found " +
                           str(self.__beta))
            if(self.__beta > self.__max_beta):
                self.__beta = -u.infinity
                return False
            if(self.__beta <= self.__min_beta):
                self.__beta = -u.infinity
                return False
            return True
        except Exception as e:
            u.logger.error("VMECProcess(" + str(sys.exc_info()[2].tb_lineno) +
                            "). Error while processing beta. " + str(e))
            return True

    def run_threed(self):
        try:
            if(self.__get_beta):
                self.extract_beta()
            if(not self.__extra_threed1):
                return True

            file_threed = open('./threed1.tj' + self.__rank, 'r')
            cnt = 1
            for line in file_threed.readlines():
                line = line.replace(" ", "")
                if(line.find('FSQRFSQZFSQL') != -1):
                    cnt += 1
            file_threed.close()
            i = 0
            file_threed = open('threed1.tj' + self.__rank, 'r')
            while(i < cnt):
                line = file_threed.readline().replace(" ", "")
                if(line.find('FSQRFSQZFSQL') != -1):
                    i += 1
            line = file_threed.readline()
            line = file_threed.readline()
            while(len(line) > 10):
                old_line = line
                line = file_threed.readline()
            file_threed.close()

#            parts = map(string.strip, string.split(old_line))
            parts = old_line.split()

            fsqr = float(parts[1])
            fsqz = float(parts[2])
            fsql = float(parts[3])
            if(fsqr > 1.0e-10) or (fsqz > 1.0e-10) or (fsql > 1.0e-10):
                #Incorrect values for fsqr, fsqz o fsql
                return False
        except Exception as e:
            u.logger.error("VMECProcess(" + str(sys.exc_info()[2].tb_lineno) +
                            "). Error while processing threed1 file. " +
                            str(e))
            return False
        u.logger.info("WORKER(" + self.__rank + "). Configuration threed1 OK")
        return True

    """
    Run VMEC
    """

    def run_vmec(self):
        try:
            if(not os.path.exists("input.tj" + str(self.__rank))):
                return False
            proc = subprocess.Popen(["/home/fraguas/bin/xvmec2000nc", "tj" + self.__rank],
                                    stdout=subprocess.PIPE)
            output = proc.stdout.read()
            u.logger.debug(output)
            try:
                if(os.path.exists("core")):
                    os.remove("core")
            except:
                pass
            if(not os.path.exists('wout_tj' + self.__rank + '.txt')):
                u.logger.debug("VMECProcess(" + self.__rank +
                               "): Invalid configuration")
                return False
            last_line = u.Tail('wout_tj' + self.__rank + '.txt')
            if last_line.find('mgrid') != -1:
                # Invalid configuration
                return False
            filenameMercier = "mercier.tj" + self.__rank
            if(not os.path.exists(filenameMercier)):
                return False
            u.logger.info("WORKER(" + self.__rank + "). Configuration VMEC OK")
            return True
        except Exception as e:
            u.logger.error("VMECProcess(" + str(sys.exc_info()[2].tb_lineno) +
                            "). Error when running VMEC. " + str(e))
            return False

    """
    Checks if the xgrid code needs to be called
    """

    def run_x_grid(self):
        fullpath = self.__rank + "/" + self.__filename
        with open(fullpath, 'r') as fileinput:
            line = fileinput.readline()
            line = fileinput.readline()
            """
            Check if we have to run xgrid
            """
            runxgrid = True
            if(line.find('mgrid.') == -1):
                #In this case, running xgrid is not necessary
                return True

        if(runxgrid):
            if(not os.path.exists('../external/mgrid.tj0')):
                u.logger.error("File Mgrid.tj0 doesn't exist")
                return False

            shutil.copy2("../external/mgrid.tj0", "mgrid.tj" + self.__rank)
            if(not os.path.exists('mgrid.tj' + self.__rank)):
                try:
                    fcmd_xgrid = open('cmd_xgrid.tj' + self.__rank, 'w')
                    fcmd_xgrid.write('tj' + self.__rank + '\n')
                    fcmd_xgrid.write('y\n')
                    fcmd_xgrid.write('1.08\n')
                    fcmd_xgrid.write('1.92\n')
                    fcmd_xgrid.write('-0.42\n')
                    fcmd_xgrid.write('0.42\n')
                    fcmd_xgrid.write('64')
                    fcmd_xgrid.close()
                    if(not os.path.exists("../external/coils")):
                        u.logger.error("File coils doesn't exist")
                        return False
                    if(not os.path.exists('coils.tj' + self.__rank)):
                        shutil.copy2("../external/coils", "coils.tj" +
                                     self.__rank)
                    subprocess.call(["./xgrid", "< cmd_xgrid.tj" +
                                    self.__rank])
                    return True
                except:
                    u.logger.error("VMECProcess(" +
                                   str(sys.exc_info()[2].tb_lineno) +
                                   "). Error during the generation of " +
                                   "the matrix file")
                    return False
            return False
        return False
