#!/usr/bin/env python

import configparser
import glob
import math
import os
import random
import shutil
import subprocess
import time
from pathlib import Path

import numpy as np

from core.comms import GlobalComms
from core.enums import ObjectiveType
from core.file_utils import tail

# from core.matrix import Matrix
from core.runtime import GlobalRuntime

INFINITY = math.inf


class VMECProcess:
    """
    This class interacts with VMEC.
    It is responsible for callling VMEC and analising its result.
    """

    def __init__(self, runtime: GlobalRuntime, comms: GlobalComms) -> None:
        self._runtime = runtime
        self._comms = comms
        # self._probMatrix = probMatrix

        self._currentPath = os.getcwd()
        self._execPath = os.path.join(
            self._currentPath,
            str(self._comms.rank),
        )

        self._filename = f"input.tj{self._comms.rank}"

        self._beta = -INFINITY
        self._bgradbval = -INFINITY
        self._bootstrap = INFINITY

        self._is_mercier_stable = True
        self._is_ballooning_stable = True

        self._dkes = False
        self._extra_threed1 = False
        self._check_mercier = False
        self._min_mercier_radius = 0.8
        self._bgradb = False
        self._check_ballooning = False
        self._get_beta = False
        self._min_beta = -INFINITY
        self._max_beta = INFINITY
        self._save_configs = False

        self._netcdf = ""

        self.read_ini_config_file(self._runtime.config_file)

        if self._comms.rank == 0:
            return

        os.makedirs(self._execPath, exist_ok=True)
        os.makedirs(
            os.path.join(self._execPath, "finished"),
            exist_ok=True,
        )

        try:
            os.chdir(self._execPath)

            if self._check_ballooning and not os.path.lexists("xcobravmec"):
                os.symlink(
                    "../../external/xcobravmec",
                    "xcobravmec",
                )

            if not os.path.lexists("xgrid"):
                os.symlink(
                    "../../external/xgrid",
                    "xgrid",
                )

            if not os.path.lexists("xvmec2000"):
                os.symlink(
                    "/home/fraguas/bin/xvmec2000nc",
                    "xvmec2000",
                )
        finally:
            os.chdir(self._currentPath)

    def get_beta(self):
        return self._beta

    def get_bgradbval(self):
        return self._bgradbval

    def read_ini_config_file(self, cfile):
        config = configparser.ConfigParser()
        config.read(cfile)
        if not config.has_section("Fusion"):
            return

        try:
            if config.has_option("Fusion", "bgradb"):
                val = config.getboolean("Fusion", "bgradb")
                if val is not None:
                    self._bgradb = val
            if config.has_option("Fusion", "mercier"):
                val = config.getboolean("Fusion", "mercier")
                if val is not None:
                    self._check_mercier = val
            if config.has_option("Fusion", "min_mercier_radius"):
                val = config.get("Fusion", "min_mercier_radius")
                if val is not None:
                    self._min_mercier_radius = float(val)
            if config.has_option("Fusion", "ballooning"):
                val = config.getboolean("Fusion", "ballooning")
                if val is not None:
                    self._check_ballooning = val
            if config.has_option("Fusion", "threed1"):
                val = config.getboolean("Fusion", "threed1")
                if val is not None:
                    self._extra_threed1 = val
            if config.has_option("Fusion", "get_beta"):
                val = config.getboolean("Fusion", "get_beta")
                if val is not None:
                    self._get_beta = val
            if config.has_option("Fusion", "min_beta"):
                val = config.get("Fusion", "min_beta")
                if val is not None:
                    self._min_beta = float(val)
            if config.has_option("Fusion", "max_beta"):
                val = config.get("Fusion", "max_beta")
                if val is not None:
                    self._max_beta = float(val)
            if config.has_option("Fusion", "dkes"):
                val = config.getboolean("Fusion", "dkes")
                if val is not None:
                    self._dkes = val
            if config.has_option("Fusion", "save_configurations"):
                val = config.getboolean("Fusion", "save_configurations")
                if val is not None:
                    self._save_configs = val
            if config.has_option("General", "netcdf"):
                val = config.get("General", "netcdf")
                if val is not None:
                    self._netcdf = val
            self._runtime.logger.debug(
                "bgradb "
                + str(self._bgradb)
                + " - mercier "
                + str(self._check_mercier)
                + " - min_radius "
                + str(self._min_mercier_radius)
                + " - ballooning "
                + str(self._check_ballooning)
                + " - threed1 "
                + str(self._extra_threed1)
                + " - beta "
                + str(self._get_beta)
            )
        except Exception:
            self._runtime.logger.exception(
                "VMECProcess: error reading configuration file."
            )
            raise

    """
    This method just calls to the solution.prepare function
    to write the input file
    """

    def create_input_file(self, solution) -> bool:
        self._runtime.logger.debug("Creating input file")

        input_file = f"input.tj{self._comms.rank}"

        try:
            os.remove(input_file)
        except FileNotFoundError:
            pass
        except OSError:
            self._runtime.logger.exception("VMECProcess: error removing old input file")
            return False

        return solution.prepare(f"{self._comms.rank}/{self._filename}")

    def clean_folder(self):
        files = [
            f"threed1.tj{self._comms.rank}",
            f"wout_tj{self._comms.rank}.txt",
            "wout.flx",
            "wout.txt",
            f"mercier.tj{self._comms.rank}",
            f"jxbout.tj{self._comms.rank}",
            "fort.9",
        ]

        for name in files:
            try:
                Path(name).unlink(missing_ok=True)
            except OSError:
                self._runtime.logger.exception(f"Failed removing {name}")

    """
    Main method of this class. It is responsible for calling the different
    executable files.
    Depending on the configuration specified in the ini file, the methods will
    or won't call the precompiled executables
    """

    def execute_configuration(self) -> float:
        """
        Execute the current configuration and return its objective value.

        Returns:
            Objective value on success.
            +/-INFINITY on invalid configurations.
        """
        if self._runtime.mock:
            return random.uniform(0.0, 1.0)

        failure_value = (
            -INFINITY if self._runtime.objective == ObjectiveType.MAXIMIZE else INFINITY
        )

        value = failure_value

        try:
            os.chdir(self._execPath)
            self.clean_folder()

            if not self.run_vmec():
                return failure_value

            if not self.run_mercier():
                return failure_value

            if not self.run_threed():
                return failure_value

            value = self._beta

            if not self.run_ballooning():
                return failure_value

            if self._bgradb:
                if not self.run_b_grad_b():
                    return failure_value
                value = self._bgradbval

            if self._dkes:
                if not self.run_dkes():
                    return failure_value
                value = self._bootstrap

            if not self._is_mercier_stable:
                self._runtime.logger.info("Unstable mercier")
                return failure_value

            self.save_configuration()

            self._runtime.logger.info(
                f"VALID configuration({self._comms.rank}). Val: {value}"
            )

            return value

        except Exception:
            self._runtime.logger.exception("VMECProcess: error executing configuration")
            return failure_value

        finally:
            os.chdir(self._currentPath)

    def save_configuration(self):
        try:
            if not self._save_configs:
                return
            filenametime = time.strftime("%Y%m%d-%H%M%S", time.localtime())
            for fileIn in glob.glob("input*"):
                shutil.copyfile(fileIn, "finished/input." + filenametime)
            for fileThr in glob.glob("threed*"):
                shutil.copyfile(fileThr, "finished/threed1." + filenametime)
            for fileW in glob.glob("wout*"):
                shutil.copyfile(fileW, "finished/wout." + filenametime)
            for fileRes in glob.glob("OUTPUT/results*"):
                shutil.copyfile(fileRes, "finished/" + fileRes + "." + filenametime)
        except Exception:
            self._runtime.logger.exception("VMECProcess: error saving configuration")

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
            with open(filepath) as file_wout:
                # Skip the first 4 lines of the file
                for _ in range(0, 4):
                    file_wout.readline()
                parts = file_wout.readline().split()

                ns = int(parts[1])
                nmax = int(parts[4])

                self._runtime.logger.debug(f"NS {ns} NMAX {nmax}")

                # Skip the next 3 lines of the file
                for _ in range(0, 3):
                    file_wout.readline()

                m = np.zeros(nmax, dtype=int)
                n = np.zeros(nmax, dtype=int)

                iotas = []
                phi = np.zeros(ns)
                rho = np.zeros(ns)

                for i in range(0, ns):
                    for j in range(0, nmax):
                        if i == 0:
                            line = file_wout.readline()
                            parts = line.split()
                            m[j] = int(parts[0].strip())
                            n[j] = int(parts[1].strip())
                            self._runtime.logger.debug(f"m {parts[0]} n {parts[1]}")

                        line = file_wout.readline()
                        parts = line.split()

                        # self._probMatrix.setitem(j, i, float(parts[0].strip()))
                        # self._probMatrix.setitem(j, i, float(parts[1].strip()))
                    for j in range(0, nmax):
                        if i == 0:
                            line = file_wout.readline()
                            parts = line.split()
                            self._runtime.logger.debug(f"m {parts[0]} n {parts[1]}")
                        line = file_wout.readline()
                        parts = line.split()
                        # self._probMatrix.setitem(j, i, float(parts[0]))
                        file_wout.readline()
                        file_wout.readline()

                for surface_idx in range(ns):
                    iotas.append(float(file_wout.readline().split()[0]))

                    file_wout.readline()  # Skip line

                    phi[surface_idx] = float(file_wout.readline().split()[1])
                    rho[surface_idx] = math.sqrt(abs(phi[surface_idx]))

                    for _ in range(2):
                        file_wout.readline()

            with open(filepath_out, "w") as file_out:
                file_out.write("Br, Bphi, Bz, dBr, dBphi, dBz , rho\n")
                """
                delta = 0.000001
                for i in range(0, ns, 20):
                    self._runtime.logger.debug(f"Surface: {i}")
                    file_out.write(f"Surface: {i}\n")
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
                                angle = m[j] * phi * 4 - n[j] * epsilon * 4
                                c = math.cos(angle)
                                s = math.sin(angle)
                                R = R + self._probMatrix.getitem(j, i) * c
                                #R = R + rmn.getitem(j, i) * c
                                Z = Z + self._probMatrix.getitem(j, i) * s
                                #Z = Z + zmn.getitem(j, i) * s
                                BR = BR + self._probMatrix.getitem(j, i) * c
                                BZ = BZ + self._probMatrix.getitem(j, i) * s
                                BPHI = BPHI + self._probMatrix.getitem(j, i) * c
                                dBR = BR + ((delta + self._probMatrix.getitem(j, i)) * c)
                                dBZ = BZ + ((delta + self._probMatrix.getitem(j, i)) * s)
                                dBphi = BPHI + ((delta + self._probMatrix.getitem(j, i)) * c)

                                values = [BR, BPHI, BZ, dBR, dBphi, dBZ, rho[i]]
                                file_out.write(
                                    ", ".join(f"{v:e}" for v in values) + "\n"
                                )
                """
        except Exception:
            self._runtime.logger.exception("VMECProcess: error processing wout file.")
            return False
        return True

    """
    Calculate the fitness value for the BxgradB.
    Argument:
        - filepath: It needs an input file with the data postprocessed
       (coming from wout)
    """

    def calculate_fitness_bgradb(self, filepath):
        fitness = 0.0  # -INFINITY
        try:
            with open(filepath) as file_out:
                file_out.readline()
                lineRPhiZ = file_out.readline()
                while len(lineRPhiZ) > 4:
                    if lineRPhiZ.find("Surface") != -1:
                        lineRPhiZ = file_out.readline()
                        continue
                    parts = lineRPhiZ.split(",")
                    #                parts = map(string.strip, string.split(lineRPhiZ, ','))
                    Br = float(parts[0])
                    Bphi = float(parts[1])
                    Bz = float(parts[2])
                    dBr = float(parts[3])
                    dBphi = float(parts[4])
                    dBz = float(parts[5])
                    # rho = float(parts[6])
                    if Br != 0.0 or Bz != 0.0 or Bphi != 0.0:
                        divisor = Br**3 + Bz**3 + Bphi**3
                        if divisor == 0.0:
                            continue
                        tempBr = (Br * dBr) / divisor
                        tempBz = (Bz * dBz) / divisor
                        tempBphi = (Bphi * dBphi) / divisor
                        temp = abs(math.sqrt(abs(tempBr**2 + tempBz**2 + tempBphi**2)))
                        fitness = fitness + temp
                    lineRPhiZ = file_out.readline()
        except Exception:
            fitness = -INFINITY
            self._runtime.logger.exception(
                "VMECProcess. Error when calculating the fitness"
            )
            pass
        if fitness < 1.0e2:
            fitness = -INFINITY
        return fitness

    """
    Runs the dkes
    """

    def run_dkes(self):
        if not self._dkes:
            return True
        self._bootstrap = INFINITY
        folders = ["EXE", "INPUT", "OUTPUT", "s_*"]
        try:
            for folder in folders:
                for file in glob.glob(folder):
                    try:
                        if os.path.isfile(file) or os.path.islink(file):
                            os.unlink(file)
                        elif os.path.isdir(file):
                            shutil.rmtree(file)
                    except Exception:
                        self._runtime.logger.exception(
                            f"VMECProcess: error removing {file}."
                        )
            os.environ["LD_LIBRARY_PATH"] = (
                os.environ["LD_LIBRARY_PATH"] + ":" + str(self._netcdf)
            )
            subprocess.call(["cp", "-rf", "../../external/DKES", "."])
            subprocess.call(["cp", "-f", "wout*", "INPUT/wout_DAB_0.0.txt"])
            subprocess.call(["cp", "-f", "threed1*", "INPUT/threed1.DAB_0.0"])
            outDKES = ""
            outPost = ""

            process = subprocess.Popen(["./EXE/dab.sh"], stdout=subprocess.PIPE)
            outDKES = process.communicate()[0]

            process = subprocess.Popen(["./EXE/recoge_res.sh"], stdout=subprocess.PIPE)
            outPost = process.communicate()[0]

            self._runtime.logger.info(outDKES)
            self._runtime.logger.info(outPost)

            if not os.path.exists("OUTPUT/results.av"):
                self._runtime.logger.info(
                    f"({self._comms.rank}) results.av does not exist"
                )
                return False
            lines = [line.strip() for line in open("OUTPUT/results.av")]
            sum = 0.0
            total = 0.0

            for line in lines:
                if "average" in line:
                    parts = line.split()

                    if len(parts) >= 5:
                        d31 = abs(float(parts[4]))
                        rho = math.sqrt(float(parts[0]))
                        total += d31 * rho
            self._bootstrap = sum
            self._runtime.logger.info(
                f"({self._comms.rank}) DKES VALUE: {self._bootstrap}"
            )
        except Exception:
            self._runtime.logger.exception("VMECProcess: error running DKES.")
            return False
        return True

    """
    Runs the bgradb program
    """

    def run_b_grad_b(self):
        if not self._bgradb:
            return True
        try:
            if not os.path.exists(f"wout_tj{self._comms.rank}.txt"):
                return False
            if not self.process_wout(
                f"wout_tj{self._comms.rank}.txt", f"wout_post{self._comms.rank}.txt"
            ):
                return False
            self._bgradbval = self.calculate_fitness_bgradb(
                f"wout_post{self._comms.rank}.txt"
            )
            self._runtime.logger.info(
                f"({self._comms.rank}) The BxgradB value is {self._bgradbval}"
            )
            if os.path.exists(f"wout_post{self._comms.rank}.txt"):
                os.remove(f"wout_post{self._comms.rank}.txt")
            return True
        except Exception:
            self._runtime.logger.exception("VMECProcess: error running BxgradB.")
            return False

    """
    Runs cobra and checks if ballooning is OK
    """

    def _is_cobra_output_stable(self, filename: str) -> bool:
        """
        Analyze the cobra output file and determine whether the
        configuration is ballooning stable.

        Returns:
            True if stable, False otherwise.
        """
        lines = Path(filename).read_text().splitlines()

        if not lines:
            return False

        # Analyze only the last 10% of the file.
        start = len(lines) - max(1, len(lines) // 10)

        for line in lines[start:]:
            parts = line.split()

            if len(parts) < 3:
                continue

            try:
                if float(parts[2]) > 0:
                    return False
            except ValueError:
                continue

        return True

    def run_ballooning(self) -> bool:
        """
        Run the ballooning stability check.

        Returns:
            True if the configuration is ballooning stable.
            False otherwise.
        """
        if not self._check_ballooning:
            return True

        rank = self._comms.rank

        try:
            # Create symbolic links expected by xcobravmec.
            for wout_file in glob.glob("./wout*"):
                link_name = f"WOUT.tj{rank}"

                if not os.path.exists(link_name):
                    os.symlink(wout_file, link_name)

            cobra_input = f"in_cobra_tj{rank}"

            shutil.copy2("../in_cobra_empty", cobra_input)

            subprocess.run(
                [
                    "sed",
                    "-i",
                    f"s/___/wout_tj{rank}.txt/g",
                    cobra_input,
                ],
                check=True,
            )

            subprocess.run(
                ["./xcobravmec", cobra_input],
                check=True,
            )

            output_file = f"cobra_grate.{rank}"

            self._is_ballooning_stable = self._is_cobra_output_stable(output_file)

            if self._is_ballooning_stable:
                self._runtime.logger.info(
                    f"WORKER({rank}). Configuration ballooning stable"
                )

            return self._is_ballooning_stable

        except Exception:
            self._runtime.logger.exception("VMECProcess: error running ballooning.")
            return False

    """
    Analyses the mercier
    """

    def run_mercier(self):
        if not self._check_mercier:
            return True
        try:
            filename = f"mercier.tj{self._comms.rank}"
            if not os.path.exists(filename):
                self._runtime.logger.error(
                    f"VMECProcess({self._comms.rank}): File {filename} doesn't exist"
                )
                return False
            with open(filename) as f:
                line = f.readline()
                while line.find("DMerc") == -1:
                    line = f.readline()

                f.readline()
                line = f.readline()
                i = 0
                window_size = 0
                sign_change = False
                self._is_mercier_stable = True
                while line:
                    linestrip = line.strip()
                    new_line = linestrip.replace("  ", " ")
                    parts = new_line.split()
                    Si, DMerci, DSheari, DCurri, DWelli, Dgeodi = parts

                    if float(Si) >= self._min_mercier_radius:
                        if float(DMerci) > 0:
                            window_size = window_size + 1
                            if sign_change:
                                if window_size >= 5:
                                    # There is a sing change in mercier
                                    self._is_mercier_stable = False
                                    return False
                            else:
                                sign_change = True
                                window_size = 1
                        else:
                            sign_change = False
                    i += 1
                    line = f.readline()
        except Exception:
            self._runtime.logger.exception(
                "VMECProcess: error while processing mercier."
            )
            self._is_mercier_stable = False
            return False
        self._runtime.logger.info(
            f"WORKER({self._comms.rank}). Configuration mercier stable"
        )
        self._is_mercier_stable = True
        return True

    """
    Analyses the threed1 file

    """

    def extract_beta(self):
        try:
            self._beta = -INFINITY
            if not self._get_beta:
                return True
            with open(f"./threed1.tj{self._comms.rank}") as file_threed:
                found = False
                line = ""
                for line in file_threed.readlines():
                    if line.find("beta total") != -1:
                        found = True
                        break
            if not found:
                return False
            parts = line.split("=")
            self._beta = float(parts[1])
            self._runtime.logger.info(
                f"Worker {self._comms.rank}. Beta found {self._beta}"
            )
            if self._beta > self._max_beta:
                self._beta = -INFINITY
                return False
            if self._beta <= self._min_beta:
                self._beta = -INFINITY
                return False
            return True
        except Exception:
            self._runtime.logger.exception("VMECProcess: error while processing beta.")
            return True

    def run_threed(self):
        try:
            if self._get_beta:
                self.extract_beta()
            if not self._extra_threed1:
                return True

            marker = "FSQRFSQZFSQL"

            with open(f"./threed1.tj{self._comms.rank}") as file_threed:
                lines = file_threed.readlines()

            last_marker = -1

            for idx, line in enumerate(lines):
                if marker in line.replace(" ", ""):
                    last_marker = idx
            line_idx = last_marker + 3
            old_line = ""
            while line_idx < len(lines) and len(lines[line_idx]) > 10:
                old_line = lines[line_idx]
                line_idx += 1

            #            parts = map(string.strip, string.split(old_line))
            parts = old_line.split()
            if len(parts) < 4:
                self._runtime.logger.error(
                    f"Worker {self._comms.rank}. Incorrect number of values in the line with fsqr, fsqz and fsql"
                )
                return False
            fsqr = float(parts[1])
            fsqz = float(parts[2])
            fsql = float(parts[3])
            if (fsqr > 1.0e-10) or (fsqz > 1.0e-10) or (fsql > 1.0e-10):
                # Incorrect values for fsqr, fsqz o fsql
                self._runtime.logger.error(
                    f"Worker {self._comms.rank}. Incorrect values for fsqr, fsqz and fsql"
                )
                return False
        except Exception:
            self._runtime.logger.exception(
                "VMECProcess: error while processing threed1 file."
            )
            return False
        self._runtime.logger.info(
            f"WORKER({self._comms.rank}). Configuration threed1 OK"
        )
        return True

    """
    Run VMEC
    """

    def run_vmec(self):
        try:
            if not os.path.exists(f"input.tj{self._comms.rank}"):
                return False
            if not os.path.exists("/home/fraguas/bin/xvmec2000nc"):
                self._runtime.logger.error(
                    f"VMECProcess({self._comms.rank}). xvmec2000nc executable doesn't exist"
                )
                return False
            proc = subprocess.Popen(
                ["/home/fraguas/bin/xvmec2000nc", f"tj{self._comms.rank}"],
                stdout=subprocess.PIPE,
            )
            output = proc.stdout.read()
            self._runtime.logger.debug(output)
            if os.path.exists("core"):
                os.remove("core")
            if not os.path.exists(f"wout_tj{self._comms.rank}.txt"):
                self._runtime.logger.debug(
                    f"VMECProcess({self._comms.rank}): Invalid configuration"
                )
                return False
            last_line = tail(f"wout_tj{self._comms.rank}.txt")
            if last_line.find("mgrid") != -1:
                # Invalid configuration
                return False
            filenameMercier = f"mercier.tj{self._comms.rank}"
            if not os.path.exists(filenameMercier):
                return False
            self._runtime.logger.info(
                f"WORKER({self._comms.rank}). Configuration VMEC OK"
            )
            return True
        except Exception:
            self._runtime.logger.exception("VMECProcess: error when running VMEC.")
            return False

    """
    Checks if the xgrid code needs to be called
    """

    def run_x_grid(self):
        fullpath = f"{self._comms.rank}/{self._filename}"
        with open(fullpath) as fileinput:
            line = fileinput.readline()
            line = fileinput.readline()
            """
            Check if we have to run xgrid
            """
            runxgrid = True
            if line.find("mgrid.") == -1:
                # In this case, running xgrid is not necessary
                return True

        if runxgrid:
            if not os.path.exists("../external/mgrid.tj0"):
                self._runtime.logger.error("File Mgrid.tj0 doesn't exist")
                return False

            shutil.copy2("../external/mgrid.tj0", f"mgrid.tj{self._comms.rank}")
            if not os.path.exists(f"mgrid.tj{self._comms.rank}"):
                try:
                    with open(f"cmd_xgrid.tj{self._comms.rank}", "w") as fcmd_xgrid:
                        fcmd_xgrid.write(f"tj{self._comms.rank}\n")
                        fcmd_xgrid.write("y\n")
                        fcmd_xgrid.write("1.08\n")
                        fcmd_xgrid.write("1.92\n")
                        fcmd_xgrid.write("-0.42\n")
                        fcmd_xgrid.write("0.42\n")
                        fcmd_xgrid.write("64")
                    if not os.path.exists("../external/coils"):
                        self._runtime.logger.error("File coils doesn't exist")
                        return False
                    if not os.path.exists(f"coils.tj{self._comms.rank}"):
                        shutil.copy2("../external/coils", f"coils.tj{self._comms.rank}")
                    subprocess.call(["./xgrid", f"< cmd_xgrid.tj{self._comms.rank}"])
                    return True
                except Exception:
                    self._runtime.logger.exception("VMECProcess. Error executing xgrid")
        return False
