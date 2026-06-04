import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data.ParameterVMEC import ParameterVMEC
from data.Parameter import ParamType


def make_vmec_param(**overrides) -> ParameterVMEC:
    base = {
        "name": "test_param",
        "index": 0,
        "ptype": ParamType.FLOAT,
        "value": 3.14,
        "gap": 0.1,
        "min_value": 0.0,
        "max_value": 10.0,
        "x_index": 1,
        "y_index": 2,
        "fixed": False,
        "display": True,
    }
    base.update(overrides)
    return ParameterVMEC(**base)


class TestParameterVMECInitialization:
    def test_vmec_inherits_parameter(self):
        p = make_vmec_param()

        assert isinstance(p, ParameterVMEC)
        assert p.get_name() == "test_param"
        assert p.get_type() == ParamType.FLOAT
        assert pytest.approx(p.get_value()) == 3.14
        assert p.get_x_index() == 1
        assert p.get_y_index() == 2
        assert p.get_display() is True
        assert p.get_fixed() is False

    def test_init_requires_all_arguments(self):
        with pytest.raises(TypeError):
            ParameterVMEC(name="test_param", index=0, ptype=ParamType.FLOAT)


class TestDisplayAndFixedFlags:
    def test_display_and_fixed_flags(self):
        p = make_vmec_param(fixed=False, display=True)

        assert p.get_display() is True
        assert p.get_fixed() is False

        p.fixed = True

        assert p.get_fixed() is True

    def test_to_be_modified_logic(self):
        p = make_vmec_param(fixed=False, display=True)

        assert p.to_be_modified() is True

        p.fixed = True
        assert p.to_be_modified() is False

        p.display = False
        assert p.to_be_modified() is False


class TestMatrixIndices:
    def test_xy_index_set_get(self):
        p = make_vmec_param(x_index=10, y_index=20)

        assert p.get_x_index() == 10
        assert p.get_y_index() == 20


class TestInheritedParameterMethods:
    def test_name_type_value_accessors(self):
        p = make_vmec_param()

        p.set_name("alpha")
        p.set_type(ParamType.INT)
        p.set_value("5")

        assert p.get_name() == "alpha"
        assert p.get_type() == ParamType.INT
        assert p.get_value() == 5

    def test_value_conversion_for_bool(self):
        p = make_vmec_param(ptype=ParamType.BOOL, value=False)

        p.set_value("yes")
        assert p.get_value() is True

    def test_bounds_and_gap_are_preserved(self):
        p = make_vmec_param(min_value=-1.0, max_value=1.0, gap=0.5)

        assert p.get_min_value() == -1.0
        assert p.get_max_value() == 1.0
        assert p.get_gap() == 0.5
