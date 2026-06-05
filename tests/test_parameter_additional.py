import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from data.Parameter import Parameter, ParamType


def make_param(
    *,
    ptype: ParamType = ParamType.STRING,
    value: object | None = None,
    name: str = "x",
    index: int = 0,
    gap: float = 0.0,
    min_value: object | None = None,
    max_value: object | None = None,
) -> Parameter:
    if ptype == ParamType.INT:
        default_min = -100
        default_max = 100
        default_value = 0
    elif ptype == ParamType.FLOAT:
        default_min = -1.0e6
        default_max = 1.0e6
        default_value = 0.0
    elif ptype == ParamType.BOOL:
        default_min = False
        default_max = True
        default_value = False
    else:
        default_min = ""
        default_max = ""
        default_value = ""

    return Parameter(
        name=name,
        index=index,
        ptype=ptype,
        value=default_value if value is None else value,
        gap=gap,
        min_value=default_min if min_value is None else min_value,
        max_value=default_max if max_value is None else max_value,
    )


def test_set_type_from_string_variants():
    p = make_param()

    p.type = "float"
    assert p.type == ParamType.FLOAT

    p.type = "double"
    assert p.type == ParamType.FLOAT

    p.type = "int"
    assert p.type == ParamType.INT

    p.type = "bool"
    assert p.type == ParamType.BOOL

    p.type = "string"
    assert p.type == ParamType.STRING


def test_set_type_invalid_string_raises():
    p = make_param()

    with pytest.raises(TypeError):
        p.type = "invalid-type"


def test_bool_parse_invalid_value_raises():
    p = make_param(ptype=ParamType.BOOL, value=False)

    with pytest.raises(ValueError, match="Cannot parse boolean value"):
        p.value = "notabool"


def test_property_setters_and_getters():
    p = make_param()

    p.type = "int"
    p.name = "alpha"
    p.index = 42
    p.value = "7.8"

    assert p.type == ParamType.INT
    assert p.name == "alpha"
    assert p.index == 42
    assert p.value == 8


def test_set_min_max_values_for_bool():
    p = make_param(
        ptype=ParamType.BOOL, value=False, min_value="true", max_value="false"
    )

    assert p.min_value is True
    assert p.max_value is False


def test_repr_includes_name_and_type():
    p = make_param(name="beta", index=3, ptype=ParamType.FLOAT, value=1.23)
    rep = repr(p)

    assert "beta" in rep
    assert "FLOAT" in rep
