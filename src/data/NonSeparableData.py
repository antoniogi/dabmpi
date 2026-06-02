#!/usr/bin/env python
# vim: set fileencoding=utf-8 :

import os
import sys
from array import array
from xml.dom import minidom
from .Parameter import Parameter


class NonSeparableData (object):
    """
    This class stores all the data required by VMEC.
    It also provides methods to read the input xml file that, for each
    parameter, specifies the min/max/default values, the gap, the index,...
    It can also create an XML output file with the data it contains
    """
    def __init__(self, runtime):
        self._numParams = 0
        self._maxRange = 0
        self._fInput = None
        self._params = []
        self._logger = runtime.logger
        return

    def __del__(self):
        try:
            del self._params[:]
        except:
            pass

    #returns the number of parameters that can be actually modified
    def getNumParams(self):
        return self._numParams

    """
    Returns a list of doubles with the values of the modificable parameters
    """
    def getValsOfParameters(self):
        buff = array('f', [0]) * self._numParams
        for i in range(self._numParams):
            buff[i] = float(self._params[i].get_value())
        return buff

    """
    Receives as parameter (buff) a list of values corresponding to
    the values that the parameters that can be modified must take.
    Goes through all of the parameters and changes the values of the
    modificable parameters to the value specified in this list
    """

    def setValsOfParameters(self, buff):
        self._logger.debug("NonSeparableData. Setting parameters (number: "
                         + str(len(buff)) + ")")
        for i in range(len(buff)):
            self._params[i].set_value(buff[i])

    def setParameters(self, parameters):
        for param in parameters:
            self.assign_parameter(param)
    """
    Return a list with all the parameters (list of Parameter objects)
    """
    def getParameters(self):
        return self._params

    """
    Assign a parameter with a new value to an older version of the
    same parameter
    """
    def assign_parameter(self, parameter):
        index = parameter.get_index()
        if index >= len(self._params):
            self._params.append(parameter)

    def getMaxRange(self):
        return self._maxRange

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
            for node in pNode.childNodes:
                if node.nodeType == node.ELEMENT_NODE:
                    c = Parameter()
                    for node_param in node.childNodes:
                        if node_param.nodeType == node_param.ELEMENT_NODE:
                            if node_param.localName == "type":
                                c.set_type(node_param.firstChild.data)
                            if node_param.localName == "value":
                                c.set_value(node_param.firstChild.data)
                            if node_param.localName == "min_value":
                                c.set_min_value(node_param.firstChild.data)
                            if node_param.localName == "max_value":
                                c.set_max_value(node_param.firstChild.data)
                            if node_param.localName == "index":
                                c.set_index(node_param.firstChild.data)
                            if node_param.localName == "name":
                                c.set_name(node_param.firstChild.data)
                            if node_param.localName == "gap":
                                c.set_gap(node_param.firstChild.data)
                    try:
                        self.assign_parameter(c)
                        self._numParams += 1
                        values = 1 + int(round((c.get_max_value() -
                                c.get_min_value()) / c.get_gap()))
                        self._maxRange = max(values, self._maxRange)
                    except Exception:
                        self._logger.exception("Problem calculating max range for parameter with index " + str(c.get_index()) + " and name " + str(c.get_name()))
                        raise
            self._logger.debug("Number of parameters " +
                           str(self._numParams) + "(" +
                           str(len(self._params)) + ")")
        except Exception:
            self._logger.exception("NonSeparableData. Exception while initializing from XML file")
            sys.exit(111)
        return
