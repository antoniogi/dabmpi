import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from data.Parameter import Parameter, ParamType


def test_set_type_from_string_variants():
    p = Parameter()

    p.set_type("float")
    assert p.get_type() == ParamType.FLOAT

    p.set_type("double")
    assert p.get_type() == ParamType.FLOAT

    p.set_type("int")
    assert p.get_type() == ParamType.INT

    p.set_type("bool")
    assert p.get_type() == ParamType.BOOL

    p.set_type("string")
    assert p.get_type() == ParamType.STRING


def test_set_type_invalid_string_raises():
    p = Parameter()

    with pytest.raises(TypeError):
        p.set_type("invalid-type")


def test_bool_parse_invalid_value_raises():
    p = Parameter(type=ParamType.BOOL)

    with pytest.raises(ValueError, match="Cannot parse boolean value"):
        p.set_value("notabool")


def test_property_setters_and_getters():
    p = Parameter()

    p.type = "int"
    p.name = "alpha"
    p.index = 42
    p.set_value("7.8")

    assert p.get_type() == ParamType.INT
    assert p.get_name() == "alpha"
    assert p.get_index() == 42
    assert p.get_value() == 8


def test_set_min_max_values_for_bool():
    p = Parameter(type=ParamType.BOOL)

    p.set_min_value("true")
    p.set_max_value("false")

    assert p.get_min_value() is True
    assert p.get_max_value() is False


def test_repr_includes_name_and_type():
    p = Parameter(name="beta", index=3, type=ParamType.FLOAT, value=1.23)
    rep = repr(p)

    assert "beta" in rep
    assert "FLOAT" in rep
