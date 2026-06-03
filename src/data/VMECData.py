#!/usr/bin/env python


import os
import sys
from array import array
from xml.dom import minidom

from .Parameter import ParamType
from .ParameterVMEC import ParameterVMEC


class VMECData:
    """
    This class stores all the data required by VMEC.
    It also provides methods to read the input xml file that, for each
    parameter, specifies the min/max/default values, the gap, the index,...
    It can also create an XML output file with the data it contains
    """

    # We define the strict order of parameters here to eliminate boilerplate in getters/setters.
    _CONFIG_PARAMS = [
        "mgrid_file",
        "lfreeb",
        "loldout",
        "lwouttxt",
        "ldiagno",
        "loptim",
    ]

    _NUMERIC_PARAMS = [
        "delt",
        "tcon0",
        "nfp",
        "ncurr",
        "mpol",
        "ntor",
        "nzeta",
        "ns",
        "niter",
        "nstep",
        "nvacskip",
        "gamma",
        "ftol",
        "bloat",
        "phiedge",
        "extcur",
        "curtor",
        "spres_ped",
        "pres_scale",
        "am",
        "ai",
        "ac",
        "raxis",
        "zaxis",
        "rbc",
        "zbc",
        "epsfcn",
        "niter_opt",
        "lreset_opt",
        "lprof_opt",
        "lbmn",
        "lfix_ntor",
        "lsurf_mask",
        "target_aspectratio",
        "target_beta",
        "target_maxcurrent",
        "target_rmax",
        "target_rmin",
        "target_iota",
        "target_well",
        "sigma_aspect",
        "sigma_curv",
        "sigma_beta",
        "sigma_kink",
        "sigma_maxcurrent",
        "sigma_rmax",
        "sigma_rmin",
        "sigma_iota",
        "sigma_vp",
        "sigma_bmin",
        "sigma_bmax",
        "sigma_ripple",
        "sigma_jstar0",
        "sigma_jstar1",
        "sigma_jstar2",
        "sigma_jstar3",
        "sigma_balloon",
        "sigma_pgrad",
        "sigma_pedge",
        "lballon_test",
        "bal_zeta0",
        "bal_theta0",
        "bal_xmax",
        "bal_np0",
        "bal_kth",
        "bal_x0",
        "nrh",
        "mbuse",
        "nbuse",
        "zeff1",
        "damp",
        "isymm0",
        "ate",
        "ati",
    ]

    def __init__(self, runtime, comms):
        self._runtime = runtime
        self._comms = comms
        self._numParams = 0
        self._maxRange = 0
        self._show_indata = True
        self._show_optimum = True
        self._show_bootin = True
        self._fInput = None

        # Keeping explicit definitions prevents breaking any code
        # that relies on instance attribute access, and keeps IDE auto-complete happy.
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

    def getNumParams(self):
        """Returns the number of parameters that can be actually modified"""
        return self._numParams

    def getMaxRange(self):
        """
        Returns the maximum range(maximum number of values) that a parameter
        can take. This is the global maximum, meaning that most of the
        parameters will take less values than this.
        If param.max_value = 3, and param.min_value=1, and param.gap=1, the
        range for param is 3 (it can take values 1,2,3)
        """
        return self._maxRange

    def _iter_params(self, include_config=False):
        """
        Helper generator that dynamically yields parameter objects in the correct order.
        Handles both individual parameters and lists of parameters.
        """
        names = (
            self._CONFIG_PARAMS + self._NUMERIC_PARAMS
            if include_config
            else self._NUMERIC_PARAMS
        )

        for name in names:
            val = getattr(self, name, None)
            if val is None:
                continue

            if isinstance(val, list):
                for item in val:
                    yield item
            else:
                yield val

    def getValsOfParameters(self):
        """Returns a list of doubles with the values of the modifiable parameters"""
        buff = array("f", [0]) * self._numParams
        idx = 0

        for param in self._iter_params(include_config=False):
            if param.to_be_modified():
                buff[idx] = float(param.get_value())
                idx += 1

        return buff

    def setValsOfParameters(self, buff):
        """
        Receives as parameter (buff) a list of values corresponding to the values
        that the parameters that can be modified must take.
        """
        self._runtime.logger.debug(
            "VMECData. Setting parameters (number: " + str(len(buff)) + ")"
        )
        idx = 0

        for param in self._iter_params(include_config=False):
            if param.to_be_modified():
                param.set_value(buff[idx])
                idx += 1

    def getParameters(self):
        """Return a list with all the parameters (list of Parameter objects)"""
        parameters = []

        for param in self._iter_params(include_config=True):
            if param.to_be_modified():
                parameters.append(param)

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
            self._runtime.logger.warning(f"Unassigned element with index: {index}")
        return -1

    """
    Method that reads the xml input file. Puts into memory all the data
    contained in that file (min-max values, initial value, gap,...)
    Argument:
        - filepath: path to the XML input file
    """

    def initialize(self, filepath):
        try:
            if not os.path.exists(filepath):
                filepath = "../" + filepath
            xmldoc = minidom.parse(filepath)
            pNode = xmldoc.childNodes[0]
            for namelists in pNode.childNodes:
                if namelists.nodeType == namelists.ELEMENT_NODE:
                    if namelists.attributes["display"].value == "False":
                        if namelists.localName == "indata":
                            self._show_indata = False
                        if namelists.localName == "optimum":
                            self._show_optimum = False
                        if namelists.localName == "bootin":
                            self._show_bootin = False
                    for node in namelists.childNodes:
                        if node.nodeType == node.ELEMENT_NODE:
                            pname = None
                            display = None
                            index = None
                            fixed = None
                            ptype = None
                            value = None
                            min_value = None
                            max_value = None
                            x_index = None
                            y_index = None
                            gap = None

                            for node_param in node.childNodes:
                                if node_param.nodeType == node_param.ELEMENT_NODE:
                                    name = node_param.localName
                                    # helper to safely read text
                                    text = None
                                    if node_param.firstChild is not None:
                                        text = node_param.firstChild.data
                                    
                                    if text==None:
                                        continue

                                    if name == "index":
                                        index = int(text)

                                    if name == "display":
                                        display = text.strip().lower() in ("true", "t", "yes", "1")

                                    if name == "fixed":
                                        fixed = text.strip().lower() in ("true", "t", "yes", "1")

                                    if name == "type":
                                        t = text.strip().lower()
                                        mapping = {
                                            "float": ParamType.FLOAT,
                                            "double": ParamType.FLOAT,
                                            "int": ParamType.INT,
                                            "bool": ParamType.BOOL,
                                            "string": ParamType.STRING,
                                        }
                                        ptype = mapping.get(t, ParamType.STRING)

                                    if name == "value":
                                        value = text
                                        try:
                                            if node_param.hasAttribute("x"):
                                                x_index = node_param.getAttribute("x")
                                                x_index = int(x_index)
                                            if node_param.hasAttribute("y"):
                                                y_index = node_param.getAttribute("y")
                                                y_index = int(y_index)
                                        except Exception:
                                            pass

                                    if name == "min_value":
                                        min_value = text
                                        #c.set_min_value(text)

                                    if name == "max_value":
                                        max_value = text
                                        #c.set_max_value(text)

                                    #if name == "index":
                                        #index = text
                                        # c.set_index(text)3

                                    if name == "name":
                                        pname = text.strip()
                                        #c.set_name(text)

                                    if name == "gap":
                                        gap = text
                                        #c.set_gap(text)
                            try:
                                c = ParameterVMEC(
                                    name=pname,
                                    index=index,
                                    ptype=ptype,
                                    value=value,
                                    gap=gap,
                                    min_value=min_value,
                                    max_value=max_value,
                                    x_index=x_index,
                                    y_index=y_index,
                                    fixed=fixed,
                                    display=display
                                )
                                self.assign_parameter(c)
                                if c.to_be_modified():
                                    self._numParams += 1
                                    values = 1 + int(
                                        round(
                                            (c.get_max_value() - c.get_min_value())
                                            / c.get_gap()
                                        )
                                    )
                                    self._maxRange = max(values, self._maxRange)
                            except Exception:
                                self._runtime.logger.exception(
                                    f"VMECData. Exception assigning parameter with index {index} and name {pname}"
                                )
                                raise
        except Exception:
            self._runtime.logger.exception(
                "VMECData. Exception while initializing from XML file"
            )
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
            " ".join(values[i : i + per_line]) for i in range(0, len(values), per_line)
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
            f"{name}={fmt.format(param.get_value())}" for name, param, fmt in params
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
            self._runtime.logger.exception("Error writing INDATA section")
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
            self._runtime.logger.exception("Error writing OPTIMUM section")
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
            self._runtime.logger.exception("Error writing BOOTIN section")
            raise

    """
    Main method for creating the input file
    """

    def create_input_file(self, filename) -> bool:
        try:
            self._runtime.logger.debug(
                f"Worker {self._comms.rank} creating file {filename}"
            )
            with open(filename, "w", encoding="utf-8") as f_input:
                writers = [
                    (self._show_indata, self.__write_indata),
                    (self._show_optimum, self.__write_optimum),
                    (self._show_bootin, self.__write_bootin),
                ]
                for enabled, writer in writers:
                    if enabled:
                        writer(f_input)
            return True
        except Exception:
            self._runtime.logger.exception(
                f"Error creating input file (worker {self._comms.rank}): {filename}"
            )
            return False
